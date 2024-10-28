# RAG_Library_2.py
# Description: This script contains the main RAG pipeline function and related functions for the RAG pipeline.
#
# Import necessary modules and functions
import configparser
import logging
import os
import time
from typing import Dict, Any, List, Optional

from App_Function_Libraries.DB.Character_Chat_DB import get_character_chats, perform_full_text_search_chat, \
    fetch_keywords_for_chats, search_character_chat, search_character_cards, fetch_character_ids_by_keywords
from App_Function_Libraries.DB.RAG_QA_Chat_DB import search_rag_chat, search_rag_notes
#
# Local Imports
from App_Function_Libraries.RAG.ChromaDB_Library import process_and_store_content, vector_search, chroma_client
from App_Function_Libraries.RAG.RAG_Persona_Chat import perform_vector_search_chat
from App_Function_Libraries.Summarization.Local_Summarization_Lib import summarize_with_custom_openai
from App_Function_Libraries.Web_Scraping.Article_Extractor_Lib import scrape_article
from App_Function_Libraries.DB.DB_Manager import fetch_keywords_for_media, search_media_db, get_notes_by_keywords, \
    search_conversations_by_keywords
from App_Function_Libraries.Utils.Utils import load_comprehensive_config
from App_Function_Libraries.Metrics.metrics_logger import log_counter, log_histogram
#
# 3rd-Party Imports
import openai
from flashrank import Ranker, RerankRequest
#
########################################################################################################################
#
# Functions:

# Initialize OpenAI client (adjust this based on your API key management)
openai.api_key = "your-openai-api-key"

# Get the directory of the current script
current_dir = os.path.dirname(os.path.abspath(__file__))
# Construct the path to the config file
config_path = os.path.join(current_dir, 'Config_Files', 'config.txt')
# Read the config file
config = configparser.ConfigParser()
# Read the configuration file
config.read('config.txt')

# RAG pipeline function for web scraping
# def rag_web_scraping_pipeline(url: str, query: str, api_choice=None) -> Dict[str, Any]:
#     try:
#         # Extract content
#         try:
#             article_data = scrape_article(url)
#             content = article_data['content']
#             title = article_data['title']
#         except Exception as e:
#             logging.error(f"Error scraping article: {str(e)}")
#             return {"error": "Failed to scrape article", "details": str(e)}
#
#         # Store the article in the database and get the media_id
#         try:
#             media_id = add_media_to_database(url, title, 'article', content)
#         except Exception as e:
#             logging.error(f"Error adding article to database: {str(e)}")
#             return {"error": "Failed to store article in database", "details": str(e)}
#
#         # Process and store content
#         collection_name = f"article_{media_id}"
#         try:
#             # Assuming you have a database object available, let's call it 'db'
#             db = get_database_connection()
#
#             process_and_store_content(
#                 database=db,
#                 content=content,
#                 collection_name=collection_name,
#                 media_id=media_id,
#                 file_name=title,
#                 create_embeddings=True,
#                 create_contextualized=True,
#                 api_name=api_choice
#             )
#         except Exception as e:
#             logging.error(f"Error processing and storing content: {str(e)}")
#             return {"error": "Failed to process and store content", "details": str(e)}
#
#         # Perform searches
#         try:
#             vector_results = vector_search(collection_name, query, k=5)
#             fts_results = search_db(query, ["content"], "", page=1, results_per_page=5)
#         except Exception as e:
#             logging.error(f"Error performing searches: {str(e)}")
#             return {"error": "Failed to perform searches", "details": str(e)}
#
#         # Combine results with error handling for missing 'content' key
#         all_results = []
#         for result in vector_results + fts_results:
#             if isinstance(result, dict) and 'content' in result:
#                 all_results.append(result['content'])
#             else:
#                 logging.warning(f"Unexpected result format: {result}")
#                 all_results.append(str(result))
#
#         context = "\n".join(all_results)
#
#         # Generate answer using the selected API
#         try:
#             answer = generate_answer(api_choice, context, query)
#         except Exception as e:
#             logging.error(f"Error generating answer: {str(e)}")
#             return {"error": "Failed to generate answer", "details": str(e)}
#
#         return {
#             "answer": answer,
#             "context": context
#         }
#
#     except Exception as e:
#         logging.error(f"Unexpected error in rag_pipeline: {str(e)}")
#         return {"error": "An unexpected error occurred", "details": str(e)}


# RAG Search with keyword filtering
# FIXME - Update each called function to support modifiable top-k results
def enhanced_rag_pipeline(query: str, api_choice: str, keywords: str = None, fts_top_k=10, apply_re_ranking=True, database_types: List[str] = "Media DB") -> Dict[str, Any]:
    """
    Perform full text search across specified database type.

    Args:
        query: Search query string
        api_choice: API to use for generating the response
        fts_top_k: Maximum number of results to return
        keywords: Optional list of media IDs to filter results
        database_types: Type of database to search ("Media DB", "RAG Chat", or "Character Chat")

    Returns:
        Dictionary containing search results with content
    """
    log_counter("enhanced_rag_pipeline_attempt", labels={"api_choice": api_choice})
    start_time = time.time()
    try:
        # Load embedding provider from config, or fallback to 'openai'
        embedding_provider = config.get('Embeddings', 'provider', fallback='openai')

        # Log the provider used
        logging.debug(f"Using embedding provider: {embedding_provider}")

        # Process keywords if provided
        keyword_list = [k.strip().lower() for k in keywords.split(',')] if keywords else []
        logging.debug(f"\n\nenhanced_rag_pipeline - Keywords: {keyword_list}")

        relevant_ids = {}

        # Fetch relevant IDs based on keywords if keywords are provided
        if keyword_list:
            try:
                for db_type in database_types:
                    if db_type == "Media DB":
                        relevant_media_ids = fetch_relevant_media_ids(keyword_list)
                        relevant_ids[db_type] = relevant_media_ids
                        logging.debug(f"enhanced_rag_pipeline - {db_type} relevant media IDs: {relevant_media_ids}")

                    elif db_type == "RAG Chat":
                        conversations, total_pages, total_count = search_conversations_by_keywords(
                            keywords=keyword_list)
                        relevant_conversation_ids = [conv['conversation_id'] for conv in conversations]
                        relevant_ids[db_type] = relevant_conversation_ids
                        logging.debug(
                            f"enhanced_rag_pipeline - {db_type} relevant conversation IDs: {relevant_conversation_ids}")

                    elif db_type == "RAG Notes":
                        notes, total_pages, total_count = get_notes_by_keywords(keyword_list)
                        relevant_note_ids = [note_id for note_id, _, _, _ in notes]  # Unpack note_id from the tuple
                        relevant_ids[db_type] = relevant_note_ids
                        logging.debug(f"enhanced_rag_pipeline - {db_type} relevant note IDs: {relevant_note_ids}")

                    elif db_type == "Character Chat":
                        relevant_chat_ids = fetch_keywords_for_chats(keyword_list)
                        relevant_ids[db_type] = relevant_chat_ids
                        logging.debug(f"enhanced_rag_pipeline - {db_type} relevant chat IDs: {relevant_chat_ids}")

                    elif db_type == "Character Cards":
                        # Assuming we have a function to fetch character IDs by keywords
                        relevant_character_ids = fetch_character_ids_by_keywords(keyword_list)
                        relevant_ids[db_type] = relevant_character_ids
                        logging.debug(
                            f"enhanced_rag_pipeline - {db_type} relevant character IDs: {relevant_character_ids}")

                    else:
                        logging.error(f"Unsupported database type: {db_type}")

            except Exception as e:
                logging.error(f"Error fetching relevant IDs: {str(e)}")
        else:
            relevant_ids = None

        # Extract relevant media IDs for each selected DB
        # Prepare a dict to hold relevant_media_ids per DB
        relevant_media_ids_dict = {}
        if relevant_ids:
            for db_type in database_types:
                relevant_media_ids = relevant_ids.get(db_type, None)
                if relevant_media_ids:
                    # Convert to List[str] if not None
                    relevant_media_ids_dict[db_type] = [str(media_id) for media_id in relevant_media_ids]
                else:
                    relevant_media_ids_dict[db_type] = None
        else:
            relevant_media_ids_dict = {db_type: None for db_type in database_types}

        # Perform vector search for all selected databases
        vector_results = []
        for db_type in database_types:
            try:
                db_relevant_ids = relevant_media_ids_dict.get(db_type)
                results = perform_vector_search(query, db_relevant_ids, top_k=fts_top_k)
                vector_results.extend(results)
                logging.debug(f"\nenhanced_rag_pipeline - Vector search results for {db_type}: {results}")
            except Exception as e:
                logging.error(f"Error performing vector search on {db_type}: {str(e)}")

        # Perform vector search
        # FIXME
        vector_results = perform_vector_search(query, relevant_media_ids)
        logging.debug(f"\n\nenhanced_rag_pipeline - Vector search results: {vector_results}")

        # Perform full-text search
        #v1
        #fts_results = perform_full_text_search(query, database_type, relevant_media_ids, fts_top_k)

        # v2
        # Perform full-text search across specified databases
        fts_results = []
        for db_type in database_types:
            try:
                db_relevant_ids = relevant_ids.get(db_type) if relevant_ids else None
                db_results = perform_full_text_search(query, db_type, db_relevant_ids, fts_top_k)
                fts_results.extend(db_results)
                logging.debug(f"enhanced_rag_pipeline - FTS results for {db_type}: {db_results}")
            except Exception as e:
                logging.error(f"Error performing full-text search on {db_type}: {str(e)}")

        logging.debug("\n\nenhanced_rag_pipeline - Full-text search results:")
        logging.debug(
            "\n\nenhanced_rag_pipeline - Full-text search results:\n" + "\n".join(
                [str(item) for item in fts_results]) + "\n"
        )

        # Combine results
        all_results = vector_results + fts_results

        if apply_re_ranking:
            logging.debug(f"\nenhanced_rag_pipeline - Applying Re-Ranking")
            # FIXME - add option to use re-ranking at call time
            # FIXME - specify model + add param to modify at call time
            # FIXME - add option to set a custom top X results
            # You can specify a model if necessary, e.g., model_name="ms-marco-MiniLM-L-12-v2"
            if all_results:
                ranker = Ranker()

                # Prepare passages for re-ranking
                passages = [{"id": i, "text": result['content']} for i, result in enumerate(all_results)]
                rerank_request = RerankRequest(query=query, passages=passages)

                # Rerank the results
                reranked_results = ranker.rerank(rerank_request)

                # Sort results based on the re-ranking score
                reranked_results = sorted(reranked_results, key=lambda x: x['score'], reverse=True)

                # Log reranked results
                logging.debug(f"\n\nenhanced_rag_pipeline - Reranked results: {reranked_results}")

                # Update all_results based on reranking
                all_results = [all_results[result['id']] for result in reranked_results]

        # Extract content from results (top fts_top_k by default)
        context = "\n".join([result['content'] for result in all_results[:fts_top_k]])
        logging.debug(f"Context length: {len(context)}")
        logging.debug(f"Context: {context[:200]}")

        # Generate answer using the selected API
        answer = generate_answer(api_choice, context, query)

        if not all_results:
            logging.info(f"No results found. Query: {query}, Keywords: {keywords}")
            return {
                "answer": "No relevant information based on your query and keywords were found in the database. Your query has been directly passed to the LLM, and here is its answer: \n\n" + answer,
                "context": "No relevant information based on your query and keywords were found in the database. The only context used was your query: \n\n" + query
            }
        # Metrics
        pipeline_duration = time.time() - start_time
        log_histogram("enhanced_rag_pipeline_duration", pipeline_duration, labels={"api_choice": api_choice})
        log_counter("enhanced_rag_pipeline_success", labels={"api_choice": api_choice})
        return {
            "answer": answer,
            "context": context
        }

    except Exception as e:
        # Metrics
        log_counter("enhanced_rag_pipeline_error", labels={"api_choice": api_choice, "error": str(e)})
        logging.error(f"Error in enhanced_rag_pipeline: {str(e)}")
        logging.error(f"Error in enhanced_rag_pipeline: {str(e)}")
        return {
            "answer": "An error occurred while processing your request.",
            "context": ""
        }



# Need to write a test for this function FIXME
def generate_answer(api_choice: str, context: str, query: str) -> str:
    # Metrics
    log_counter("generate_answer_attempt", labels={"api_choice": api_choice})
    start_time = time.time()
    logging.debug("Entering generate_answer function")
    config = load_comprehensive_config()
    logging.debug(f"Config sections: {config.sections()}")
    prompt = f"Context: {context}\n\nQuestion: {query}"
    try:
        if api_choice == "OpenAI":
            from App_Function_Libraries.Summarization.Summarization_General_Lib import summarize_with_openai
            answer_generation_duration = time.time() - start_time
            log_histogram("generate_answer_duration", answer_generation_duration, labels={"api_choice": api_choice})
            log_counter("generate_answer_success", labels={"api_choice": api_choice})
            return summarize_with_openai(config['API']['openai_api_key'], prompt, "")

        elif api_choice == "Anthropic":
            from App_Function_Libraries.Summarization.Summarization_General_Lib import summarize_with_anthropic
            answer_generation_duration = time.time() - start_time
            log_histogram("generate_answer_duration", answer_generation_duration, labels={"api_choice": api_choice})
            log_counter("generate_answer_success", labels={"api_choice": api_choice})
            return summarize_with_anthropic(config['API']['anthropic_api_key'], prompt, "")

        elif api_choice == "Cohere":
            from App_Function_Libraries.Summarization.Summarization_General_Lib import summarize_with_cohere
            answer_generation_duration = time.time() - start_time
            log_histogram("generate_answer_duration", answer_generation_duration, labels={"api_choice": api_choice})
            log_counter("generate_answer_success", labels={"api_choice": api_choice})
            return summarize_with_cohere(config['API']['cohere_api_key'], prompt, "")

        elif api_choice == "Groq":
            from App_Function_Libraries.Summarization.Summarization_General_Lib import summarize_with_groq
            answer_generation_duration = time.time() - start_time
            log_histogram("generate_answer_duration", answer_generation_duration, labels={"api_choice": api_choice})
            log_counter("generate_answer_success", labels={"api_choice": api_choice})
            return summarize_with_groq(config['API']['groq_api_key'], prompt, "")

        elif api_choice == "OpenRouter":
            from App_Function_Libraries.Summarization.Summarization_General_Lib import summarize_with_openrouter
            answer_generation_duration = time.time() - start_time
            log_histogram("generate_answer_duration", answer_generation_duration, labels={"api_choice": api_choice})
            log_counter("generate_answer_success", labels={"api_choice": api_choice})
            return summarize_with_openrouter(config['API']['openrouter_api_key'], prompt, "")

        elif api_choice == "HuggingFace":
            from App_Function_Libraries.Summarization.Summarization_General_Lib import summarize_with_huggingface
            answer_generation_duration = time.time() - start_time
            log_histogram("generate_answer_duration", answer_generation_duration, labels={"api_choice": api_choice})
            log_counter("generate_answer_success", labels={"api_choice": api_choice})
            return summarize_with_huggingface(config['API']['huggingface_api_key'], prompt, "")

        elif api_choice == "DeepSeek":
            from App_Function_Libraries.Summarization.Summarization_General_Lib import summarize_with_deepseek
            answer_generation_duration = time.time() - start_time
            log_histogram("generate_answer_duration", answer_generation_duration, labels={"api_choice": api_choice})
            log_counter("generate_answer_success", labels={"api_choice": api_choice})
            return summarize_with_deepseek(config['API']['deepseek_api_key'], prompt, "")

        elif api_choice == "Mistral":
            from App_Function_Libraries.Summarization.Summarization_General_Lib import summarize_with_mistral
            answer_generation_duration = time.time() - start_time
            log_histogram("generate_answer_duration", answer_generation_duration, labels={"api_choice": api_choice})
            log_counter("generate_answer_success", labels={"api_choice": api_choice})
            return summarize_with_mistral(config['API']['mistral_api_key'], prompt, "")

        # Local LLM APIs
        elif api_choice == "Local-LLM":
            from App_Function_Libraries.Summarization.Local_Summarization_Lib import summarize_with_local_llm
            answer_generation_duration = time.time() - start_time
            log_histogram("generate_answer_duration", answer_generation_duration, labels={"api_choice": api_choice})
            log_counter("generate_answer_success", labels={"api_choice": api_choice})
            # FIXME
            return summarize_with_local_llm(config['Local-API']['local_llm_path'], prompt, "")

        elif api_choice == "Llama.cpp":
            from App_Function_Libraries.Summarization.Local_Summarization_Lib import summarize_with_llama
            answer_generation_duration = time.time() - start_time
            log_histogram("generate_answer_duration", answer_generation_duration, labels={"api_choice": api_choice})
            log_counter("generate_answer_success", labels={"api_choice": api_choice})
            return summarize_with_llama(prompt, "", config['Local-API']['llama_api_key'], None, None)
        elif api_choice == "Kobold":
            from App_Function_Libraries.Summarization.Local_Summarization_Lib import summarize_with_kobold
            answer_generation_duration = time.time() - start_time
            log_histogram("generate_answer_duration", answer_generation_duration, labels={"api_choice": api_choice})
            log_counter("generate_answer_success", labels={"api_choice": api_choice})
            return summarize_with_kobold(prompt, config['Local-API']['kobold_api_key'], "", system_message=None, temp=None)

        elif api_choice == "Ooba":
            from App_Function_Libraries.Summarization.Local_Summarization_Lib import summarize_with_oobabooga
            answer_generation_duration = time.time() - start_time
            log_histogram("generate_answer_duration", answer_generation_duration, labels={"api_choice": api_choice})
            log_counter("generate_answer_success", labels={"api_choice": api_choice})
            return summarize_with_oobabooga(prompt, config['Local-API']['ooba_api_key'], custom_prompt="", system_message=None, temp=None)

        elif api_choice == "TabbyAPI":
            from App_Function_Libraries.Summarization.Local_Summarization_Lib import summarize_with_tabbyapi
            answer_generation_duration = time.time() - start_time
            log_histogram("generate_answer_duration", answer_generation_duration, labels={"api_choice": api_choice})
            log_counter("generate_answer_success", labels={"api_choice": api_choice})
            return summarize_with_tabbyapi(prompt, None, None, None, None, )

        elif api_choice == "vLLM":
            from App_Function_Libraries.Summarization.Local_Summarization_Lib import summarize_with_vllm
            answer_generation_duration = time.time() - start_time
            log_histogram("generate_answer_duration", answer_generation_duration, labels={"api_choice": api_choice})
            log_counter("generate_answer_success", labels={"api_choice": api_choice})
            return summarize_with_vllm(prompt, "", config['Local-API']['vllm_api_key'], None, None)

        elif api_choice.lower() == "ollama":
            from App_Function_Libraries.Summarization.Local_Summarization_Lib import summarize_with_ollama
            answer_generation_duration = time.time() - start_time
            log_histogram("generate_answer_duration", answer_generation_duration, labels={"api_choice": api_choice})
            log_counter("generate_answer_success", labels={"api_choice": api_choice})
            return summarize_with_ollama(prompt, "", config['Local-API']['ollama_api_IP'], config['Local-API']['ollama_api_key'], None, None, None)

        elif api_choice.lower() == "custom_openai_api":
            logging.debug(f"RAG Answer Gen: Trying with Custom_OpenAI API")
            summary = summarize_with_custom_openai(prompt, "", config['API']['custom_openai_api_key'], None,
                                                   None)
        else:
            log_counter("generate_answer_error", labels={"api_choice": api_choice, "error": str()})
            raise ValueError(f"Unsupported API choice: {api_choice}")
    except Exception as e:
        log_counter("generate_answer_error", labels={"api_choice": api_choice, "error": str(e)})
        logging.error(f"Error in generate_answer: {str(e)}")
        return "An error occurred while generating the answer."


def perform_vector_search(query: str, relevant_media_ids: List[str] = None, top_k=10) -> List[Dict[str, Any]]:
    log_counter("perform_vector_search_attempt")
    start_time = time.time()
    all_collections = chroma_client.list_collections()
    vector_results = []
    try:
        for collection in all_collections:
            collection_results = vector_search(collection.name, query, k=top_k)
            if not collection_results:
                continue  # Skip empty results
            filtered_results = [
                result for result in collection_results
                if relevant_media_ids is None or result['metadata'].get('media_id') in relevant_media_ids
            ]
            vector_results.extend(filtered_results)
        search_duration = time.time() - start_time
        log_histogram("perform_vector_search_duration", search_duration)
        log_counter("perform_vector_search_success", labels={"result_count": len(vector_results)})
        return vector_results
    except Exception as e:
        log_counter("perform_vector_search_error", labels={"error": str(e)})
        logging.error(f"Error in perform_vector_search: {str(e)}")
        raise


# V2
def perform_full_text_search(query: str, database_type: str, relevant_ids: List[str] = None, fts_top_k=None) -> List[Dict[str, Any]]:
    """
    Perform full-text search on a specified database type.

    Args:
        query: Search query string
        database_type: Type of database to search ("Media DB", "RAG Chat", "RAG Notes", "Character Chat", "Character Cards")
        relevant_ids: Optional list of media IDs to filter results
        fts_top_k: Maximum number of results to return

    Returns:
        List of search results with content and metadata
    """
    log_counter("perform_full_text_search_attempt", labels={"database_type": database_type})
    start_time = time.time()

    try:
        # Set default for fts_top_k
        if fts_top_k is None:
            fts_top_k = 10

        # Call appropriate search function based on database type
        search_functions = {
            "Media DB": search_media_db,
            "RAG Chat": search_rag_chat,
            "RAG Notes": search_rag_notes,
            "Character Chat": search_character_chat,
            "Character Cards": search_character_cards
        }

        if database_type not in search_functions:
            raise ValueError(f"Unsupported database type: {database_type}")

        # Call the appropriate search function
        results = search_functions[database_type](query, fts_top_k, relevant_ids)

        search_duration = time.time() - start_time
        log_histogram("perform_full_text_search_duration", search_duration,
                      labels={"database_type": database_type})
        log_counter("perform_full_text_search_success",
                    labels={"database_type": database_type, "result_count": len(results)})

        return results

    except Exception as e:
        log_counter("perform_full_text_search_error",
                    labels={"database_type": database_type, "error": str(e)})
        logging.error(f"Error in perform_full_text_search ({database_type}): {str(e)}")
        raise


# v1
# def perform_full_text_search(query: str, relevant_media_ids: List[str] = None, fts_top_k=None) -> List[Dict[str, Any]]:
#     log_counter("perform_full_text_search_attempt")
#     start_time = time.time()
#     try:
#         fts_results = search_db(query, ["content"], "", page=1, results_per_page=fts_top_k or 10)
#         filtered_fts_results = [
#             {
#                 "content": result['content'],
#                 "metadata": {"media_id": result['id']}
#             }
#             for result in fts_results
#             if relevant_media_ids is None or result['id'] in relevant_media_ids
#         ]
#         search_duration = time.time() - start_time
#         log_histogram("perform_full_text_search_duration", search_duration)
#         log_counter("perform_full_text_search_success", labels={"result_count": len(filtered_fts_results)})
#         return filtered_fts_results
#     except Exception as e:
#         log_counter("perform_full_text_search_error", labels={"error": str(e)})
#         logging.error(f"Error in perform_full_text_search: {str(e)}")
#         raise


def fetch_relevant_media_ids(keywords: List[str], top_k=10) -> List[int]:
    log_counter("fetch_relevant_media_ids_attempt", labels={"keyword_count": len(keywords)})
    start_time = time.time()
    relevant_ids = set()
    for keyword in keywords:
        try:
            media_ids = fetch_keywords_for_media(keyword)
            relevant_ids.update(media_ids)
        except Exception as e:
            log_counter("fetch_relevant_media_ids_error", labels={"error": str(e)})
            logging.error(f"Error fetching relevant media IDs for keyword '{keyword}': {str(e)}")
            # Continue processing other keywords

    fetch_duration = time.time() - start_time
    log_histogram("fetch_relevant_media_ids_duration", fetch_duration)
    log_counter("fetch_relevant_media_ids_success", labels={"result_count": len(relevant_ids)})
    return list(relevant_ids)


def filter_results_by_keywords(results: List[Dict[str, Any]], keywords: List[str]) -> List[Dict[str, Any]]:
    log_counter("filter_results_by_keywords_attempt", labels={"result_count": len(results), "keyword_count": len(keywords)})
    start_time = time.time()
    if not keywords:
        return results

    filtered_results = []
    for result in results:
        try:
            metadata = result.get('metadata', {})
            if metadata is None:
                logging.warning(f"No metadata found for result: {result}")
                continue
            if not isinstance(metadata, dict):
                logging.warning(f"Unexpected metadata type: {type(metadata)}. Expected dict.")
                continue

            media_id = metadata.get('media_id')
            if media_id is None:
                logging.warning(f"No media_id found in metadata: {metadata}")
                continue

            media_keywords = fetch_keywords_for_media(media_id)
            if any(keyword.lower() in [mk.lower() for mk in media_keywords] for keyword in keywords):
                filtered_results.append(result)
        except Exception as e:
            logging.error(f"Error processing result: {result}. Error: {str(e)}")

    filter_duration = time.time() - start_time
    log_histogram("filter_results_by_keywords_duration", filter_duration)
    log_counter("filter_results_by_keywords_success", labels={"filtered_count": len(filtered_results)})
    return filtered_results

# FIXME: to be implememted
def extract_media_id_from_result(result: str) -> Optional[int]:
    # Implement this function based on how you store the media_id in your results
    # For example, if it's stored at the beginning of each result:
    try:
        return int(result.split('_')[0])
    except (IndexError, ValueError):
        logging.error(f"Failed to extract media_id from result: {result}")
        return None

#
#
########################################################################################################################


############################################################################################################
#
# Chat RAG

def enhanced_rag_pipeline_chat(query: str, api_choice: str, character_id: int, keywords: Optional[str] = None) -> Dict[str, Any]:
    """
    Enhanced RAG pipeline tailored for the Character Chat tab.

    Args:
        query (str): The user's input query.
        api_choice (str): The API to use for generating the response.
        character_id (int): The ID of the character being interacted with.
        keywords (Optional[str]): Comma-separated keywords to filter search results.

    Returns:
        Dict[str, Any]: Contains the generated answer and the context used.
    """
    log_counter("enhanced_rag_pipeline_chat_attempt", labels={"api_choice": api_choice, "character_id": character_id})
    start_time = time.time()
    try:
        # Load embedding provider from config, or fallback to 'openai'
        embedding_provider = config.get('Embeddings', 'provider', fallback='openai')
        logging.debug(f"Using embedding provider: {embedding_provider}")

        # Process keywords if provided
        keyword_list = [k.strip().lower() for k in keywords.split(',')] if keywords else []
        logging.debug(f"enhanced_rag_pipeline_chat - Keywords: {keyword_list}")

        # Fetch relevant chat IDs based on character_id and keywords
        if keyword_list:
            relevant_chat_ids = fetch_keywords_for_chats(keyword_list)
        else:
            relevant_chat_ids = fetch_all_chat_ids(character_id)
        logging.debug(f"enhanced_rag_pipeline_chat - Relevant chat IDs: {relevant_chat_ids}")

        if not relevant_chat_ids:
            logging.info(f"No chats found for the given keywords and character ID: {character_id}")
            # Fallback to generating answer without context
            answer = generate_answer(api_choice, "", query)
            # Metrics
            pipeline_duration = time.time() - start_time
            log_histogram("enhanced_rag_pipeline_chat_duration", pipeline_duration, labels={"api_choice": api_choice})
            log_counter("enhanced_rag_pipeline_chat_success",
                        labels={"api_choice": api_choice, "character_id": character_id})
            return {
                "answer": answer,
                "context": ""
            }

        # Perform vector search within the relevant chats
        vector_results = perform_vector_search_chat(query, relevant_chat_ids)
        logging.debug(f"enhanced_rag_pipeline_chat - Vector search results: {vector_results}")

        # Perform full-text search within the relevant chats
        # FIXME - Update for DB Selection
        fts_results = perform_full_text_search_chat(query, relevant_chat_ids)
        logging.debug("enhanced_rag_pipeline_chat - Full-text search results:")
        logging.debug("\n".join([str(item) for item in fts_results]))

        # Combine results
        all_results = vector_results + fts_results

        apply_re_ranking = True
        if apply_re_ranking:
            logging.debug("enhanced_rag_pipeline_chat - Applying Re-Ranking")
            ranker = Ranker()

            # Prepare passages for re-ranking
            passages = [{"id": i, "text": result['content']} for i, result in enumerate(all_results)]
            rerank_request = RerankRequest(query=query, passages=passages)

            # Rerank the results
            reranked_results = ranker.rerank(rerank_request)

            # Sort results based on the re-ranking score
            reranked_results = sorted(reranked_results, key=lambda x: x['score'], reverse=True)

            # Log reranked results
            logging.debug(f"enhanced_rag_pipeline_chat - Reranked results: {reranked_results}")

            # Update all_results based on reranking
            all_results = [all_results[result['id']] for result in reranked_results]

        # Extract context from top results (limit to top 10)
        context = "\n".join([result['content'] for result in all_results[:10]])
        logging.debug(f"Context length: {len(context)}")
        logging.debug(f"Context: {context[:200]}")  # Log only the first 200 characters for brevity

        # Generate answer using the selected API
        answer = generate_answer(api_choice, context, query)

        if not all_results:
            logging.info(f"No results found. Query: {query}, Keywords: {keywords}")
            return {
                "answer": "No relevant information based on your query and keywords were found in the database. Your query has been directly passed to the LLM, and here is its answer: \n\n" + answer,
                "context": "No relevant information based on your query and keywords were found in the database. The only context used was your query: \n\n" + query
            }

        return {
            "answer": answer,
            "context": context
        }

    except Exception as e:
        log_counter("enhanced_rag_pipeline_chat_error", labels={"api_choice": api_choice, "character_id": character_id, "error": str(e)})
        logging.error(f"Error in enhanced_rag_pipeline_chat: {str(e)}")
        return {
            "answer": "An error occurred while processing your request.",
            "context": ""
        }


def fetch_relevant_chat_ids(character_id: int, keywords: List[str]) -> List[int]:
    """
    Fetch chat IDs associated with a character and filtered by keywords.

    Args:
        character_id (int): The ID of the character.
        keywords (List[str]): List of keywords to filter chats.

    Returns:
        List[int]: List of relevant chat IDs.
    """
    log_counter("fetch_relevant_chat_ids_attempt", labels={"character_id": character_id, "keyword_count": len(keywords)})
    start_time = time.time()
    relevant_ids = set()
    try:
        media_ids = fetch_keywords_for_chats(keywords)
        fetch_duration = time.time() - start_time
        log_histogram("fetch_relevant_chat_ids_duration", fetch_duration)
        log_counter("fetch_relevant_chat_ids_success",
                    labels={"character_id": character_id, "result_count": len(relevant_ids)})
        relevant_ids.update(media_ids)
        return list(relevant_ids)
    except Exception as e:
        log_counter("fetch_relevant_chat_ids_error", labels={"character_id": character_id, "error": str(e)})
        logging.error(f"Error fetching relevant chat IDs: {str(e)}")
        return []


def fetch_all_chat_ids(character_id: int) -> List[int]:
    """
    Fetch all chat IDs associated with a specific character.

    Args:
        character_id (int): The ID of the character.

    Returns:
        List[int]: List of all chat IDs for the character.
    """
    log_counter("fetch_all_chat_ids_attempt", labels={"character_id": character_id})
    start_time = time.time()
    try:
        chats = get_character_chats(character_id=character_id)
        chat_ids = [chat['id'] for chat in chats]
        fetch_duration = time.time() - start_time
        log_histogram("fetch_all_chat_ids_duration", fetch_duration)
        log_counter("fetch_all_chat_ids_success", labels={"character_id": character_id, "chat_count": len(chat_ids)})
        return chat_ids
    except Exception as e:
        log_counter("fetch_all_chat_ids_error", labels={"character_id": character_id, "error": str(e)})
        logging.error(f"Error fetching all chat IDs for character {character_id}: {str(e)}")
        return []

#
# End of Chat RAG
############################################################################################################

# Function to preprocess and store all existing content in the database
# def preprocess_all_content(database, create_contextualized=True, api_name="gpt-3.5-turbo"):
#     unprocessed_media = get_unprocessed_media()
#     total_media = len(unprocessed_media)
#
#     for index, row in enumerate(unprocessed_media, 1):
#         media_id, content, media_type, file_name = row
#         collection_name = f"{media_type}_{media_id}"
#
#         logger.info(f"Processing media {index} of {total_media}: ID {media_id}, Type {media_type}")
#
#         try:
#             process_and_store_content(
#                 database=database,
#                 content=content,
#                 collection_name=collection_name,
#                 media_id=media_id,
#                 file_name=file_name or f"{media_type}_{media_id}",
#                 create_embeddings=True,
#                 create_contextualized=create_contextualized,
#                 api_name=api_name
#             )
#
#             # Mark the media as processed in the database
#             mark_media_as_processed(database, media_id)
#
#             logger.info(f"Successfully processed media ID {media_id}")
#         except Exception as e:
#             logger.error(f"Error processing media ID {media_id}: {str(e)}")
#
#     logger.info("Finished preprocessing all unprocessed content")

############################################################################################################
#
# ElasticSearch Retriever

# https://github.com/langchain-ai/langchain/tree/44e3e2391c48bfd0a8e6a20adde0b6567f4f43c3/templates/rag-elasticsearch
#
# https://github.com/langchain-ai/langchain/tree/44e3e2391c48bfd0a8e6a20adde0b6567f4f43c3/templates/rag-self-query

#
# End of RAG_Library_2.py
############################################################################################################
