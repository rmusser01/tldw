# Rag_Chat_tab.py
# Description: This file contains the code for the RAG Chat tab in the Gradio UI
#
# Imports
import logging
#
# External Imports
import gradio as gr
#
# Local Imports

from App_Function_Libraries.RAG.RAG_Library_2 import enhanced_rag_pipeline
#
########################################################################################################################
#
# Functions:

def create_rag_tab():
    with gr.TabItem("RAG Search", visible=True):
        gr.Markdown("# Retrieval-Augmented Generation (RAG) Search")

        with gr.Row():
            with gr.Column():
                search_query = gr.Textbox(label="Enter your question", placeholder="What would you like to know?")

                keyword_filtering_checkbox = gr.Checkbox(label="Enable Keyword Filtering", value=False)

                keywords_input = gr.Textbox(
                    label="Enter keywords (comma-separated)",
                    value="keyword1, keyword2, ...",
                    visible=False
                )

                keyword_instructions = gr.Markdown(
                    "Enter comma-separated keywords to filter your search results.",
                    visible=False
                )

                api_choice = gr.Dropdown(
                    choices=["Local-LLM", "OpenAI", "Anthropic", "Cohere", "Groq", "DeepSeek", "Mistral", "OpenRouter", "Llama.cpp", "Kobold", "Ooba", "Tabbyapi", "VLLM", "ollama", "HuggingFace"],
                    label="Select API for RAG",
                    value="OpenAI"
                )
                search_button = gr.Button("Search")

            with gr.Column():
                result_output = gr.Textbox(label="Answer", lines=10)
                context_output = gr.Textbox(label="Context", lines=10, visible=True)

        def toggle_keyword_filtering(checkbox_value):
            return {
                keywords_input: gr.update(visible=checkbox_value),
                keyword_instructions: gr.update(visible=checkbox_value)
            }

        keyword_filtering_checkbox.change(
            toggle_keyword_filtering,
            inputs=[keyword_filtering_checkbox],
            outputs=[keywords_input, keyword_instructions]
        )

        def perform_rag_search(query, keywords, api_choice):
            if keywords == "keyword1, keyword2, ...":
                keywords = None
            result = enhanced_rag_pipeline(query, api_choice, keywords)
            return result['answer'], result['context']

        search_button.click(perform_rag_search, inputs=[search_query, keywords_input, api_choice], outputs=[result_output, context_output])



#
# End of file
########################################################################################################################

