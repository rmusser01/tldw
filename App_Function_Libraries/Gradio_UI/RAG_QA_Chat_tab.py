# RAG_QA_Chat_tab.py
# Description: Gradio UI for RAG QA Chat
#
# Imports
import csv
import logging
import json
import os
from datetime import datetime
#
# External Imports
import docx2txt
import gradio as gr
# Local Imports
from App_Function_Libraries.Books.Book_Ingestion_Lib import read_epub
from App_Function_Libraries.DB.DB_Manager import DatabaseError, get_paginated_files, add_media_with_keywords
from App_Function_Libraries.PDF.PDF_Ingestion_Lib import extract_text_and_format_from_pdf
from App_Function_Libraries.RAG.RAG_Library_2 import generate_answer, enhanced_rag_pipeline
from App_Function_Libraries.RAG.RAG_QA_Chat import search_database, rag_qa_chat
# Eventually... FIXME
from App_Function_Libraries.RAG.RAG_QA_Chat import load_chat_history, save_chat_history
#
########################################################################################################################
#
# Functions:

def create_rag_qa_chat_tab():
    with gr.TabItem("RAG QA Chat", visible=True):
        gr.Markdown("# RAG QA Chat")

        with gr.Row():
            with gr.Column(scale=1):
                context_source = gr.Radio(
                    ["All Files in the Database", "Search Database", "Upload File"],
                    label="Context Source",
                    value="All Files in the Database"
                )
                existing_file = gr.Dropdown(label="Select Existing File", choices=[], interactive=True)
                file_page = gr.State(value=1)
                with gr.Row():
                    prev_page_btn = gr.Button("Previous Page")
                    next_page_btn = gr.Button("Next Page")
                    page_info = gr.HTML("Page 1")

                search_query = gr.Textbox(label="Search Query", visible=False)
                search_button = gr.Button("Search", visible=False)
                search_results = gr.Dropdown(label="Search Results", choices=[], visible=False)
                file_upload = gr.File(
                    label="Upload File",
                    visible=False,
                    file_types=["txt", "pdf", "epub", "md", "rtf", "json", "csv"]
                )
                convert_to_text = gr.Checkbox(label="Convert to plain text", visible=False)
                keywords = gr.Textbox(label="Keywords (comma-separated)", visible=False)

                api_choice = gr.Dropdown(
                    choices=["Local-LLM", "OpenAI", "Anthropic", "Cohere", "Groq", "DeepSeek", "Mistral", "OpenRouter", "Llama.cpp", "Kobold", "Ooba", "Tabbyapi", "VLLM", "ollama", "HuggingFace"],
                    label="Select API for RAG",
                    value="OpenAI"
                )
                use_query_rewriting = gr.Checkbox(label="Use Query Rewriting", value=True)

            with gr.Column(scale=2):
                chatbot = gr.Chatbot(height=500)
                msg = gr.Textbox(label="Enter your message")
                submit = gr.Button("Submit (Might take a few seconds/turns blue while processing...)")
                clear_chat = gr.Button("Clear Chat History")

        loading_indicator = gr.HTML(visible=False)

        def update_file_list(page):
            files, total_pages, current_page = get_paginated_files(page)
            choices = [f"{title} (ID: {id})" for id, title in files]
            return gr.update(choices=choices), gr.update(value=f"Page {current_page} of {total_pages}"), current_page

        def next_page_fn(current_page):
            return update_file_list(current_page + 1)

        def prev_page_fn(current_page):
            return update_file_list(max(1, current_page - 1))

        def update_context_source(choice):
            return {
                existing_file: gr.update(visible=choice == "Existing File"),
                prev_page_btn: gr.update(visible=choice == "Existing File"),
                next_page_btn: gr.update(visible=choice == "Existing File"),
                page_info: gr.update(visible=choice == "Existing File"),
                search_query: gr.update(visible=choice == "Search Database"),
                search_button: gr.update(visible=choice == "Search Database"),
                search_results: gr.update(visible=choice == "Search Database"),
                file_upload: gr.update(visible=choice == "Upload File"),
                convert_to_text: gr.update(visible=choice == "Upload File"),
                keywords: gr.update(visible=choice == "Upload File")
            }

        context_source.change(update_context_source, context_source,
                              [existing_file, prev_page_btn, next_page_btn, page_info, search_query, search_button,
                               search_results, file_upload, convert_to_text, keywords])

        next_page_btn.click(next_page_fn, inputs=[file_page], outputs=[existing_file, page_info, file_page])
        prev_page_btn.click(prev_page_fn, inputs=[file_page], outputs=[existing_file, page_info, file_page])

        # Initialize the file list
        context_source.change(lambda: update_file_list(1), outputs=[existing_file, page_info, file_page])

        loading_indicator = gr.HTML(visible=False)

        def rag_qa_chat_wrapper(message, history, context_source, existing_file, search_results, file_upload,
                                convert_to_text, keywords, api_choice, use_query_rewriting):
            try:
                logging.info(f"Starting rag_qa_chat_wrapper with message: {message}")
                logging.info(f"Context source: {context_source}")
                logging.info(f"API choice: {api_choice}")
                logging.info(f"Query rewriting: {'enabled' if use_query_rewriting else 'disabled'}")

                # Show loading indicator
                yield history, "", gr.update(visible=True)

                # Ensure api_choice is a string
                api_choice = api_choice.value if isinstance(api_choice, gr.components.Dropdown) else api_choice
                logging.info(f"Resolved API choice: {api_choice}")

                # Only rephrase the question if it's not the first query and query rewriting is enabled
                if len(history) > 0 and use_query_rewriting:
                    rephrased_question = rephrase_question(history, message, api_choice)
                    logging.info(f"Original question: {message}")
                    logging.info(f"Rephrased question: {rephrased_question}")
                else:
                    rephrased_question = message
                    logging.info(f"Using original question: {message}")

                if context_source == "All Files in the Database":
                    # Use the enhanced_rag_pipeline to search the entire database
                    context = enhanced_rag_pipeline(rephrased_question, api_choice)
                    logging.info(f"Using enhanced_rag_pipeline for database search")
                elif context_source == "Search Database":
                    context = f"media_id:{search_results.split('(ID: ')[1][:-1]}"
                    logging.info(f"Using search result with context: {context}")
                else:  # Upload File
                    logging.info("Processing uploaded file")
                    if file_upload is None:
                        raise ValueError("No file uploaded")

                    # Process the uploaded file
                    file_path = file_upload.name
                    file_name = os.path.basename(file_path)
                    logging.info(f"Uploaded file: {file_name}")

                    if convert_to_text:
                        logging.info("Converting file to plain text")
                        content = convert_file_to_text(file_path)
                    else:
                        logging.info("Reading file content")
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()

                    logging.info(f"File content length: {len(content)} characters")

                    # Process keywords
                    if not keywords:
                        keywords = "default,rag-file-upload"
                    logging.info(f"Keywords: {keywords}")

                    # Add the content to the database and get the media_id
                    logging.info("Adding content to database")
                    result = add_media_with_keywords(
                        url=file_name,
                        title=file_name,
                        media_type='document',
                        content=content,
                        keywords=keywords,
                        prompt='No prompt for uploaded files',
                        summary='No summary for uploaded files',
                        transcription_model='None',
                        author='Unknown',
                        ingestion_date=datetime.now().strftime('%Y-%m-%d')
                    )

                    logging.info(f"Result from add_media_with_keywords: {result}")
                    if isinstance(result, tuple):
                        media_id, _ = result
                    else:
                        media_id = result

                    context = f"media_id:{media_id}"
                    logging.info(f"Context for uploaded file: {context}")

                logging.info("Calling rag_qa_chat function")
                new_history, response = rag_qa_chat(rephrased_question, history, context, api_choice)
                # Log first 100 chars of response
                logging.info(
                    f"Response received from rag_qa_chat: {response[:100]}...")

                # Safely update history
                if new_history:
                    new_history[-1] = (message, new_history[-1][1])
                else:
                    new_history = [(message, response)]

                gr.Info("Response generated successfully")
                logging.info("rag_qa_chat_wrapper completed successfully")
                yield new_history, "", gr.update(visible=False)
            except ValueError as e:
                logging.error(f"Input error in rag_qa_chat_wrapper: {str(e)}")
                gr.Error(f"Input error: {str(e)}")
                yield history, "", gr.update(visible=False)
            except DatabaseError as e:
                logging.error(f"Database error in rag_qa_chat_wrapper: {str(e)}")
                gr.Error(f"Database error: {str(e)}")
                yield history, "", gr.update(visible=False)
            except Exception as e:
                logging.error(f"Unexpected error in rag_qa_chat_wrapper: {e}", exc_info=True)
                gr.Error("An unexpected error occurred. Please try again later.")
                yield history, "", gr.update(visible=False)

        def rephrase_question(history, latest_question, api_choice):
            # Thank you https://www.reddit.com/r/LocalLLaMA/comments/1fi1kex/multi_turn_conversation_and_rag/
            logging.info("RAG QnA: Rephrasing question")
            conversation_history = "\n".join([f"User: {h[0]}\nAssistant: {h[1]}" for h in history[:-1]])
            prompt = f"""You are a helpful assistant. Given the conversation history and the latest question, resolve any ambiguous references in the latest question.

        Conversation History:
        {conversation_history}

        Latest Question:
        {latest_question}

        Rewritten Question:"""

            # Use the selected API to generate the rephrased question
            rephrased_question = generate_answer(api_choice, prompt, "")
            logging.info(f"Rephrased question: {rephrased_question}")
            return rephrased_question.strip()

        def perform_search(query):
            try:
                results = search_database(query)
                return gr.update(choices=results)
            except Exception as e:
                gr.Error(f"Error performing search: {str(e)}")
                return gr.update(choices=[])

        def clear_chat_history():
            return [], ""

        search_button.click(perform_search, inputs=[search_query], outputs=[search_results])

        submit.click(
            rag_qa_chat_wrapper,
            inputs=[msg, chatbot, context_source, existing_file, search_results, file_upload,
                    convert_to_text, keywords, api_choice, use_query_rewriting],
            outputs=[chatbot, msg, loading_indicator]
        )

        clear_chat.click(clear_chat_history, outputs=[chatbot, msg])

    return (context_source, existing_file, search_query, search_button, search_results, file_upload,
            convert_to_text, keywords, api_choice, use_query_rewriting, chatbot, msg, submit, clear_chat)

def convert_file_to_text(file_path):
    """Convert various file types to plain text."""
    file_extension = os.path.splitext(file_path)[1].lower()

    if file_extension == '.pdf':
        return extract_text_and_format_from_pdf(file_path)
    elif file_extension == '.epub':
        return read_epub(file_path)
    elif file_extension in ['.json', '.csv']:
        return read_structured_file(file_path)
    elif file_extension == '.docx':
        return docx2txt.process(file_path)
    elif file_extension in ['.txt', '.md', '.rtf']:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    else:
        raise ValueError(f"Unsupported file type: {file_extension}")

def read_structured_file(file_path):
    """Read and convert JSON or CSV files to text."""
    file_extension = os.path.splitext(file_path)[1].lower()

    if file_extension == '.json':
        with open(file_path, 'r') as file:
            data = json.load(file)
        return json.dumps(data, indent=2)

    elif file_extension == '.csv':
        with open(file_path, 'r', newline='') as file:
            csv_reader = csv.reader(file)
            return '\n'.join([','.join(row) for row in csv_reader])

    else:
        raise ValueError(f"Unsupported file type: {file_extension}")

#
# End of RAG_QA_Chat_tab.py
########################################################################################################################
#