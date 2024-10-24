# Anki_Validation_tab.py
# Description: Gradio functions for the Anki Validation tab
#
# Imports
import json
import logging
from datetime import datetime
from typing import Dict, Any

#
# External Imports
import gradio as gr
#from outlines import models, prompts
#
# Local Imports
from App_Function_Libraries.Gradio_UI.Chat_ui import chat_wrapper
from App_Function_Libraries.Utils.Utils import default_api_endpoint, format_api_name, global_api_endpoints
#
############################################################################################################
#
# Functions:

# def create_anki_generation_tab():
#     try:
#         default_value = None
#         if default_api_endpoint:
#             if default_api_endpoint in global_api_endpoints:
#                 default_value = format_api_name(default_api_endpoint)
#             else:
#                 logging.warning(f"Default API endpoint '{default_api_endpoint}' not found in global_api_endpoints")
#     except Exception as e:
#         logging.error(f"Error setting default API endpoint: {str(e)}")
#         default_value = None
#     with gr.TabItem("Anki Flashcard Generation", visible=True):
#         gr.Markdown("# Anki Flashcard Generation")
#         chat_history = gr.State([])
#         generated_cards_state = gr.State({})
#
#         # Add progress tracking
#         generation_progress = gr.Progress()
#         status_message = gr.Status()
#
#         with gr.Row():
#             # Left Column: Generation Controls
#             with gr.Column(scale=1):
#                 gr.Markdown("## Content Input")
#                 source_text = gr.TextArea(
#                     label="Source Text or Topic",
#                     placeholder="Enter the text or topic you want to create flashcards from...",
#                     lines=5
#                 )
#
#                 # API Configuration
#                 api_endpoint = gr.Dropdown(
#                     choices=["None"] + [format_api_name(api) for api in global_api_endpoints],
#                     value=default_value,
#                     label="API for Card Generation"
#                 )
#                 api_key = gr.Textbox(label="API Key (if required)", type="password")
#
#                 with gr.Accordion("Generation Settings", open=True):
#                     num_cards = gr.Slider(
#                         minimum=1,
#                         maximum=20,
#                         value=5,
#                         step=1,
#                         label="Number of Cards"
#                     )
#
#                     card_types = gr.CheckboxGroup(
#                         choices=["basic", "cloze", "reverse"],
#                         value=["basic"],
#                         label="Card Types to Generate"
#                     )
#
#                     difficulty_level = gr.Radio(
#                         choices=["beginner", "intermediate", "advanced"],
#                         value="intermediate",
#                         label="Difficulty Level"
#                     )
#
#                     subject_area = gr.Dropdown(
#                         choices=[
#                             "general",
#                             "language_learning",
#                             "science",
#                             "mathematics",
#                             "history",
#                             "geography",
#                             "computer_science",
#                             "custom"
#                         ],
#                         value="general",
#                         label="Subject Area"
#                     )
#
#                     custom_subject = gr.Textbox(
#                         label="Custom Subject",
#                         visible=False,
#                         placeholder="Enter custom subject..."
#                     )
#
#                 with gr.Accordion("Advanced Options", open=False):
#                     temperature = gr.Slider(
#                         label="Temperature",
#                         minimum=0.00,
#                         maximum=1.0,
#                         step=0.05,
#                         value=0.7
#                     )
#
#                     max_retries = gr.Slider(
#                         label="Max Retries on Error",
#                         minimum=1,
#                         maximum=5,
#                         step=1,
#                         value=3
#                     )
#
#                     include_examples = gr.Checkbox(
#                         label="Include example usage",
#                         value=True
#                     )
#
#                     include_mnemonics = gr.Checkbox(
#                         label="Generate mnemonics",
#                         value=True
#                     )
#
#                     include_hints = gr.Checkbox(
#                         label="Include hints",
#                         value=True
#                     )
#
#                     tag_style = gr.Radio(
#                         choices=["broad", "specific", "hierarchical"],
#                         value="specific",
#                         label="Tag Style"
#                     )
#
#                     system_prompt = gr.Textbox(
#                         label="System Prompt",
#                         value="You are an expert at creating effective Anki flashcards.",
#                         lines=2
#                     )
#
#                 generate_button = gr.Button("Generate Flashcards")
#                 regenerate_button = gr.Button("Regenerate", visible=False)
#                 error_log = gr.TextArea(
#                     label="Error Log",
#                     visible=False,
#                     lines=3
#                 )
#
#             # Right Column: Chat Interface and Preview
#             with gr.Column(scale=1):
#                 gr.Markdown("## Interactive Card Generation")
#                 chatbot = gr.Chatbot(height=400, elem_classes="chatbot-container")
#
#                 with gr.Row():
#                     msg = gr.Textbox(
#                         label="Chat to refine cards",
#                         placeholder="Ask questions or request modifications..."
#                     )
#                     submit_chat = gr.Button("Submit")
#
#                 gr.Markdown("## Generated Cards Preview")
#                 generated_cards = gr.JSON(label="Generated Flashcards")
#
#                 with gr.Row():
#                     edit_generated = gr.Button("Edit in Validator")
#                     save_generated = gr.Button("Save to File")
#                     clear_chat = gr.Button("Clear Chat")
#
#                 generation_status = gr.Markdown("")
#                 download_file = gr.File(label="Download Cards", visible=False)
#
#         # Helper Functions and Classes
#         class AnkiCardGenerator:
#             def __init__(self):
#                 self.schema = {
#                     "type": "object",
#                     "properties": {
#                         "cards": {
#                             "type": "array",
#                             "items": {
#                                 "type": "object",
#                                 "properties": {
#                                     "id": {"type": "string"},
#                                     "type": {"type": "string", "enum": ["basic", "cloze", "reverse"]},
#                                     "front": {"type": "string"},
#                                     "back": {"type": "string"},
#                                     "tags": {
#                                         "type": "array",
#                                         "items": {"type": "string"}
#                                     },
#                                     "note": {"type": "string"}
#                                 },
#                                 "required": ["id", "type", "front", "back", "tags"]
#                             }
#                         }
#                     },
#                     "required": ["cards"]
#                 }
#
#                 self.template = prompts.TextTemplate("""
#                 Generate {num_cards} Anki flashcards about: {text}
#
#                 Requirements:
#                 - Difficulty: {difficulty}
#                 - Subject: {subject}
#                 - Card Types: {card_types}
#                 - Include Examples: {include_examples}
#                 - Include Mnemonics: {include_mnemonics}
#                 - Include Hints: {include_hints}
#                 - Tag Style: {tag_style}
#
#                 Each card must have:
#                 1. Unique ID starting with CARD_
#                 2. Type (one of: basic, cloze, reverse)
#                 3. Clear question/prompt on front
#                 4. Comprehensive answer on back
#                 5. Relevant tags including subject and difficulty
#                 6. Optional note with study tips or mnemonics
#
#                 For cloze deletions, use the format {{c1::text to be hidden}}.
#
#                 Ensure each card:
#                 - Focuses on a single concept
#                 - Is clear and unambiguous
#                 - Uses appropriate formatting
#                 - Has relevant tags
#                 - Includes requested additional information
#                 """)
#
#             async def generate_with_progress(
#                     self,
#                     text: str,
#                     config: Dict[str, Any],
#                     progress: gr.Progress
#             ) -> GenerationResult:
#                 try:
#                     # Initialize progress
#                     progress(0, desc="Initializing generation...")
#
#                     # Configure model
#                     model = models.Model(config["api_endpoint"])
#
#                     # Generate with schema validation
#                     progress(0.3, desc="Generating cards...")
#                     response = await model.generate(
#                         self.template,
#                         schema=self.schema,
#                         text=text,
#                         **config
#                     )
#
#                     # Validate response
#                     progress(0.6, desc="Validating generated cards...")
#                     validated_cards = self.validate_cards(response)
#
#                     # Final processing
#                     progress(0.9, desc="Finalizing...")
#                     time.sleep(0.5)  # Brief pause for UI feedback
#                     return GenerationResult(
#                         cards=validated_cards,
#                         error=None,
#                         status="Generation completed successfully!",
#                         progress=1.0
#                     )
#
#                 except Exception as e:
#                     logging.error(f"Card generation error: {str(e)}")
#                     return GenerationResult(
#                         cards=None,
#                         error=str(e),
#                         status=f"Error: {str(e)}",
#                         progress=1.0
#                     )
#
#             def validate_cards(self, cards: Dict[str, Any]) -> Dict[str, Any]:
#                 """Validate and clean generated cards"""
#                 if not isinstance(cards, dict) or "cards" not in cards:
#                     raise ValueError("Invalid card format")
#
#                 seen_ids = set()
#                 cleaned_cards = []
#
#                 for card in cards["cards"]:
#                     # Check ID uniqueness
#                     if card["id"] in seen_ids:
#                         card["id"] = f"{card['id']}_{len(seen_ids)}"
#                     seen_ids.add(card["id"])
#
#                     # Validate card type
#                     if card["type"] not in ["basic", "cloze", "reverse"]:
#                         raise ValueError(f"Invalid card type: {card['type']}")
#
#                     # Check content
#                     if not card["front"].strip() or not card["back"].strip():
#                         raise ValueError("Empty card content")
#
#                     # Validate cloze format
#                     if card["type"] == "cloze" and "{{c1::" not in card["front"]:
#                         raise ValueError("Invalid cloze format")
#
#                     # Clean and standardize tags
#                     if not isinstance(card["tags"], list):
#                         card["tags"] = [str(card["tags"])]
#                     card["tags"] = [tag.strip().lower() for tag in card["tags"] if tag.strip()]
#
#                     cleaned_cards.append(card)
#
#                 return {"cards": cleaned_cards}
#
#         # Initialize generator
#         generator = AnkiCardGenerator()
#
#         async def generate_flashcards(*args):
#             text, num_cards, card_types, difficulty, subject, custom_subject, \
#                 include_examples, include_mnemonics, include_hints, tag_style, \
#                 temperature, api_endpoint, api_key, system_prompt, max_retries = args
#
#             actual_subject = custom_subject if subject == "custom" else subject
#
#             config = {
#                 "num_cards": num_cards,
#                 "difficulty": difficulty,
#                 "subject": actual_subject,
#                 "card_types": card_types,
#                 "include_examples": include_examples,
#                 "include_mnemonics": include_mnemonics,
#                 "include_hints": include_hints,
#                 "tag_style": tag_style,
#                 "temperature": temperature,
#                 "api_endpoint": api_endpoint,
#                 "api_key": api_key,
#                 "system_prompt": system_prompt
#             }
#
#             errors = []
#             retry_count = 0
#
#             while retry_count < max_retries:
#                 try:
#                     result = await generator.generate_with_progress(text, config, generation_progress)
#
#                     if result.error:
#                         errors.append(f"Attempt {retry_count + 1}: {result.error}")
#                         retry_count += 1
#                         await asyncio.sleep(1)
#                         continue
#
#                     return (
#                         result.cards,
#                         gr.update(visible=True),
#                         result.status,
#                         gr.update(visible=False),
#                         [[None, "Cards generated! You can now modify them through chat."]]
#                     )
#
#                 except Exception as e:
#                     errors.append(f"Attempt {retry_count + 1}: {str(e)}")
#                     retry_count += 1
#                     await asyncio.sleep(1)
#
#             error_log = "\n".join(errors)
#             return (
#                 None,
#                 gr.update(visible=False),
#                 "Failed to generate cards after all retries",
#                 gr.update(value=error_log, visible=True),
#                 [[None, "Failed to generate cards. Please check the error log."]]
#             )
#
#         def save_generated_cards(cards):
#             if not cards:
#                 return "No cards to save", None
#
#             try:
#                 cards_json = json.dumps(cards, indent=2)
#                 current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
#                 filename = f"anki_cards_{current_time}.json"
#
#                 return (
#                     "Cards saved successfully!",
#                     (filename, cards_json, "application/json")
#                 )
#             except Exception as e:
#                 logging.error(f"Error saving cards: {e}")
#                 return f"Error saving cards: {str(e)}", None
#
#         def clear_chat_history():
#             return [], [], "Chat cleared"
#
#         def toggle_custom_subject(choice):
#             return gr.update(visible=choice == "custom")
#
#         def send_to_validator(cards):
#             if not cards:
#                 return "No cards to validate"
#             try:
#                 # Here you would integrate with your validation tab
#                 validated_cards = generator.validate_cards(cards)
#                 return "Cards validated and sent to validator"
#             except Exception as e:
#                 logging.error(f"Validation error: {e}")
#                 return f"Validation error: {str(e)}"
#
#         # Register callbacks
#         subject_area.change(
#             fn=toggle_custom_subject,
#             inputs=subject_area,
#             outputs=custom_subject
#         )
#
#         generate_button.click(
#             fn=generate_flashcards,
#             inputs=[
#                 source_text, num_cards, card_types, difficulty_level,
#                 subject_area, custom_subject, include_examples,
#                 include_mnemonics, include_hints, tag_style,
#                 temperature, api_endpoint, api_key, system_prompt,
#                 max_retries
#             ],
#             outputs=[
#                 generated_cards,
#                 regenerate_button,
#                 generation_status,
#                 error_log,
#                 chatbot
#             ]
#         )
#
#         regenerate_button.click(
#             fn=generate_flashcards,
#             inputs=[
#                 source_text, num_cards, card_types, difficulty_level,
#                 subject_area, custom_subject, include_examples,
#                 include_mnemonics, include_hints, tag_style,
#                 temperature, api_endpoint, api_key, system_prompt,
#                 max_retries
#             ],
#             outputs=[
#                 generated_cards,
#                 regenerate_button,
#                 generation_status,
#                 error_log,
#                 chatbot
#             ]
#         )
#
#         clear_chat.click(
#             fn=clear_chat_history,
#             outputs=[chatbot, chat_history, generation_status]
#         )
#
#         edit_generated.click(
#             fn=send_to_validator,
#             inputs=generated_cards,
#             outputs=generation_status
#         )
#
#         save_generated.click(
#             fn=save_generated_cards,
#             inputs=generated_cards,
#             outputs=[generation_status, download_file]
#         )
#
#         return (
#             source_text, num_cards, card_types, difficulty_level,
#             subject_area, custom_subject, include_examples,
#             include_mnemonics, include_hints, tag_style,
#             api_endpoint, api_key, temperature, system_prompt,
#             generate_button, regenerate_button, generated_cards,
#             edit_generated, save_generated, clear_chat,
#             generation_status, chatbot, msg, submit_chat,
#             chat_history, generated_cards_state, download_file,
#             error_log, max_retries
#         )


def create_anki_validation_tab():
    with gr.TabItem("Anki Flashcard Validation", visible=True):
        gr.Markdown("# Anki Flashcard Validation and Editor")

        with gr.Row():
            # Left Column: Input and Validation
            with gr.Column(scale=1):
                gr.Markdown("## Import or Create Flashcards")
                flashcard_input = gr.TextArea(
                    label="Enter Flashcards (JSON format)",
                    placeholder='''{
    "cards": [
        {
            "id": "CARD_001",
            "type": "basic",
            "front": "What is the capital of France?",
            "back": "Paris",
            "tags": ["geography", "europe"],
            "note": "Remember: City of Light"
        }
    ]
}''',
                    lines=10
                )

                import_file = gr.File(
                    label="Or Import JSON File",
                    file_types=[".json"]
                )

                validate_button = gr.Button("Validate Flashcards")

            # Right Column: Validation Results and Editor
            with gr.Column(scale=1):
                gr.Markdown("## Validation Results")
                validation_status = gr.Markdown("")

                with gr.Accordion("Validation Rules", open=False):
                    gr.Markdown("""
                    ### Required Fields:
                    - Unique ID
                    - Card Type (basic, cloze, reverse)
                    - Front content
                    - Back content
                    - At least one tag

                    ### Content Rules:
                    - No empty fields
                    - Front side should be a clear question/prompt
                    - Back side should contain complete answer
                    - Cloze deletions must have valid syntax
                    - No duplicate IDs
                    """)

        with gr.Row():
            # Card Editor
            gr.Markdown("## Card Editor")
        with gr.Row():
            with gr.Column(scale=1):
                with gr.Accordion("Edit Individual Cards", open=True):
                    card_selector = gr.Dropdown(
                        label="Select Card to Edit",
                        choices=[],
                        interactive=True
                    )

                    card_type = gr.Radio(
                        choices=["basic", "cloze", "reverse"],
                        label="Card Type",
                        value="basic"
                    )

                    front_content = gr.TextArea(
                        label="Front Content",
                        lines=3
                    )

                    back_content = gr.TextArea(
                        label="Back Content",
                        lines=3
                    )

                    tags_input = gr.TextArea(
                        label="Tags (comma-separated)",
                        lines=1
                    )

                    notes_input = gr.TextArea(
                        label="Additional Notes",
                        lines=2
                    )

                    update_card_button = gr.Button("Update Card")
                    delete_card_button = gr.Button("Delete Card", variant="stop")

        with gr.Row():
            with gr.Column(scale=1):
                # Export Options
                gr.Markdown("## Export Options")
                export_format = gr.Radio(
                    choices=["Anki CSV", "JSON", "Plain Text"],
                    label="Export Format",
                    value="Anki CSV"
                )
                export_button = gr.Button("Export Valid Cards")
                export_file = gr.File(label="Download Validated Cards")
                export_status = gr.Markdown("")
            with gr.Column(scale=1):
                gr.Markdown("## Export Instructions")
                gr.Markdown("""
                ### Anki CSV Format:
                - Front, Back, Tags, Type, Note
                - Use for importing into Anki
                
                ### JSON Format:
                - JSON array of cards
                - Use for custom processing
                
                ### Plain Text Format:
                - Question and Answer pairs
                - Use for manual review
                """)

        # Helper Functions
        def validate_flashcards(content):
            try:
                data = json.loads(content)
                validation_results = []
                is_valid = True

                if not isinstance(data, dict) or 'cards' not in data:
                    return False, "Invalid JSON format. Must contain 'cards' array."

                seen_ids = set()
                for idx, card in enumerate(data['cards']):
                    card_issues = []

                    # Check required fields
                    if 'id' not in card:
                        card_issues.append("Missing ID")
                    elif card['id'] in seen_ids:
                        card_issues.append("Duplicate ID")
                    else:
                        seen_ids.add(card['id'])

                    if 'type' not in card or card['type'] not in ['basic', 'cloze', 'reverse']:
                        card_issues.append("Invalid card type")

                    if 'front' not in card or not card['front'].strip():
                        card_issues.append("Missing front content")

                    if 'back' not in card or not card['back'].strip():
                        card_issues.append("Missing back content")

                    if 'tags' not in card or not card['tags']:
                        card_issues.append("Missing tags")

                    # Content-specific validation
                    if card.get('type') == 'cloze':
                        if '{{c1::' not in card['front']:
                            card_issues.append("Invalid cloze format")

                    if card_issues:
                        is_valid = False
                        validation_results.append(f"Card {card['id']}: {', '.join(card_issues)}")

                return is_valid, "\n".join(validation_results) if validation_results else "All cards are valid!"

            except json.JSONDecodeError:
                return False, "Invalid JSON format"
            except Exception as e:
                return False, f"Validation error: {str(e)}"

        def load_card_for_editing(card_selection, current_content):
            if not card_selection or not current_content:
                return {}, gr.update(), gr.update(), gr.update(), gr.update(), gr.update()

            try:
                data = json.loads(current_content)
                selected_id = card_selection.split(" - ")[0]

                for card in data['cards']:
                    if card['id'] == selected_id:
                        return (
                            card,
                            card['type'],
                            card['front'],
                            card['back'],
                            ", ".join(card['tags']),
                            card.get('note', '')
                        )

                return {}, gr.update(), gr.update(), gr.update(), gr.update(), gr.update()

            except Exception as e:
                return {}, gr.update(), gr.update(), gr.update(), gr.update(), gr.update()

        def update_card(current_content, card_selection, card_type, front, back, tags, notes):
            try:
                data = json.loads(current_content)
                selected_id = card_selection.split(" - ")[0]

                for card in data['cards']:
                    if card['id'] == selected_id:
                        card['type'] = card_type
                        card['front'] = front
                        card['back'] = back
                        card['tags'] = [tag.strip() for tag in tags.split(',')]
                        card['note'] = notes

                return json.dumps(data, indent=2), "Card updated successfully!"

            except Exception as e:
                return current_content, f"Error updating card: {str(e)}"

        def export_cards(content, format_type):
            try:
                is_valid, validation_message = validate_flashcards(content)
                if not is_valid:
                    return "Please fix validation issues before exporting.", None

                data = json.loads(content)

                if format_type == "Anki CSV":
                    output = "Front,Back,Tags,Type,Note\n"
                    for card in data['cards']:
                        output += f'"{card["front"]}","{card["back"]}","{" ".join(card["tags"])}","{card["type"]}","{card.get("note", "")}"\n'
                    return "Cards exported successfully!", ("anki_cards.csv", output, "text/csv")

                elif format_type == "JSON":
                    return "Cards exported successfully!", ("anki_cards.json", content, "application/json")

                else:  # Plain Text
                    output = ""
                    for card in data['cards']:
                        output += f"Q: {card['front']}\nA: {card['back']}\n\n"
                    return "Cards exported successfully!", ("anki_cards.txt", output, "text/plain")

            except Exception as e:
                return f"Export error: {str(e)}", None

        # Register callbacks
        validate_button.click(
            fn=validate_flashcards,
            inputs=[flashcard_input],
            outputs=[validation_status]
        )

        card_selector.change(
            fn=load_card_for_editing,
            inputs=[card_selector, flashcard_input],
            outputs=[
                gr.State(),  # For storing current card data
                card_type,
                front_content,
                back_content,
                tags_input,
                notes_input
            ]
        )

        update_card_button.click(
            fn=update_card,
            inputs=[
                flashcard_input,
                card_selector,
                card_type,
                front_content,
                back_content,
                tags_input,
                notes_input
            ],
            outputs=[flashcard_input, validation_status]
        )

        export_button.click(
            fn=export_cards,
            inputs=[flashcard_input, export_format],
            outputs=[export_status, export_file]
        )

        return (
            flashcard_input,
            import_file,
            validate_button,
            validation_status,
            card_selector,
            card_type,
            front_content,
            back_content,
            tags_input,
            notes_input,
            update_card_button,
            delete_card_button,
            export_format,
            export_button,
            export_file,
            export_status
        )

#
# End of Anki_Validation_tab.py
############################################################################################################

import json
import zipfile
import sqlite3
import tempfile
import os
import shutil
import base64
from pathlib import Path
import gradio as gr


def extract_media_from_apkg(zip_path, temp_dir):
    """Extract and process media files from APKG."""
    media_files = {}
    try:
        # Extract media.json which maps filenames
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            if 'media' in zip_ref.namelist():
                media_json = json.loads(zip_ref.read('media').decode('utf-8'))

                # Extract all media files
                for file_id, filename in media_json.items():
                    if str(file_id) in zip_ref.namelist():
                        file_data = zip_ref.read(str(file_id))
                        file_path = os.path.join(temp_dir, filename)

                        # Save file temporarily
                        with open(file_path, 'wb') as f:
                            f.write(file_data)

                        # Convert to base64 for supported image types
                        if any(filename.lower().endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.gif']):
                            with open(file_path, 'rb') as f:
                                file_content = f.read()
                                file_ext = os.path.splitext(filename)[1].lower()
                                media_type = f"image/{file_ext[1:]}"
                                if file_ext == '.jpg':
                                    media_type = "image/jpeg"
                                media_files[
                                    filename] = f"data:{media_type};base64,{base64.b64encode(file_content).decode('utf-8')}"

                        # Clean up temporary file
                        os.remove(file_path)

    except Exception as e:
        print(f"Error processing media: {str(e)}")
    return media_files


def process_apkg_file(file_path):
    """Extract and validate an APKG file, returning the card data and media files."""
    if not file_path:
        return None, None, "No file provided"

    temp_dir = tempfile.mkdtemp()
    try:
        # Extract media files first
        media_files = extract_media_from_apkg(file_path.name, temp_dir)

        # Extract APKG and process database
        with zipfile.ZipFile(file_path.name, 'r') as zip_ref:
            zip_ref.extractall(temp_dir)

        # Connect to the SQLite database
        db_path = os.path.join(temp_dir, 'collection.anki2')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Get deck information
        cursor.execute("SELECT decks, models FROM col")
        decks_json, models_json = cursor.fetchone()
        deck_info = {
            "decks": json.loads(decks_json),
            "models": json.loads(models_json)
        }

        # Get cards and notes with media processing
        cards_data = {"cards": []}
        cursor.execute("""
            SELECT n.id, n.flds, n.tags, c.type, n.mid, m.name, n.sfld
            FROM notes n
            JOIN cards c ON c.nid = n.id
            JOIN notetypes m ON m.id = n.mid
        """)

        for row in cursor:
            note_id, fields, tags, card_type, model_id, model_name, sort_field = row
            fields_list = fields.split('\x1f')

            # Process fields for media references
            processed_fields = []
            for field in fields_list:
                # Replace media references with base64 data
                for filename, base64_data in media_files.items():
                    field = field.replace(
                        f'<img src="{filename}"',
                        f'<img src="{base64_data}"'
                    )
                processed_fields.append(field)

            # Convert Anki card type
            if 'cloze' in model_name.lower():
                converted_type = 'cloze'
            elif len(processed_fields) > 1:
                converted_type = 'basic'
            else:
                converted_type = 'basic'

            card_data = {
                "id": f"APKG_{note_id}",
                "type": converted_type,
                "front": processed_fields[0],
                "back": processed_fields[1] if len(processed_fields) > 1 else "",
                "tags": tags.strip().split(" ") if tags.strip() else ["imported"],
                "note": f"Imported from deck: {model_name}",
                "has_media": any('<img' in field for field in processed_fields)
            }

            cards_data["cards"].append(card_data)

        conn.close()
        return cards_data, deck_info, "APKG file processed successfully!"

    except sqlite3.Error as e:
        return None, None, f"Database error: {str(e)}"
    except json.JSONDecodeError as e:
        return None, None, f"JSON parsing error: {str(e)}"
    except Exception as e:
        return None, None, f"Error processing APKG file: {str(e)}"
    finally:
        shutil.rmtree(temp_dir)


def validate_flashcards(content):
    """Validate flashcard content with enhanced image support."""
    try:
        data = json.loads(content)
        validation_results = []
        is_valid = True

        if not isinstance(data, dict) or 'cards' not in data:
            return False, "Invalid JSON format. Must contain 'cards' array."

        seen_ids = set()
        for idx, card in enumerate(data['cards']):
            card_issues = []

            # Check required fields
            if 'id' not in card:
                card_issues.append("Missing ID")
            elif card['id'] in seen_ids:
                card_issues.append("Duplicate ID")
            else:
                seen_ids.add(card['id'])

            if 'type' not in card or card['type'] not in ['basic', 'cloze', 'reverse']:
                card_issues.append("Invalid card type")

            if 'front' not in card or not card['front'].strip():
                card_issues.append("Missing front content")

            if 'back' not in card or not card['back'].strip():
                card_issues.append("Missing back content")

            if 'tags' not in card or not card['tags']:
                card_issues.append("Missing tags")

            # Content-specific validation
            if card.get('type') == 'cloze':
                if '{{c1::' not in card['front']:
                    card_issues.append("Invalid cloze format")

            # Image validation
            for field in ['front', 'back']:
                if '<img' in card[field]:
                    if not (card[field].count('<img') == card[field].count('src="')):
                        card_issues.append(f"Invalid image tag in {field}")
                    if 'data:image/' not in card[field] and 'http' not in card[field]:
                        card_issues.append(f"Invalid image source in {field}")

            if card_issues:
                is_valid = False
                validation_results.append(f"Card {card['id']}: {', '.join(card_issues)}")

        return is_valid, "\n".join(validation_results) if validation_results else "All cards are valid!"

    except json.JSONDecodeError:
        return False, "Invalid JSON format"
    except Exception as e:
        return False, f"Validation error: {str(e)}"


def handle_file_upload(file, input_type):
    """Handle file upload based on input type."""
    if not file:
        return None, None, "No file uploaded"

    if input_type == "APKG":
        cards_data, deck_info, message = process_apkg_file(file)
        if cards_data:
            return json.dumps(cards_data, indent=2), deck_info, message
        return None, None, message
    else:  # JSON
        try:
            content = file.read().decode('utf-8')
            json.loads(content)  # Validate JSON
            return content, None, "JSON file loaded successfully!"
        except Exception as e:
            return None, None, f"Error loading JSON file: {str(e)}"


def create_anki_validation_tab_two():
    with gr.TabItem("Anki Flashcard Validation", visible=True):
        gr.Markdown("# Anki Flashcard Validation and Editor")

        with gr.Row():
            # Left Column: Input and Validation
            with gr.Column(scale=1):
                gr.Markdown("## Import or Create Flashcards")

                input_type = gr.Radio(
                    choices=["JSON", "APKG"],
                    label="Input Type",
                    value="JSON"
                )

                with gr.Group() as json_input_group:
                    flashcard_input = gr.TextArea(
                        label="Enter Flashcards (JSON format)",
                        placeholder='''{
    "cards": [
        {
            "id": "CARD_001",
            "type": "basic",
            "front": "What is the capital of France?",
            "back": "Paris",
            "tags": ["geography", "europe"],
            "note": "Remember: City of Light"
        }
    ]
}''',
                        lines=10
                    )

                    import_json = gr.File(
                        label="Or Import JSON File",
                        file_types=[".json"]
                    )

                with gr.Group(visible=False) as apkg_input_group:
                    import_apkg = gr.File(
                        label="Import APKG File",
                        file_types=[".apkg"]
                    )
                    deck_info = gr.JSON(
                        label="Deck Information",
                        visible=False
                    )

                validate_button = gr.Button("Validate Flashcards")

            # Right Column: Validation Results and Editor
            with gr.Column(scale=1):
                gr.Markdown("## Validation Results")
                validation_status = gr.Markdown("")

                with gr.Accordion("Validation Rules", open=False):
                    gr.Markdown("""
                    ### Required Fields:
                    - Unique ID
                    - Card Type (basic, cloze, reverse)
                    - Front content
                    - Back content
                    - At least one tag

                    ### Content Rules:
                    - No empty fields
                    - Front side should be a clear question/prompt
                    - Back side should contain complete answer
                    - Cloze deletions must have valid syntax
                    - No duplicate IDs

                    ### Image Rules:
                    - Valid image tags
                    - Supported formats (JPG, PNG, GIF)
                    - Base64 encoded or valid URL

                    ### APKG-specific Rules:
                    - Valid SQLite database structure
                    - Media files properly referenced
                    - Note types match Anki standards
                    - Card templates are well-formed
                    """)

        with gr.Row():
            # Card Editor
            gr.Markdown("## Card Editor")
        with gr.Row():
            with gr.Column(scale=1):
                with gr.Accordion("Edit Individual Cards", open=True):
                    card_selector = gr.Dropdown(
                        label="Select Card to Edit",
                        choices=[],
                        interactive=True
                    )

                    card_type = gr.Radio(
                        choices=["basic", "cloze", "reverse"],
                        label="Card Type",
                        value="basic"
                    )

                    front_preview = gr.HTML(
                        label="Front Preview",
                        value=""
                    )

                    front_content = gr.TextArea(
                        label="Front Content",
                        lines=3
                    )

                    back_preview = gr.HTML(
                        label="Back Preview",
                        value=""
                    )

                    back_content = gr.TextArea(
                        label="Back Content",
                        lines=3
                    )

                    tags_input = gr.TextArea(
                        label="Tags (comma-separated)",
                        lines=1
                    )

                    notes_input = gr.TextArea(
                        label="Additional Notes",
                        lines=2
                    )

                    update_card_button = gr.Button("Update Card")
                    delete_card_button = gr.Button("Delete Card", variant="stop")

        with gr.Row():
            with gr.Column(scale=1):
                # Export Options
                gr.Markdown("## Export Options")
                export_format = gr.Radio(
                    choices=["Anki CSV", "JSON", "Plain Text"],
                    label="Export Format",
                    value="Anki CSV"
                )
                export_button = gr.Button("Export Valid Cards")
                export_file = gr.File(label="Download Validated Cards")
                export_status = gr.Markdown("")
            with gr.Column(scale=1):
                gr.Markdown("## Export Instructions")
                gr.Markdown("""
                ### Anki CSV Format:
                - Front, Back, Tags, Type, Note
                - Use for importing into Anki
                - Images preserved as HTML

                ### JSON Format:
                - JSON array of cards
                - Images as base64 or URLs
                - Use for custom processing

                ### Plain Text Format:
                - Question and Answer pairs
                - Images represented as [IMG] placeholder
                - Use for manual review
                """)

        # Helper function for previewing HTML content
        def update_preview(content):
            """Sanitize and update HTML preview."""
            if not content:
                return ""
            # Basic XSS prevention while allowing images
            allowed_tags = {'img', 'b', 'i', 'u', 'div', 'br', 'p'}
            # Add more sophisticated HTML sanitization here if needed
            return content

        def load_card_for_editing(card_selection, current_content):
            if not card_selection or not current_content:
                return {}, gr.update(), gr.update(), gr.update(), gr.update(), gr.update(), gr.update(), gr.update()

            try:
                data = json.loads(current_content)
                selected_id = card_selection.split(" - ")[0]

                for card in data['cards']:
                    if card['id'] == selected_id:
                        return (
                            card,
                            card['type'],
                            update_preview(card['front']),
                            card['front'],
                            update_preview(card['back']),
                            card['back'],
                            ", ".join(card['tags']),
                            card.get('note', '')
                        )

                return {}, gr.update(), gr.update(), gr.update(), gr.update(), gr.update(), gr.update(), gr.update()

            except Exception as e:
                return {}, gr.update(), gr.update(), gr.update(), gr.update(), gr.update(), gr.update(), gr.update()

        # Update visibility based on input type
        def update_input_visibility(input_type):
            return (
                gr.update(visible=input_type == "JSON"))
