# PDF_ingestion_tab.py
# Gradio UI for ingesting PDFs into the database
import os
import shutil
import tempfile

# Imports
#
# External Imports
import gradio as gr
#
# Local Imports
from App_Function_Libraries.DB.DB_Manager import load_preset_prompts
from App_Function_Libraries.Gradio_UI.Chat_ui import update_user_prompt
from App_Function_Libraries.PDF.PDF_Ingestion_Lib import extract_metadata_from_pdf, extract_text_and_format_from_pdf, \
    process_and_cleanup_pdf
#
#
########################################################################################################################
#
# Functions:

def create_pdf_ingestion_tab():
    with gr.TabItem("PDF Ingestion", visible=True):
        # TODO - Add functionality to extract metadata from pdf as part of conversion process in marker
        gr.Markdown("# Ingest PDF Files and Extract Metadata")
        with gr.Row():
            with gr.Column():
                pdf_file_input = gr.File(label="Uploaded PDF File", file_types=[".pdf"], visible=True)
                pdf_upload_button = gr.UploadButton("Click to Upload PDF", file_types=[".pdf"])
                pdf_title_input = gr.Textbox(label="Title (Optional)")
                pdf_author_input = gr.Textbox(label="Author (Optional)")
                pdf_keywords_input = gr.Textbox(label="Keywords (Optional, comma-separated)")
                with gr.Row():
                    custom_prompt_checkbox = gr.Checkbox(label="Use a Custom Prompt",
                                                     value=False,
                                                     visible=True)
                    preset_prompt_checkbox = gr.Checkbox(label="Use a pre-set Prompt",
                                                     value=False,
                                                     visible=True)
                with gr.Row():
                    preset_prompt = gr.Dropdown(label="Select Preset Prompt",
                                                choices=load_preset_prompts(),
                                                visible=False)
                with gr.Row():
                    custom_prompt_input = gr.Textbox(label="Custom Prompt",
                                                     placeholder="Enter custom prompt here",
                                                     lines=3,
                                                     visible=False)
                with gr.Row():
                    system_prompt_input = gr.Textbox(label="System Prompt",
                                                     value="""
<s>You are a bulleted notes specialist.
[INST]```When creating comprehensive bulleted notes, you should follow these guidelines: Use multiple headings based on the referenced topics, not categories like quotes or terms. Headings should be surrounded by bold formatting and not be listed as bullet points themselves. Leave no space between headings and their corresponding list items underneath. Important terms within the content should be emphasized by setting them in bold font. Any text that ends with a colon should also be bolded. Before submitting your response, review the instructions, and make any corrections necessary to adhered to the specified format. Do not reference these instructions within the notes.``` \nBased on the content between backticks create comprehensive bulleted notes.[/INST]
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
- Do not reference these instructions in your response.</s>[INST] {{ .Prompt }} [/INST]""",
                                                     lines=3,
                                                     visible=False)

                custom_prompt_checkbox.change(
                    fn=lambda x: (gr.update(visible=x), gr.update(visible=x)),
                    inputs=[custom_prompt_checkbox],
                    outputs=[custom_prompt_input, system_prompt_input]
                )
                preset_prompt_checkbox.change(
                    fn=lambda x: gr.update(visible=x),
                    inputs=[preset_prompt_checkbox],
                    outputs=[preset_prompt]
                )

                def update_prompts(preset_name):
                    prompts = update_user_prompt(preset_name)
                    return (
                        gr.update(value=prompts["user_prompt"], visible=True),
                        gr.update(value=prompts["system_prompt"], visible=True)
                    )

                preset_prompt.change(
                    update_prompts,
                    inputs=preset_prompt,
                    outputs=[custom_prompt_input, system_prompt_input]
                )

                pdf_ingest_button = gr.Button("Ingest PDF")

                pdf_upload_button.upload(fn=lambda file: file, inputs=pdf_upload_button, outputs=pdf_file_input)
            with gr.Column():
                pdf_result_output = gr.Textbox(label="Result")

            pdf_ingest_button.click(
                fn=process_and_cleanup_pdf,
                inputs=[pdf_file_input, pdf_title_input, pdf_author_input, pdf_keywords_input],
                outputs=pdf_result_output
            )


def test_pdf_ingestion(pdf_file):
    if pdf_file is None:
        return "No file uploaded", ""

    try:
        # Create a temporary directory
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a path for the temporary PDF file
            temp_path = os.path.join(temp_dir, "temp.pdf")

            # Copy the contents of the uploaded file to the temporary file
            shutil.copy(pdf_file.name, temp_path)

            # Extract text and convert to Markdown
            markdown_text = extract_text_and_format_from_pdf(temp_path)

            # Extract metadata from PDF
            metadata = extract_metadata_from_pdf(temp_path)

            # Use metadata for title and author if not provided
            title = metadata.get('title', os.path.splitext(os.path.basename(pdf_file.name))[0])
            author = metadata.get('author', 'Unknown')

        result = f"PDF '{title}' by {author} processed successfully."
        return result, markdown_text
    except Exception as e:
        return f"Error ingesting PDF: {str(e)}", ""

def create_pdf_ingestion_test_tab():
    with gr.TabItem("Test PDF Ingestion", visible=True):
        with gr.Row():
            with gr.Column():
                pdf_file_input = gr.File(label="Upload PDF for testing")
                test_button = gr.Button("Test PDF Ingestion")
            with gr.Column():
                test_output = gr.Textbox(label="Test Result")
                pdf_content_output = gr.Textbox(label="PDF Content", lines=200)
        test_button.click(
            fn=test_pdf_ingestion,
            inputs=[pdf_file_input],
            outputs=[test_output, pdf_content_output]
        )

