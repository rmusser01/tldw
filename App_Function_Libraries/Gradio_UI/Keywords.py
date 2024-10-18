# Keywords.py
# Purpose: This file contains the functions to create the Keywords tab in the Gradio UI.
#
# The Keywords tab allows the user to add, delete, view, and export keywords from the database.
#
# Imports:

#
# External Imports
import gradio as gr
#
# Internal Imports
from App_Function_Libraries.DB.DB_Manager import add_keyword, delete_keyword, keywords_browser_interface, export_keywords_to_csv
#
#
######################################################################################################################
#
# Functions:


def create_export_keywords_tab():
    with gr.TabItem("Export Keywords", visible=True):
        with gr.Row():
            with gr.Column():
                export_keywords_button = gr.Button("Export Keywords")
            with gr.Column():
                export_keywords_output = gr.File(label="Download Exported Keywords")
                export_keywords_status = gr.Textbox(label="Export Status")

            export_keywords_button.click(
                fn=export_keywords_to_csv,
                outputs=[export_keywords_status, export_keywords_output]
            )

def create_view_keywords_tab():
    with gr.TabItem("View Keywords", visible=True):
        gr.Markdown("# Browse Keywords")
        with gr.Column():
            browse_output = gr.Markdown()
            browse_button = gr.Button("View Existing Keywords")
            browse_button.click(fn=keywords_browser_interface, outputs=browse_output)


def create_add_keyword_tab():
    with gr.TabItem("Add Keywords", visible=True):
        with gr.Row():
            with gr.Column():
                gr.Markdown("# Add Keywords to the Database")
                add_input = gr.Textbox(label="Add Keywords (comma-separated)", placeholder="Enter keywords here...")
                add_button = gr.Button("Add Keywords")
            with gr.Row():
                add_output = gr.Textbox(label="Result")
                add_button.click(fn=add_keyword, inputs=add_input, outputs=add_output)


def create_delete_keyword_tab():
    with gr.Tab("Delete Keywords", visible=True):
        with gr.Row():
            with gr.Column():
                gr.Markdown("# Delete Keywords from the Database")
                delete_input = gr.Textbox(label="Delete Keyword", placeholder="Enter keyword to delete here...")
                delete_button = gr.Button("Delete Keyword")
            with gr.Row():
                delete_output = gr.Textbox(label="Result")
                delete_button.click(fn=delete_keyword, inputs=delete_input, outputs=delete_output)
