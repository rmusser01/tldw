# Book_Ingestion_tab.py
# Functionality to import epubs/ebooks into the system.
####################
# Function List
#
# 1. create_import_book_tab()
# 2. import_epub(epub_file, title, author, keywords, system_prompt, user_prompt, auto_summarize, api_name, api_key)
#
####################
# Imports
#
# External Imports
import gradio as gr
#
# Local Imports
from App_Function_Libraries.Books.Book_Ingestion_Lib import process_zip_file, import_epub, import_file_handler
#
########################################################################################################################
#
# Functions:



def create_import_book_tab():
    with gr.TabItem("Ebook(epub) Files", visible=True):
        with gr.Row():
            with gr.Column():
                gr.Markdown("# Import .epub files")
                gr.Markdown("Upload a single .epub file or a .zip file containing multiple .epub files")
                gr.Markdown(
                    "🔗 **How to remove DRM from your ebooks:** [Reddit Guide](https://www.reddit.com/r/Calibre/comments/1ck4w8e/2024_guide_on_removing_drm_from_kobo_kindle_ebooks/)")
                import_file = gr.File(label="Upload file for import", file_types=[".epub", ".zip"])
                title_input = gr.Textbox(label="Title", placeholder="Enter the title of the content (for single files)")
                author_input = gr.Textbox(label="Author", placeholder="Enter the author's name (for single files)")
                keywords_input = gr.Textbox(label="Keywords (like genre or publish year)",
                                            placeholder="Enter keywords, comma-separated")
                system_prompt_input = gr.Textbox(label="System Prompt", lines=3,
                                                 value=""""
                                                    <s>You are a bulleted notes specialist. [INST]```When creating comprehensive bulleted notes, you should follow these guidelines: Use multiple headings based on the referenced topics, not categories like quotes or terms. Headings should be surrounded by bold formatting and not be listed as bullet points themselves. Leave no space between headings and their corresponding list items underneath. Important terms within the content should be emphasized by setting them in bold font. Any text that ends with a colon should also be bolded. Before submitting your response, review the instructions, and make any corrections necessary to adhered to the specified format. Do not reference these instructions within the notes.``` \nBased on the content between backticks create comprehensive bulleted notes.[/INST]
                                                    **Bulleted Note Creation Guidelines**

                                                    **Headings**:
                                                    - Based on referenced topics, not categories like quotes or terms
                                                    - Surrounded by **bold** formatting 
                                                    - Not listed as bullet points
                                                    - No space between headings and list items underneath

                                                    **Emphasis**:
                                                    - **Important terms** set in bold font
                                                    - **Text ending in a colon**: also bolded

                                                    **Review**:
                                                    - Ensure adherence to specified format
                                                    - Do not reference these instructions in your response.</s>[INST] {{ .Prompt }} [/INST]
                                                """, )
                custom_prompt_input = gr.Textbox(label="Custom User Prompt",
                                                 placeholder="Enter a custom user prompt for summarization (optional)")
                auto_summarize_checkbox = gr.Checkbox(label="Auto-summarize", value=False)
                api_name_input = gr.Dropdown(
                    choices=[None, "Local-LLM", "OpenAI", "Anthropic", "Cohere", "Groq", "DeepSeek", "Mistral",
                             "OpenRouter", "Llama.cpp", "Kobold", "Ooba", "Tabbyapi", "VLLM", "ollama", "HuggingFace"],
                    label="API for Auto-summarization"
                )
                api_key_input = gr.Textbox(label="API Key", type="password")

                # Chunking options
                max_chunk_size = gr.Slider(minimum=100, maximum=2000, value=500, step=50, label="Max Chunk Size")
                chunk_overlap = gr.Slider(minimum=0, maximum=500, value=200, step=10, label="Chunk Overlap")
                custom_chapter_pattern = gr.Textbox(label="Custom Chapter Pattern (optional)",
                                                    placeholder="Enter a custom regex pattern for chapter detection")


                import_button = gr.Button("Import eBook(s)")
            with gr.Column():
                with gr.Row():
                    import_output = gr.Textbox(label="Import Status", lines=10, interactive=False)

        import_button.click(
            fn=import_file_handler,
            inputs=[
                import_file,
                title_input,
                author_input,
                keywords_input,
                custom_prompt_input,
                auto_summarize_checkbox,
                api_name_input,
                api_key_input,
                max_chunk_size,
                chunk_overlap,
                custom_chapter_pattern
            ],
            outputs=import_output
        )

    return import_file, title_input, author_input, keywords_input, system_prompt_input, custom_prompt_input, auto_summarize_checkbox, api_name_input, api_key_input, import_button, import_output

#
# End of File
########################################################################################################################