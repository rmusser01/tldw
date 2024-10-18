# RAG_QA_Chat_Notes.py
# Description: This file contains the code for the RAG QA Chat Notes tab in the RAG QA Chat application.
#
# Imports
import logging
# External Imports
import gradio as gr
#
# Local Imports
from App_Function_Libraries.DB.RAG_QA_Chat_DB import save_message, add_keywords_to_conversation, \
    search_conversations_by_keywords, load_chat_history, save_notes, get_notes, clear_notes, \
    add_keywords_to_note, execute_query, start_new_conversation
from App_Function_Libraries.RAG.RAG_QA_Chat import rag_qa_chat
#
####################################################################################################
#
# Functions
def create_rag_qa_chat_notes_tab():
    with gr.TabItem("RAG QA Chat", visible=True):
        gr.Markdown("# RAG QA Chat")

        state = gr.State({
            "conversation_id": None,
            "page": 1,
            "context_source": "Entire Media Database",
        })

        with gr.Row():
            with gr.Column(scale=1):
                context_source = gr.Radio(
                    ["Entire Media Database", "Search Database", "Upload File"],
                    label="Context Source",
                    value="Entire Media Database"
                )
                existing_file = gr.Dropdown(label="Select Existing File", choices=[], interactive=True)
                file_page = gr.State(value=1)
                with gr.Row():
                    page_number = gr.Number(value=1, label="Page", precision=0)
                    page_size = gr.Number(value=20, label="Items per page", precision=0)
                    total_pages = gr.Number(label="Total Pages", interactive=False)
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
            with gr.Column(scale=1):
                api_choice = gr.Dropdown(
                    choices=["Local-LLM", "OpenAI", "Anthropic", "Cohere", "Groq", "DeepSeek", "Mistral", "OpenRouter",
                             "Llama.cpp", "Kobold", "Ooba", "Tabbyapi", "VLLM", "ollama", "HuggingFace"],
                    label="Select API for RAG",
                    value="OpenAI"
                )
                use_query_rewriting = gr.Checkbox(label="Use Query Rewriting", value=True)

                # FIXME - add load conversations button
                load_conversation = gr.Dropdown(label="Load Conversation", choices=[])
                new_conversation = gr.Button("New Conversation")
                conversation_title = gr.Textbox(label="Conversation Title",
                                                placeholder="Enter a title for the new conversation")

        with gr.Row():
            with gr.Column(scale=2):
                chatbot = gr.Chatbot(height=500)
                msg = gr.Textbox(label="Enter your message")
                submit = gr.Button("Submit")
                clear_chat = gr.Button("Clear Chat History")

            with gr.Column(scale=1):
                notes = gr.TextArea(label="Notes", placeholder="Enter your notes here...", lines=20)
                keywords_for_notes = gr.Textbox(label="Keywords for Notes (comma-separated)",
                                                placeholder="Enter keywords for the note", visible=True)
                save_notes_btn = gr.Button("Save Notes")  # Renamed to avoid conflict
                clear_notes_btn = gr.Button("Clear Notes")  # Renamed to avoid conflict

        loading_indicator = gr.HTML(visible=False)

        def rag_qa_chat_wrapper(message, history, state, context_source, existing_file, search_results, file_upload,
                                convert_to_text, keywords, api_choice, use_query_rewriting):
            try:
                conversation_id = state.value["conversation_id"]
                if not conversation_id:
                    conversation_id = start_new_conversation("Untitled Conversation")  # Provide a title or handle accordingly
                    state = update_state(state, conversation_id=conversation_id)

                save_message(conversation_id, 'human', message)

                if keywords:
                    add_keywords_to_conversation(conversation_id, [kw.strip() for kw in keywords.split(',')])

                # Implement your actual RAG logic here
                response = "response"#rag_qa_chat(message, conversation_id, context_source, existing_file, search_results,
                                       #file_upload, convert_to_text, api_choice, use_query_rewriting)

                save_message(conversation_id, 'ai', response)

                new_history = history + [(message, response)]

                logging.info(f"Successfully processed message for conversation '{conversation_id}'")
                return new_history, "", gr.update(visible=False), state

            except Exception as e:
                logging.error(f"Error in rag_qa_chat_wrapper: {e}")
                gr.Error("An unexpected error occurred. Please try again later.")
                return history, "", gr.update(visible=False), state

        def load_conversation_history(selected_conversation_id, page, page_size, state):
            if selected_conversation_id:
                history, total_pages_val, _ = load_chat_history(selected_conversation_id, page, page_size)
                notes_content = get_notes(selected_conversation_id)  # Retrieve notes here
                updated_state = update_state(state, conversation_id=selected_conversation_id, page=page)
                return history, total_pages_val, updated_state, "\n".join(notes_content)
            return [], 1, state, ""

        def start_new_conversation_wrapper(title, state):
            new_conversation_id = start_new_conversation(title if title else "Untitled Conversation")
            return [], update_state(state, conversation_id=new_conversation_id, page=1)

        def update_state(state, **kwargs):
            new_state = state.value.copy()
            new_state.update(kwargs)
            return new_state

        def update_page(direction, current_page, total_pages_val):
            new_page = max(1, min(current_page + direction, total_pages_val))
            return new_page

        def update_context_source(choice):
            return {
                existing_file: gr.update(visible=choice == "Select Existing File"),
                prev_page_btn: gr.update(visible=choice == "Search Database"),
                next_page_btn: gr.update(visible=choice == "Search Database"),
                page_info: gr.update(visible=choice == "Search Database"),
                search_query: gr.update(visible=choice == "Search Database"),
                search_button: gr.update(visible=choice == "Search Database"),
                search_results: gr.update(visible=choice == "Search Database"),
                file_upload: gr.update(visible=choice == "Upload File"),
                convert_to_text: gr.update(visible=choice == "Upload File"),
                keywords: gr.update(visible=choice == "Upload File")
            }

        def perform_search(query):
            try:
                results = search_conversations_by_keywords([kw.strip() for kw in query.split()])
                return gr.update(choices=[f"{title} (ID: {id})" for id, title in results[0]])
            except Exception as e:
                logging.error(f"Error performing search: {e}")
                gr.Error(f"Error performing search: {str(e)}")
                return gr.update(choices=[])

        def clear_chat_history():
            return [], ""

        def save_notes_function(notes_content, keywords_content):
            """Save the notes and associated keywords to the database."""
            conversation_id = state.value["conversation_id"]
            if conversation_id and notes_content:
                # Save the note
                save_notes(conversation_id, notes_content)

                # Get the last inserted note ID
                query = "SELECT id FROM rag_qa_notes WHERE conversation_id = ? ORDER BY timestamp DESC LIMIT 1"
                note_id = execute_query(query, (conversation_id,))[0][0]

                if keywords_content:
                    add_keywords_to_note(note_id, [kw.strip() for kw in keywords_content.split(',')])

                logging.info("Notes and keywords saved successfully!")
                return notes_content
            else:
                logging.warning("No conversation ID or notes to save.")
                return ""

        def clear_notes_function():
            """Clear notes for the current conversation."""
            conversation_id = state.value["conversation_id"]
            if conversation_id:
                clear_notes(conversation_id)
                logging.info("Notes cleared successfully!")
            return ""

        # Event handlers
        submit.click(
            rag_qa_chat_wrapper,
            inputs=[msg, chatbot, state, context_source, existing_file, search_results, file_upload,
                    convert_to_text, keywords, api_choice, use_query_rewriting],
            outputs=[chatbot, msg, loading_indicator, state]
        )

        load_conversation.change(
            load_conversation_history,
            inputs=[load_conversation, page_number, page_size, state],
            outputs=[chatbot, total_pages, state, notes]
        )

        new_conversation.click(
            start_new_conversation_wrapper,
            inputs=[conversation_title, state],
            outputs=[chatbot, state]
        )

        # Pagination Event handlers
        prev_page_btn.click(
            lambda current_page, total_pages_val: update_page(-1, current_page, total_pages_val),
            inputs=[page_number, total_pages],
            outputs=[page_number]
        )

        next_page_btn.click(
            lambda current_page, total_pages_val: update_page(1, current_page, total_pages_val),
            inputs=[page_number, total_pages],
            outputs=[page_number]
        )

        context_source.change(update_context_source, inputs=[context_source],
                              outputs=[existing_file, prev_page_btn, next_page_btn, page_info,
                                       search_query, search_button, search_results,
                                       file_upload, convert_to_text, keywords])

        search_button.click(perform_search, inputs=[search_query], outputs=[search_results])

        clear_chat.click(clear_chat_history, outputs=[chatbot, msg])

        save_notes_btn.click(save_notes_function, inputs=[notes, keywords_for_notes], outputs=[notes])
        clear_notes_btn.click(clear_notes_function, outputs=[notes])

    return (context_source, existing_file, search_query, search_button, search_results, file_upload,
            convert_to_text, keywords, api_choice, use_query_rewriting, chatbot, msg, submit, clear_chat,
            notes, save_notes_btn, clear_notes_btn, load_conversation, new_conversation, conversation_title,
            prev_page_btn, next_page_btn, page_number, page_size, total_pages)

#
# End of RAG_QA_Chat_Notes.py
####################################################################################################
