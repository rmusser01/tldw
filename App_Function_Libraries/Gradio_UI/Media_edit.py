# Media_edit.py
# Functions for Gradio Media_Edit UI

# Imports
import logging
import uuid

# External Imports
import gradio as gr
#
# Local Imports
from App_Function_Libraries.DB.DB_Manager import add_prompt, update_media_content, db, add_or_update_prompt, \
    load_prompt_details, fetch_keywords_for_media, update_keywords_for_media
from App_Function_Libraries.Gradio_UI.Gradio_Shared import update_dropdown, update_prompt_dropdown
from App_Function_Libraries.DB.SQLite_DB import fetch_item_details


def create_media_edit_tab():
    with gr.TabItem("Edit Existing Items", visible=True):
        gr.Markdown("# Search and Edit Media Items")

        with gr.Row():
            search_query_input = gr.Textbox(label="Search Query", placeholder="Enter your search query here...")
            search_type_input = gr.Radio(choices=["Title", "URL", "Keyword", "Content"], value="Title", label="Search By")
            search_button = gr.Button("Search")

        with gr.Row():
            items_output = gr.Dropdown(label="Select Item", choices=[], interactive=True)
            item_mapping = gr.State({})

        content_input = gr.Textbox(label="Edit Content", lines=10)
        prompt_input = gr.Textbox(label="Edit Prompt", lines=3)
        summary_input = gr.Textbox(label="Edit Summary", lines=5)

        # Adding keyword input box for editing
        keywords_input = gr.Textbox(label="Edit Keywords (comma-separated)", placeholder="Enter keywords here...")

        update_button = gr.Button("Update Media Content")
        status_message = gr.Textbox(label="Status", interactive=False)

        # Function to update the dropdown with search results
        search_button.click(
            fn=update_dropdown,
            inputs=[search_query_input, search_type_input],
            outputs=[items_output, item_mapping]
        )

        # Function to load selected media content including keywords
        def load_selected_media_content(selected_item, item_mapping):
            if selected_item and item_mapping and selected_item in item_mapping:
                media_id = item_mapping[selected_item]
                content, prompt, summary = fetch_item_details(media_id)

                # Fetch keywords for the selected item
                keywords = fetch_keywords_for_media(media_id)
                keywords_str = ", ".join(keywords) if keywords else ""

                return content, prompt, summary, keywords_str
            return "No item selected or invalid selection", "", "", ""

        # Load the selected media content and associated keywords
        items_output.change(
            fn=load_selected_media_content,
            inputs=[items_output, item_mapping],
            outputs=[content_input, prompt_input, summary_input, keywords_input]
        )

        # Function to update media content, prompt, summary, and keywords
        def update_media_with_keywords(selected_item, item_mapping, content, prompt, summary, keywords):
            if selected_item and item_mapping and selected_item in item_mapping:
                media_id = item_mapping[selected_item]

                # Split keywords into a list
                keyword_list = [kw.strip() for kw in keywords.split(",") if kw.strip()]

                # Update content, prompt, summary, and keywords in the database
                status = update_media_content(media_id, content, prompt, summary)
                keyword_status = update_keywords_for_media(media_id, keyword_list)

                return f"{status}\nKeywords: {keyword_status}"
            return "No item selected or invalid selection"

        # Update button click event
        update_button.click(
            fn=update_media_with_keywords,
            inputs=[items_output, item_mapping, content_input, prompt_input, summary_input, keywords_input],
            outputs=status_message
        )


def create_media_edit_and_clone_tab():
    with gr.TabItem("Clone and Edit Existing Items", visible=True):
        gr.Markdown("# Search, Edit, and Clone Existing Items")

        with gr.Row():
            with gr.Column():
                search_query_input = gr.Textbox(label="Search Query", placeholder="Enter your search query here...")
                search_type_input = gr.Radio(choices=["Title", "URL", "Keyword", "Content"], value="Title",
                                         label="Search By")
            with gr.Column():
                search_button = gr.Button("Search")
                clone_button = gr.Button("Clone Item")
            save_clone_button = gr.Button("Save Cloned Item", visible=False)
        with gr.Row():
            items_output = gr.Dropdown(label="Select Item", choices=[], interactive=True)
            item_mapping = gr.State({})

        content_input = gr.Textbox(label="Edit Content", lines=10)
        prompt_input = gr.Textbox(label="Edit Prompt", lines=3)
        summary_input = gr.Textbox(label="Edit Summary", lines=5)
        new_title_input = gr.Textbox(label="New Title (for cloning)", visible=False)
        status_message = gr.Textbox(label="Status", interactive=False)

        search_button.click(
            fn=update_dropdown,
            inputs=[search_query_input, search_type_input],
            outputs=[items_output, item_mapping]
        )

        def load_selected_media_content(selected_item, item_mapping):
            if selected_item and item_mapping and selected_item in item_mapping:
                media_id = item_mapping[selected_item]
                content, prompt, summary = fetch_item_details(media_id)
                return content, prompt, summary, gr.update(visible=True), gr.update(visible=False)
            return "No item selected or invalid selection", "", "", gr.update(visible=False), gr.update(visible=False)

        items_output.change(
            fn=load_selected_media_content,
            inputs=[items_output, item_mapping],
            outputs=[content_input, prompt_input, summary_input, clone_button, save_clone_button]
        )

        def prepare_for_cloning(selected_item):
            return gr.update(value=f"Copy of {selected_item}", visible=True), gr.update(visible=True)

        clone_button.click(
            fn=prepare_for_cloning,
            inputs=[items_output],
            outputs=[new_title_input, save_clone_button]
        )

        def save_cloned_item(selected_item, item_mapping, content, prompt, summary, new_title):
            if selected_item and item_mapping and selected_item in item_mapping:
                original_media_id = item_mapping[selected_item]
                try:
                    with db.get_connection() as conn:
                        cursor = conn.cursor()

                        # Fetch the original item's details
                        cursor.execute("SELECT type, url FROM Media WHERE id = ?", (original_media_id,))
                        original_type, original_url = cursor.fetchone()

                        # Generate a new unique URL
                        new_url = f"{original_url}_clone_{uuid.uuid4().hex[:8]}"

                        # Insert new item into Media table
                        cursor.execute("""
                            INSERT INTO Media (title, content, url, type)
                            VALUES (?, ?, ?, ?)
                        """, (new_title, content, new_url, original_type))

                        new_media_id = cursor.lastrowid

                        # Insert new item into MediaModifications table
                        cursor.execute("""
                            INSERT INTO MediaModifications (media_id, prompt, summary, modification_date)
                            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                        """, (new_media_id, prompt, summary))

                        # Copy keywords from the original item
                        cursor.execute("""
                            INSERT INTO MediaKeywords (media_id, keyword_id)
                            SELECT ?, keyword_id
                            FROM MediaKeywords
                            WHERE media_id = ?
                        """, (new_media_id, original_media_id))

                        # Update full-text search index
                        cursor.execute("""
                            INSERT INTO media_fts (rowid, title, content)
                            VALUES (?, ?, ?)
                        """, (new_media_id, new_title, content))

                        conn.commit()

                    return f"Cloned item saved successfully with ID: {new_media_id}", gr.update(
                        visible=False), gr.update(visible=False)
                except Exception as e:
                    logging.error(f"Error saving cloned item: {e}")
                    return f"Error saving cloned item: {str(e)}", gr.update(visible=True), gr.update(visible=True)
            else:
                return "No item selected or invalid selection", gr.update(visible=True), gr.update(visible=True)

        save_clone_button.click(
            fn=save_cloned_item,
            inputs=[items_output, item_mapping, content_input, prompt_input, summary_input, new_title_input],
            outputs=[status_message, new_title_input, save_clone_button]
        )


def create_prompt_edit_tab():
    with gr.TabItem("Add & Edit Prompts", visible=True):
        with gr.Row():
            with gr.Column():
                prompt_dropdown = gr.Dropdown(
                    label="Select Prompt",
                    choices=[],
                    interactive=True
                )
                prompt_list_button = gr.Button("List Prompts")

            with gr.Column():
                title_input = gr.Textbox(label="Title", placeholder="Enter the prompt title")
                author_input = gr.Textbox(label="Author", placeholder="Enter the prompt's author", lines=3)
                description_input = gr.Textbox(label="Description", placeholder="Enter the prompt description", lines=3)
                system_prompt_input = gr.Textbox(label="System Prompt", placeholder="Enter the system prompt", lines=3)
                user_prompt_input = gr.Textbox(label="User Prompt", placeholder="Enter the user prompt", lines=3)
                add_prompt_button = gr.Button("Add/Update Prompt")
                add_prompt_output = gr.HTML()

        # Event handlers
        prompt_list_button.click(
            fn=update_prompt_dropdown,
            outputs=prompt_dropdown
        )

        add_prompt_button.click(
            fn=add_or_update_prompt,
            inputs=[title_input, author_input, description_input, system_prompt_input, user_prompt_input],
            outputs=add_prompt_output
        )

        # Load prompt details when selected
        prompt_dropdown.change(
            fn=load_prompt_details,
            inputs=[prompt_dropdown],
            outputs=[title_input, author_input, system_prompt_input, user_prompt_input]
        )


def create_prompt_clone_tab():
    with gr.TabItem("Clone and Edit Prompts", visible=True):
        with gr.Row():
            with gr.Column():
                gr.Markdown("# Clone and Edit Prompts")
                prompt_dropdown = gr.Dropdown(
                    label="Select Prompt",
                    choices=[],
                    interactive=True
                )
                prompt_list_button = gr.Button("List Prompts")

            with gr.Column():
                title_input = gr.Textbox(label="Title", placeholder="Enter the prompt title")
                author_input = gr.Textbox(label="Author", placeholder="Enter the prompt's author", lines=3)
                description_input = gr.Textbox(label="Description", placeholder="Enter the prompt description", lines=3)
                system_prompt_input = gr.Textbox(label="System Prompt", placeholder="Enter the system prompt", lines=3)
                user_prompt_input = gr.Textbox(label="User Prompt", placeholder="Enter the user prompt", lines=3)
                clone_prompt_button = gr.Button("Clone Selected Prompt")
                save_cloned_prompt_button = gr.Button("Save Cloned Prompt", visible=False)
                add_prompt_output = gr.HTML()

        # Event handlers
        prompt_list_button.click(
            fn=update_prompt_dropdown,
            outputs=prompt_dropdown
        )

        # Load prompt details when selected
        prompt_dropdown.change(
            fn=load_prompt_details,
            inputs=[prompt_dropdown],
            outputs=[title_input, author_input, description_input, system_prompt_input, user_prompt_input]
        )

        def prepare_for_cloning(selected_prompt):
            if selected_prompt:
                return gr.update(value=f"Copy of {selected_prompt}"), gr.update(visible=True)
            return gr.update(), gr.update(visible=False)

        clone_prompt_button.click(
            fn=prepare_for_cloning,
            inputs=[prompt_dropdown],
            outputs=[title_input, save_cloned_prompt_button]
        )

        def save_cloned_prompt(title, description, system_prompt, user_prompt):
            try:
                result = add_prompt(title, description, system_prompt, user_prompt)
                if result == "Prompt added successfully.":
                    return result, gr.update(choices=update_prompt_dropdown())
                else:
                    return result, gr.update()
            except Exception as e:
                return f"Error saving cloned prompt: {str(e)}", gr.update()

        save_cloned_prompt_button.click(
            fn=save_cloned_prompt,
            inputs=[title_input, description_input, system_prompt_input, user_prompt_input],
            outputs=[add_prompt_output, prompt_dropdown]
        )