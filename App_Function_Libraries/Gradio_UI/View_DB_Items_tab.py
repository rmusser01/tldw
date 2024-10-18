# View_DB_Items_tab.py
# Description: This file contains the code for the search tab in the Gradio UI
#
# Imports
import html
#
# External Imports
import gradio as gr
#
# Local Imports
from App_Function_Libraries.DB.DB_Manager import view_database, get_all_document_versions, \
    fetch_paginated_data, fetch_item_details, get_latest_transcription, list_prompts, fetch_prompt_details, \
    load_preset_prompts
from App_Function_Libraries.DB.SQLite_DB import get_document_version
#
####################################################################################################
#
# Functions

def create_prompt_view_tab():
    with gr.TabItem("View Prompt Database", visible=True):
        gr.Markdown("# View Prompt Database Entries")
        with gr.Row():
            with gr.Column():
                entries_per_page = gr.Dropdown(choices=[10, 20, 50, 100], label="Entries per Page", value=10)
                page_number = gr.Number(value=1, label="Page Number", precision=0)
                view_button = gr.Button("View Page")
                next_page_button = gr.Button("Next Page")
                previous_page_button = gr.Button("Previous Page")
                pagination_info = gr.Textbox(label="Pagination Info", interactive=False)
                prompt_selector = gr.Dropdown(label="Select Prompt to View", choices=[])
            with gr.Column():
                results_table = gr.HTML()
                selected_prompt_display = gr.HTML()

        def view_database(page, entries_per_page):
            try:
                prompts, total_pages, current_page = list_prompts(page, entries_per_page)

                table_html = "<table style='width:100%; border-collapse: collapse;'>"
                table_html += "<tr><th style='border: 1px solid black; padding: 8px;'>Title</th><th style='border: 1px solid black; padding: 8px;'>Author</th></tr>"
                prompt_choices = []
                for prompt_name in prompts:
                    details = fetch_prompt_details(prompt_name)
                    if details:
                        title, _, _, _, _, _ = details
                        author = "Unknown"  # Assuming author is not stored in the current schema
                        table_html += f"<tr><td style='border: 1px solid black; padding: 8px;'>{html.escape(title)}</td><td style='border: 1px solid black; padding: 8px;'>{html.escape(author)}</td></tr>"
                        prompt_choices.append((title, title))  # Using title as both label and value
                table_html += "</table>"

                total_prompts = len(load_preset_prompts())  # This might be inefficient for large datasets
                pagination = f"Page {current_page} of {total_pages} (Total prompts: {total_prompts})"

                return table_html, pagination, total_pages, prompt_choices
            except Exception as e:
                return f"<p>Error fetching prompts: {e}</p>", "Error", 0, []

        def update_page(page, entries_per_page):
            results, pagination, total_pages, prompt_choices = view_database(page, entries_per_page)
            next_disabled = page >= total_pages
            prev_disabled = page <= 1
            return results, pagination, page, gr.update(interactive=not next_disabled), gr.update(
                interactive=not prev_disabled), gr.update(choices=prompt_choices)

        def go_to_next_page(current_page, entries_per_page):
            next_page = current_page + 1
            return update_page(next_page, entries_per_page)

        def go_to_previous_page(current_page, entries_per_page):
            previous_page = max(1, current_page - 1)
            return update_page(previous_page, entries_per_page)

        def display_selected_prompt(prompt_name):
            details = fetch_prompt_details(prompt_name)
            if details:
                title, author, description, system_prompt, user_prompt, keywords = details
                # Handle None values by converting them to empty strings
                description = description or ""
                system_prompt = system_prompt or ""
                user_prompt = user_prompt or ""
                author = author or "Unknown"
                keywords = keywords or ""

                html_content = f"""
                <div style="border: 1px solid #ddd; padding: 10px; margin-bottom: 20px;">
                    <h3>{html.escape(title)}</h3> <h4>by {html.escape(author)}</h4>
                    <p><strong>Description:</strong> {html.escape(description)}</p>
                    <div style="margin-top: 10px;">
                        <strong>System Prompt:</strong>
                        <pre style="white-space: pre-wrap; word-wrap: break-word;">{html.escape(system_prompt)}</pre>
                    </div>
                    <div style="margin-top: 10px;">
                        <strong>User Prompt:</strong>
                        <pre style="white-space: pre-wrap; word-wrap: break-word;">{html.escape(user_prompt)}</pre>
                    </div>
                    <p><strong>Keywords:</strong> {html.escape(keywords)}</p>
                </div>
                """
                return html_content
            else:
                return "<p>Prompt not found.</p>"

        view_button.click(
            fn=update_page,
            inputs=[page_number, entries_per_page],
            outputs=[results_table, pagination_info, page_number, next_page_button, previous_page_button,
                     prompt_selector]
        )

        next_page_button.click(
            fn=go_to_next_page,
            inputs=[page_number, entries_per_page],
            outputs=[results_table, pagination_info, page_number, next_page_button, previous_page_button,
                     prompt_selector]
        )

        previous_page_button.click(
            fn=go_to_previous_page,
            inputs=[page_number, entries_per_page],
            outputs=[results_table, pagination_info, page_number, next_page_button, previous_page_button,
                     prompt_selector]
        )

        prompt_selector.change(
            fn=display_selected_prompt,
            inputs=[prompt_selector],
            outputs=[selected_prompt_display]
        )

def format_as_html(content, title):
    escaped_content = html.escape(content)
    formatted_content = escaped_content.replace('\n', '<br>')
    return f"""
    <div style="border: 1px solid #ddd; padding: 10px; margin-bottom: 10px;">
        <h3>{title}</h3>
        <div style="max-height: 700px; overflow-y: auto;">
            {formatted_content}
        </div>
    </div>
    """

def extract_prompt_and_summary(content: str):
    # Implement this function based on how prompt and summary are stored in your DocumentVersions content
    # This is a placeholder implementation
    parts = content.split('\n\n', 2)
    prompt = parts[0] if len(parts) > 0 else "No prompt available."
    summary = parts[1] if len(parts) > 1 else "No summary available."
    return prompt, summary


def create_view_all_with_versions_tab():
    with gr.TabItem("View All Items", visible=True):
        gr.Markdown("# View All Database Entries with Version Selection")
        with gr.Row():
            with gr.Column(scale=1):
                entries_per_page = gr.Dropdown(choices=[10, 20, 50, 100], label="Entries per Page", value=10)
                page_number = gr.Number(value=1, label="Page Number", precision=0)
                view_button = gr.Button("View Page")
                next_page_button = gr.Button("Next Page")
                previous_page_button = gr.Button("Previous Page")
            with gr.Column(scale=2):
                items_output = gr.Dropdown(label="Select Item to View Details", choices=[])
                version_dropdown = gr.Dropdown(label="Select Version", choices=[], visible=False)
        with gr.Row():
            with gr.Column(scale=1):
                pagination_info = gr.Textbox(label="Pagination Info", interactive=False)
            with gr.Column(scale=2):
                prompt_output = gr.Textbox(label="Prompt Used", visible=True)
                summary_output = gr.HTML(label="Summary", visible=True)
                transcription_output = gr.HTML(label="Transcription", visible=True)

        item_mapping = gr.State({})

        def update_page(page, entries_per_page):
            results, total_entries = fetch_paginated_data(page, entries_per_page)
            total_pages = (total_entries + entries_per_page - 1) // entries_per_page
            pagination = f"Page {page} of {total_pages} (Total items: {total_entries})"

            choices = [f"{item[1]} (ID: {item[0]})" for item in results]
            new_item_mapping = {f"{item[1]} (ID: {item[0]})": item[0] for item in results}

            next_disabled = page >= total_pages
            prev_disabled = page <= 1

            return (gr.update(choices=choices, value=None),
                    pagination,
                    page,
                    gr.update(interactive=not next_disabled),
                    gr.update(interactive=not prev_disabled),
                    gr.update(visible=False, choices=[]),
                    "", "", "",
                    new_item_mapping)

        def format_as_html(content, title):
            if content is None:
                content = "No content available."
            escaped_content = html.escape(str(content))
            formatted_content = escaped_content.replace('\n', '<br>')
            return f"""
            <div style="border: 1px solid #ddd; padding: 10px; margin-bottom: 10px;">
                <h3>{title}</h3>
                <div style="max-height: 700px; overflow-y: auto;">
                    {formatted_content}
                </div>
            </div>
            """

        def display_item_details(selected_item, item_mapping):
            if selected_item and item_mapping and selected_item in item_mapping:
                media_id = item_mapping[selected_item]
                prompt, summary, transcription = fetch_item_details(media_id)
                versions = get_all_document_versions(media_id)

                # Filter out duplicate versions and sort them
                unique_versions = list(set((v['version_number'], v['created_at']) for v in versions))
                unique_versions.sort(key=lambda x: x[0], reverse=True)
                version_choices = [f"Version {v[0]} ({v[1]})" for v in unique_versions]

                summary_html = format_as_html(summary, "Summary")
                transcription_html = format_as_html(transcription, "Transcription")

                return (
                    gr.update(visible=True, choices=version_choices,
                              value=version_choices[0] if version_choices else None),
                    prompt if prompt is not None else "",
                    summary_html,
                    transcription_html
                )
            return gr.update(visible=False, choices=[]), "", "", ""

        def update_version_content(selected_item, item_mapping, selected_version):
            if selected_item and item_mapping and selected_item in item_mapping and selected_version:
                media_id = item_mapping[selected_item]
                version_number = int(selected_version.split()[1].split('(')[0])
                version_data = get_document_version(media_id, version_number)

                if 'error' not in version_data:
                    content = version_data['content']
                    prompt, summary = extract_prompt_and_summary(content)
                    transcription = get_latest_transcription(media_id)

                    summary_html = format_as_html(summary, "Summary")
                    transcription_html = format_as_html(transcription, "Transcription")

                    return prompt if prompt is not None else "", summary_html, transcription_html
            return gr.update(value=selected_item), gr.update(), gr.update()

        view_button.click(
            fn=update_page,
            inputs=[page_number, entries_per_page],
            outputs=[items_output, pagination_info, page_number, next_page_button, previous_page_button,
                     version_dropdown, prompt_output, summary_output, transcription_output, item_mapping]
        )

        next_page_button.click(
            fn=lambda page, entries: update_page(page + 1, entries),
            inputs=[page_number, entries_per_page],
            outputs=[items_output, pagination_info, page_number, next_page_button, previous_page_button,
                     version_dropdown, prompt_output, summary_output, transcription_output, item_mapping]
        )

        previous_page_button.click(
            fn=lambda page, entries: update_page(max(1, page - 1), entries),
            inputs=[page_number, entries_per_page],
            outputs=[items_output, pagination_info, page_number, next_page_button, previous_page_button,
                     version_dropdown, prompt_output, summary_output, transcription_output, item_mapping]
        )

        items_output.change(
            fn=display_item_details,
            inputs=[items_output, item_mapping],
            outputs=[version_dropdown, prompt_output, summary_output, transcription_output]
        )

        version_dropdown.change(
            fn=update_version_content,
            inputs=[items_output, item_mapping, version_dropdown],
            outputs=[prompt_output, summary_output, transcription_output]
        )


def create_viewing_tab():
    with gr.TabItem("View Database Entries", visible=True):
        gr.Markdown("# View Database Entries")
        with gr.Row():
            with gr.Column():
                entries_per_page = gr.Dropdown(choices=[10, 20, 50, 100], label="Entries per Page", value=10)
                page_number = gr.Number(value=1, label="Page Number", precision=0)
                view_button = gr.Button("View Page")
                next_page_button = gr.Button("Next Page")
                previous_page_button = gr.Button("Previous Page")
                pagination_info = gr.Textbox(label="Pagination Info", interactive=False)
            with gr.Column():
                results_display = gr.HTML()


        def update_page(page, entries_per_page):
            results, pagination, total_pages = view_database(page, entries_per_page)
            next_disabled = page >= total_pages
            prev_disabled = page <= 1
            return results, pagination, page, gr.update(interactive=not next_disabled), gr.update(interactive=not prev_disabled)

        def go_to_next_page(current_page, entries_per_page):
            next_page = current_page + 1
            return update_page(next_page, entries_per_page)

        def go_to_previous_page(current_page, entries_per_page):
            previous_page = max(1, current_page - 1)
            return update_page(previous_page, entries_per_page)

        view_button.click(
            fn=update_page,
            inputs=[page_number, entries_per_page],
            outputs=[results_display, pagination_info, page_number, next_page_button, previous_page_button]
        )

        next_page_button.click(
            fn=go_to_next_page,
            inputs=[page_number, entries_per_page],
            outputs=[results_display, pagination_info, page_number, next_page_button, previous_page_button]
        )

        previous_page_button.click(
            fn=go_to_previous_page,
            inputs=[page_number, entries_per_page],
            outputs=[results_display, pagination_info, page_number, next_page_button, previous_page_button]
        )

#
####################################################################################################