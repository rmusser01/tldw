import chromadb
from chromadb.config import Settings
from typing import List, Dict, Any
import logging
import numpy as np
from App_Function_Libraries.Utils.Utils import load_and_log_configs, get_database_path, ensure_directory_exists, logger
from App_Function_Libraries.Chunk_Lib import chunk_for_embedding, chunk_options
from App_Function_Libraries.DB.DB_Manager import get_unprocessed_media, mark_media_as_processed
from App_Function_Libraries.DB.SQLite_DB import process_chunks
from App_Function_Libraries.RAG.Embeddings_Create import create_embedding, create_embeddings_batch
from App_Function_Libraries.Summarization.Summarization_General_Lib import summarize

import threading
from itertools import islice

# Load configurations - ensure this is only called once, ideally at the application's entry point.
config = load_and_log_configs()
chroma_db_path = config['db_config']['chroma_db_path']
embedding_model = config['embedding_config']['embedding_model']
embedding_provider = config['embedding_config']['embedding_provider']
embedding_api_key = config['embedding_config']['embedding_api_key']
embedding_api_url = config['embedding_config']['embedding_api_url']

# Initialize ChromaDB client
chroma_client = chromadb.PersistentClient(path=chroma_db_path, settings=Settings(anonymized_telemetry=False))
_chroma_lock = threading.Lock()  # Create a lock - STILL GOOD TO HAVE for other operations.

def store_in_chroma(collection_name: str, texts: List[str], embeddings: Any, ids: List[str],
                    metadatas: List[Dict[str, Any]]):
    """
    Stores text, embeddings, and metadata in ChromaDB using upsert.
    """
    # Input validation
    if not all([texts, embeddings, ids, metadatas]):
        raise ValueError("All input lists (texts, embeddings, ids, metadatas) must be non-empty.")

    if not (len(texts) == len(embeddings) == len(ids) == len(metadatas)):
        raise ValueError("All input lists must have the same length.")

    # Convert embeddings to list if it's a numpy array
    if isinstance(embeddings, np.ndarray):
        embeddings = embeddings.tolist()
    elif not isinstance(embeddings, list):
        raise TypeError("Embeddings must be either a list or a numpy array")

    if not embeddings:  # Check for empty embeddings list after conversion
      raise ValueError("No embeddings provided")
    embedding_dim = len(embeddings[0])


    with _chroma_lock:  # Good practice to keep the lock for all Chroma operations.
        logging.info(f"Storing embeddings in ChromaDB - Collection: {collection_name}")
        logging.info(f"Number of embeddings: {len(embeddings)}, Dimension: {embedding_dim}")
        try:
            collection = chroma_client.get_or_create_collection(name=collection_name) #still needed, but in try

            # Clean metadata
            cleaned_metadatas = [clean_metadata(metadata) for metadata in metadatas]

            # Perform the upsert operation
            collection.upsert(
                documents=texts,
                embeddings=embeddings,
                ids=ids,
                metadatas=cleaned_metadatas
            )
            logging.info(f"Successfully upserted {len(embeddings)} embeddings")

            # Verification (Optional, but good for debugging)
            results = collection.get(ids=ids, include=["documents", "embeddings", "metadatas"])
            for i, doc_id in enumerate(ids):
                if results['embeddings'][i] is None:
                    raise ValueError(f"Failed to store (or retrieve after upsert) embedding for {doc_id}")
                else:
                    logging.debug(f"Embedding stored successfully for {doc_id}")
                    logging.debug(f"Stored document preview: {results['documents'][i][:100]}...")
                    logging.debug(f"Stored metadata: {results['metadatas'][i]}")

            logging.info("Successfully stored and verified all embeddings in ChromaDB")

        except Exception as e:
            logging.error(f"Error in store_in_chroma: {str(e)}") #keep
            raise
    return collection

def query_chroma(collection_name, query_embedding, n_results=5, where_clause=None):
    """
    Queries ChromaDB for the most similar embeddings.

    :param collection_name: Name of the collection.
    :param query_embedding: The embedding to query for.
    :param n_results: Number of results to return.
    :param where_clause: Optional where clause for filtering results.
    :return: Query results.
    """
    with _chroma_lock:
        collection = chroma_client.get_collection(name=collection_name)
        return collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=where_clause
        )

def delete_from_chroma(collection_name, ids):
    """
    Deletes entries from a ChromaDB collection by their IDs.

    :param collection_name: Name of the collection.
    :param ids: List of IDs to delete.
    """
    with _chroma_lock:
        collection = chroma_client.get_collection(name=collection_name)
        collection.delete(ids=ids)

def get_chroma_collection(collection_name):
    """Retrieves a specified ChromaDB collection.

    Args:
        collection_name (str): The name of the collection to retrieve.

    Returns:
        chromadb.Collection: The requested ChromaDB collection.
    """
    # Directly return the result of get_collection
    with _chroma_lock:
        return chroma_client.get_collection(collection_name)

def count_items_in_collection(collection_name):
    """
    Counts the number of items in a specified ChromaDB collection.

    Args:
        collection_name (str): The name of the collection.

    Returns:
        int: The number of items in the collection.
    """
    with _chroma_lock:
        collection = chroma_client.get_collection(name=collection_name)
        return collection.count()

def clean_metadata(metadata: Dict[str, Any]) -> Dict[str, Any]:
    """Clean metadata by removing None values and converting to appropriate types"""
    cleaned = {}
    for key, value in metadata.items():
        if value is not None:  # Skip None values
            if isinstance(value, (str, int, float, bool)):
                cleaned[key] = value
            elif isinstance(value, (np.int32, np.int64)):
                cleaned[key] = int(value)
            elif isinstance(value, (np.float32, np.float64)):
                cleaned[key] = float(value)
            else:
                cleaned[key] = str(value)  # Convert other types to string
    return cleaned


def vector_search(collection_name: str, query: str, k: int = 10) -> List[Dict[str, Any]]:
    try:
        collection = chroma_client.get_collection(name=collection_name)

        # Fetch a sample of embeddings to check metadata
        sample_results = collection.get(limit=10, include=["metadatas"])
        if not sample_results.get('metadatas') or not any(sample_results['metadatas']):
            logging.warning(f"No metadata found in the collection '{collection_name}'. Skipping this collection.")
            return []

        # Check if all embeddings use the same model and provider
        embedding_models = [
            metadata.get('embedding_model') for metadata in sample_results['metadatas']
            if metadata and metadata.get('embedding_model')
        ]
        embedding_providers = [
            metadata.get('embedding_provider') for metadata in sample_results['metadatas']
            if metadata and metadata.get('embedding_provider')
        ]

        if not embedding_models or not embedding_providers:
            raise ValueError("Embedding model or provider information not found in metadata")

        embedding_model = max(set(embedding_models), key=embedding_models.count)
        embedding_provider = max(set(embedding_providers), key=embedding_providers.count)

        logging.info(f"Using embedding model: {embedding_model} from provider: {embedding_provider}")

        # Generate query embedding using the existing create_embedding function
        query_embedding = create_embedding(query, embedding_provider, embedding_model, embedding_api_url)

        # Ensure query_embedding is a list
        if isinstance(query_embedding, np.ndarray):
            query_embedding = query_embedding.tolist()

        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=k,
            include=["documents", "metadatas"]
        )

        if not results['documents'][0]:
            logging.warning(f"No results found for the query in collection '{collection_name}'.")
            return []

        return [{"content": doc, "metadata": meta} for doc, meta in zip(results['documents'][0], results['metadatas'][0])]
    except Exception as e:
        logging.error(f"Error in vector_search for collection '{collection_name}': {str(e)}", exc_info=True)
        return []

def reset_chroma_collection(collection_name: str):
    with _chroma_lock:
        try:
            chroma_client.delete_collection(collection_name)
            #chroma_client.create_collection(collection_name) #not necessary
            logging.info(f"Reset ChromaDB collection: {collection_name}")
        except Exception as e:
            logging.error(f"Error resetting ChromaDB collection: {str(e)}")

def batched(iterable, n):
    "Batch data into lists of length n. The last batch may be shorter."
    it = iter(iterable)
    while True:
        batch = list(islice(it, n))
        if not batch:
            return
        yield batch

def situate_context(api_name, doc_content: str, chunk_content: str) -> str:
    doc_content_prompt = f"""
    <document>
    {doc_content}
    </document>
    """

    chunk_context_prompt = f"""
    \n\n\n\n\n
    Here is the chunk we want to situate within the whole document
    <chunk>
    {chunk_content}
    </chunk>

    Please give a short succinct context to situate this chunk within the overall document for the purposes of improving search retrieval of the chunk.
    Answer only with the succinct context and nothing else.
    """

    response = summarize(chunk_context_prompt, doc_content_prompt, api_name, api_key=None, temp=0, system_message=None)
    return response

def process_and_store_content(database, content: str, collection_name: str, media_id: int, file_name: str,
                              create_embeddings: bool = True, create_contextualized: bool = True, api_name: str = "gpt-3.5-turbo",
                              chunk_options = None, embedding_provider: str = None,
                              embedding_model: str = None, embedding_api_url: str = None):
    try:
        logger.info(f"Processing content for media_id {media_id} in collection {collection_name}")

        chunks = chunk_for_embedding(content, file_name, chunk_options)

        # Process chunks synchronously
        process_chunks(database, chunks, media_id)

        if create_embeddings:
            texts = []
            contextualized_chunks = []
            for chunk in chunks:
                chunk_text = chunk['text']
                if create_contextualized:
                    context = situate_context(api_name, content, chunk_text)
                    contextualized_text = f"{chunk_text}\n\nContextual Summary: {context}"
                    contextualized_chunks.append(contextualized_text)
                else:
                    contextualized_chunks.append(chunk_text)
                texts.append(chunk_text)  # Store original text for database

            embeddings = create_embeddings_batch(contextualized_chunks, embedding_provider, embedding_model, embedding_api_url)
            ids = [f"{media_id}_chunk_{i}" for i in range(1, len(chunks) + 1)]
            metadatas = [{
                "media_id": str(media_id),
                "chunk_index": i,
                "total_chunks": len(chunks),
                "start_index": int(chunk['metadata']['start_index']),
                "end_index": int(chunk['metadata']['end_index']),
                "file_name": str(chunk['metadata']['file_name']),
                "relative_position": float(chunk['metadata']['relative_position']),
                "contextualized": create_contextualized,
                "original_text": chunk['text'],
                "contextual_summary": contextualized_chunks[i-1].split("\n\nContextual Summary: ")[-1] if create_contextualized else ""
            } for i, chunk in enumerate(chunks, 1)]

            store_in_chroma(collection_name, contextualized_chunks, embeddings, ids, metadatas)

            # Mark the media as processed
            mark_media_as_processed(database, media_id)

        # Update full-text search index
        database.execute_query(
            "INSERT OR REPLACE INTO media_fts (rowid, title, content) SELECT id, title, content FROM Media WHERE id = ?",
            (media_id,)
        )

        logger.info(f"Finished processing and storing content for media_id {media_id}")

    except Exception as e:
        logger.error(f"Error in process_and_store_content for media_id {media_id}: {str(e)}")
        raise

def check_embedding_status(selected_item, item_mapping):
    if not selected_item:
        return "Please select an item", ""

    try:
        item_id = item_mapping.get(selected_item)
        if item_id is None:
            return f"Invalid item selected: {selected_item}", ""

        item_title = selected_item.rsplit(' (', 1)[0]
        collection = chroma_client.get_or_create_collection(name="all_content_embeddings")

        result = collection.get(ids=[f"doc_{item_id}"], include=["embeddings", "metadatas"])
        logging.info(f"ChromaDB result for item '{item_title}' (ID: {item_id}): {result}")

        if not result['ids']:
            return f"No embedding found for item '{item_title}' (ID: {item_id})", ""

        if not result['embeddings'] or not result['embeddings'][0]:
            return f"Embedding data missing for item '{item_title}' (ID: {item_id})", ""

        embedding = result['embeddings'][0]
        metadata = result['metadatas'][0] if result['metadatas'] else {}
        embedding_preview = str(embedding[:50])
        status = f"Embedding exists for item '{item_title}' (ID: {item_id})"
        return status, f"First 50 elements of embedding:\n{embedding_preview}\n\nMetadata: {metadata}"

    except Exception as e:
        logging.error(f"Error in check_embedding_status: {str(e)}")
        return f"Error processing item: {selected_item}. Details: {str(e)}", ""

# Function to process content, create chunks, embeddings, and store in ChromaDB and SQLite
# def process_and_store_content(content: str, collection_name: str, media_id: int):
#     # Process the content into chunks
#     chunks = improved_chunking_process(content, chunk_options)
#     texts = [chunk['text'] for chunk in chunks]
#
#     # Generate embeddings for each chunk
#     embeddings = [create_embedding(text) for text in texts]
#
#     # Create unique IDs for each chunk using the media_id and chunk index
#     ids = [f"{media_id}_chunk_{i}" for i in range(len(texts))]
#
#     # Store the texts, embeddings, and IDs in ChromaDB
#     store_in_chroma(collection_name, texts, embeddings, ids)
#
#     # Store the chunk metadata in SQLite
#     for i, chunk in enumerate(chunks):
#         add_media_chunk(media_id, chunk['text'], chunk['start'], chunk['end'], ids[i])
#
#     # Update the FTS table
#     update_fts_for_media(media_id)


#
# End of Functions for ChromaDB
#######################################################################################################################


# FIXME - Suggestions from ChatGPT:
# 2. Detailed Mapping and Assessment
# a. preprocess_all_content
#
# Test: test_preprocess_all_content
#
# Coverage:
#
#     Mocks the get_unprocessed_media function to return a predefined unprocessed media list.
#     Mocks process_and_store_content and mark_media_as_processed to verify their invocation with correct arguments.
#     Asserts that process_and_store_content and mark_media_as_processed are called exactly once with expected parameters.
#
# Assessment:
#
#     Strengths: Ensures that preprocess_all_content correctly retrieves unprocessed media, processes each item, and marks it as processed.
#     Suggestions:
#         Multiple Media Items: Test with multiple media items to verify loop handling.
#         Exception Handling: Simulate exceptions within process_and_store_content to ensure proper logging and continuation or halting as intended.
#
# b. process_and_store_content
#
# Test: test_process_and_store_content
#
# Coverage:
#
#     Mocks dependencies: chunk_for_embedding, process_chunks, situate_context, create_embeddings_batch, and chroma_client.
#     Simulates the scenario where the specified ChromaDB collection does not exist initially and needs to be created.
#     Verifies that chunks are processed, embeddings are created, stored in ChromaDB, and database queries are executed correctly.
#
# Assessment:
#
#     Strengths: Thoroughly checks the workflow of processing content, including chunking, embedding creation, and storage.
#     Suggestions:
#         Existing Collection: Add a test case where the collection already exists to ensure that get_collection is used without attempting to create a new one.
#         Embedding Creation Disabled: Test with create_embeddings=False to verify alternative code paths.
#         Error Scenarios: Simulate failures in embedding creation or storage to ensure exceptions are handled gracefully.
#
# c. check_embedding_status
#
# Test: test_check_embedding_status
#
# Coverage:
#
#     Mocks the ChromaDB client to return predefined embeddings and metadata.
#     Verifies that the function correctly identifies the existence of embeddings and retrieves relevant metadata.
#
# Assessment:
#
#     Strengths: Confirms that the function accurately detects existing embeddings and handles metadata appropriately.
#     Suggestions:
#         No Embeddings Found: Test the scenario where no embeddings exist for the selected item.
#         Missing Metadata: Simulate missing or incomplete metadata to ensure robust error handling.
#
# d. reset_chroma_collection
#
# Test: test_reset_chroma_collection
#
# Coverage:
#
#     Mocks the ChromaDB client’s delete_collection and create_collection methods.
#     Verifies that the specified collection is deleted and recreated.
#
# Assessment:
#
#     Strengths: Ensures that the reset operation performs both deletion and creation as intended.
#     Suggestions:
#         Non-Existent Collection: Test resetting a collection that does not exist to verify behavior.
#         Exception Handling: Simulate failures during deletion or creation to check error logging and propagation.
#
# e. store_in_chroma
#
# Test: test_store_in_chroma
#
# Coverage:
#
#     Mocks the ChromaDB client to return a mock collection.
#     Verifies that documents, embeddings, IDs, and metadata are upserted correctly into the collection.
#
# Assessment:
#
#     Strengths: Confirms that embeddings and associated data are stored accurately in ChromaDB.
#     Suggestions:
#         Empty Embeddings: Test storing with empty embeddings to ensure proper error handling.
#         Embedding Dimension Mismatch: Simulate a dimension mismatch to verify that the function handles it as expected.
#
# f. vector_search
#
# Test: test_vector_search
#
# Coverage:
#
#     Mocks the ChromaDB client’s get_collection, get, and query methods.
#     Mocks the create_embedding function to return a predefined embedding.
#     Verifies that the search retrieves the correct documents and metadata based on the query.
#
# Assessment:
#
#     Strengths: Ensures that the vector search mechanism correctly interacts with ChromaDB and returns expected results.
#     Suggestions:
#         No Results Found: Test queries that return no results to verify handling.
#         Multiple Results: Ensure that multiple documents are retrieved and correctly formatted.
#         Metadata Variations: Test with diverse metadata to confirm accurate retrieval.
#
# g. batched
#
# Test: test_batched
#
# Coverage:
#
#     Uses pytest.mark.parametrize to test multiple scenarios:
#         Regular batching.
#         Batch size larger than the iterable.
#         Empty iterable.
#
# Assessment:
#
#     Strengths: Comprehensive coverage of typical and edge batching scenarios.
#     Suggestions:
#         Non-Integer Batch Sizes: Test with invalid batch sizes (e.g., zero, negative numbers) to ensure proper handling or error raising.
#
# h. situate_context and schedule_embedding
#
# Tests: Not directly tested
#
# Coverage:
#
#     These functions are currently not directly tested in the test_chromadb.py suite.
#
# Assessment:
#
#     Suggestions:
#         situate_context:
#             Unit Test: Since it's a pure function that interacts with the summarize function, create a separate test to mock summarize and verify the context generation.
#             Edge Cases: Test with empty strings, very long texts, or special characters to ensure robustness.
#         schedule_embedding:
#             Integration Test: Since it orchestrates multiple operations (chunking, embedding creation, storage), consider writing an integration test that mocks all dependent functions and verifies the complete workflow.