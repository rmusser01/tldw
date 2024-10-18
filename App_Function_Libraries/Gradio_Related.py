# Gradio_Related.py
#########################################
# Gradio UI Functions Library
# I fucking hate Gradio.
#
#########################################
#
# Built-In Imports
import logging
import os
import webbrowser

#
# Import 3rd-Party Libraries
import gradio as gr
#
# Local Imports
from App_Function_Libraries.DB.DB_Manager import get_db_config
from App_Function_Libraries.Gradio_UI.Arxiv_tab import create_arxiv_tab
from App_Function_Libraries.Gradio_UI.Audio_ingestion_tab import create_audio_processing_tab
from App_Function_Libraries.Gradio_UI.Book_Ingestion_tab import create_import_book_tab
from App_Function_Libraries.Gradio_UI.Character_Chat_tab import create_character_card_interaction_tab, create_character_chat_mgmt_tab, create_custom_character_card_tab, \
    create_character_card_validation_tab, create_export_characters_tab
from App_Function_Libraries.Gradio_UI.Character_interaction_tab import create_narrator_controlled_conversation_tab, \
    create_multiple_character_chat_tab
from App_Function_Libraries.Gradio_UI.Chat_ui import create_chat_management_tab, \
    create_chat_interface_four, create_chat_interface_multi_api, create_chat_interface_stacked, create_chat_interface
from App_Function_Libraries.Gradio_UI.Config_tab import create_config_editor_tab
from App_Function_Libraries.Gradio_UI.Explain_summarize_tab import create_summarize_explain_tab
from App_Function_Libraries.Gradio_UI.Export_Functionality import create_export_tab
from App_Function_Libraries.Gradio_UI.Backup_Functionality import create_backup_tab, create_view_backups_tab, \
    create_restore_backup_tab
from App_Function_Libraries.Gradio_UI.Import_Functionality import create_import_single_prompt_tab, \
    create_import_obsidian_vault_tab, create_import_item_tab, create_import_multiple_prompts_tab
from App_Function_Libraries.Gradio_UI.Introduction_tab import create_introduction_tab
from App_Function_Libraries.Gradio_UI.Keywords import create_view_keywords_tab, create_add_keyword_tab, \
    create_delete_keyword_tab, create_export_keywords_tab
from App_Function_Libraries.Gradio_UI.Live_Recording import create_live_recording_tab
from App_Function_Libraries.Gradio_UI.Llamafile_tab import create_chat_with_llamafile_tab
#from App_Function_Libraries.Gradio_UI.MMLU_Pro_tab import create_mmlu_pro_tab
from App_Function_Libraries.Gradio_UI.Media_edit import create_prompt_clone_tab, create_prompt_edit_tab, \
    create_media_edit_and_clone_tab, create_media_edit_tab
from App_Function_Libraries.Gradio_UI.Media_wiki_tab import create_mediawiki_import_tab, create_mediawiki_config_tab
from App_Function_Libraries.Gradio_UI.PDF_ingestion_tab import create_pdf_ingestion_tab, create_pdf_ingestion_test_tab
from App_Function_Libraries.Gradio_UI.Plaintext_tab_import import create_plain_text_import_tab
from App_Function_Libraries.Gradio_UI.Podcast_tab import create_podcast_tab
from App_Function_Libraries.Gradio_UI.Prompt_Suggestion_tab import create_prompt_suggestion_tab
from App_Function_Libraries.Gradio_UI.RAG_QA_Chat_tab import create_rag_qa_chat_tab
from App_Function_Libraries.Gradio_UI.Re_summarize_tab import create_resummary_tab
from App_Function_Libraries.Gradio_UI.Search_Tab import create_prompt_search_tab, \
    create_search_summaries_tab, create_search_tab
from App_Function_Libraries.Gradio_UI.RAG_Chat_tab import create_rag_tab
from App_Function_Libraries.Gradio_UI.Embeddings_tab import create_embeddings_tab, create_view_embeddings_tab, \
    create_purge_embeddings_tab
from App_Function_Libraries.Gradio_UI.Trash import create_view_trash_tab, create_empty_trash_tab, \
    create_delete_trash_tab, create_search_and_mark_trash_tab
from App_Function_Libraries.Gradio_UI.Utilities import create_utilities_yt_timestamp_tab, create_utilities_yt_audio_tab, \
    create_utilities_yt_video_tab
from App_Function_Libraries.Gradio_UI.Video_transcription_tab import create_video_transcription_tab
from App_Function_Libraries.Gradio_UI.View_tab import create_manage_items_tab
from App_Function_Libraries.Gradio_UI.Website_scraping_tab import create_website_scraping_tab
from App_Function_Libraries.Gradio_UI.Chat_Workflows import chat_workflows_tab
from App_Function_Libraries.Gradio_UI.View_DB_Items_tab import create_prompt_view_tab, \
    create_view_all_with_versions_tab, create_viewing_tab
#
# Gradio UI Imports
from App_Function_Libraries.Gradio_UI.Evaluations_Benchmarks_tab import create_geval_tab, create_infinite_bench_tab
#from App_Function_Libraries.Local_LLM.Local_LLM_huggingface import create_huggingface_tab
from App_Function_Libraries.Local_LLM.Local_LLM_ollama import create_ollama_tab
from App_Function_Libraries.Gradio_UI.RAG_QA_Chat_Notes import create_rag_qa_chat_notes_tab

#
#######################################################################################################################
# Function Definitions
#


# Disable Gradio Analytics
os.environ['GRADIO_ANALYTICS_ENABLED'] = 'False'


custom_prompt_input = None
server_mode = False
share_public = False
custom_prompt_summarize_bulleted_notes = ("""
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
                    """)
#
# End of globals
#######################################################################################################################
#
# Start of Video/Audio Transcription and Summarization Functions
#
# Functions:
# FIXME
#
#
################################################################################################################
# Functions for Re-Summarization
#
# Functions:
# FIXME
# End of Re-Summarization Functions
#
############################################################################################################################################################################################################################
#
# Explain/Summarize This Tab
#
# Functions:
# FIXME
#
#
############################################################################################################################################################################################################################
#
# Transcript Comparison Tab
#
# Functions:
# FIXME
#
#
###########################################################################################################################################################################################################################
#
# Search Tab
#
# Functions:
# FIXME
#
# End of Search Tab Functions
#
##############################################################################################################################################################################################################################
#
# Llamafile Tab
#
# Functions:
# FIXME
#
# End of Llamafile Tab Functions
##############################################################################################################################################################################################################################
#
# Chat Interface Tab Functions
#
# Functions:
# FIXME
#
#
# End of Chat Interface Tab Functions
################################################################################################################################################################################################################################
#
# Media Edit Tab Functions
# Functions:
# Fixme
# create_media_edit_tab():
##### Trash Tab
# FIXME
# Functions:
#
# End of Media Edit Tab Functions
################################################################################################################
#
# Import Items Tab Functions
#
# Functions:
#FIXME
# End of Import Items Tab Functions
################################################################################################################
#
# Export Items Tab Functions
#
# Functions:
# FIXME
#
#
# End of Export Items Tab Functions
################################################################################################################
#
# Keyword Management Tab Functions
#
# Functions:
#  create_view_keywords_tab():
# FIXME
#
# End of Keyword Management Tab Functions
################################################################################################################
#
# Document Editing Tab Functions
#
# Functions:
#   #FIXME
#
#
################################################################################################################
#
# Utilities Tab Functions
# Functions:
#   create_utilities_yt_video_tab():
# #FIXME

#
# End of Utilities Tab Functions
################################################################################################################

# FIXME - Prompt sample box
#
# # Sample data
# prompts_category_1 = [
#     "What are the key points discussed in the video?",
#     "Summarize the main arguments made by the speaker.",
#     "Describe the conclusions of the study presented."
# ]
#
# prompts_category_2 = [
#     "How does the proposed solution address the problem?",
#     "What are the implications of the findings?",
#     "Can you explain the theory behind the observed phenomenon?"
# ]
#
# all_prompts2 = prompts_category_1 + prompts_category_2


def launch_ui(share_public=None, server_mode=False):
    webbrowser.open_new_tab('http://127.0.0.1:7860/?__theme=dark')
    share=share_public
    css = """
    .result-box {
        margin-bottom: 20px;
        border: 1px solid #ddd;
        padding: 10px;
    }
    .result-box.error {
        border-color: #ff0000;
        background-color: #ffeeee;
    }
    .transcription, .summary {
        max-height: 800px;
        overflow-y: auto;
        border: 1px solid #eee;
        padding: 10px;
        margin-top: 10px;
    }
    """

    with gr.Blocks(theme='bethecloud/storj_theme',css=css) as iface:
        gr.HTML(
            """
            <script>
            document.addEventListener('DOMContentLoaded', (event) => {
                document.body.classList.add('dark');
                document.querySelector('gradio-app').style.backgroundColor = 'var(--color-background-primary)';
            });
            </script>
            """
        )
        db_config = get_db_config()
        db_type = db_config['type']
        gr.Markdown(f"# tl/dw: Your LLM-powered Research Multi-tool")
        gr.Markdown(f"(Using {db_type.capitalize()} Database)")
        with gr.Tabs():
            with gr.TabItem("Transcription / Summarization / Ingestion", id="ingestion-grouping", visible=True):
                with gr.Tabs():
                    create_video_transcription_tab()
                    create_audio_processing_tab()
                    create_podcast_tab()
                    create_import_book_tab()
                    create_plain_text_import_tab()
                    create_website_scraping_tab()
                    create_pdf_ingestion_tab()
                    create_pdf_ingestion_test_tab()
                    create_resummary_tab()
                    create_summarize_explain_tab()
                    create_live_recording_tab()
                    create_arxiv_tab()

            with gr.TabItem("Text Search", id="text search", visible=True):
                create_search_tab()
                create_search_summaries_tab()

            with gr.TabItem("RAG Chat+Notes", id="RAG Chat Notes group", visible=True):
                create_rag_qa_chat_notes_tab()

            with gr.TabItem("RAG Search", id="RAG Search group", visible=True):
                create_rag_tab()
                create_rag_qa_chat_tab()

            with gr.TabItem("Chat with an LLM", id="LLM Chat group", visible=True):
                create_chat_interface()
                create_chat_interface_stacked()
                create_chat_interface_multi_api()
                create_chat_interface_four()
                create_chat_with_llamafile_tab()
                create_chat_management_tab()
                chat_workflows_tab()


            with gr.TabItem("Character Chat", id="character chat group", visible=True):
                create_character_card_interaction_tab()
                create_character_chat_mgmt_tab()
                create_custom_character_card_tab()
                create_character_card_validation_tab()
                create_multiple_character_chat_tab()
                create_narrator_controlled_conversation_tab()
                create_export_characters_tab()


            with gr.TabItem("View DB Items", id="view db items group", visible=True):
                # This one works
                create_view_all_with_versions_tab()
                # This one is WIP
                create_viewing_tab()
                create_prompt_view_tab()


            with gr.TabItem("Prompts", id='view prompts group', visible=True):
                create_prompt_view_tab()
                create_prompt_search_tab()
                create_prompt_edit_tab()
                create_prompt_clone_tab()
                create_prompt_suggestion_tab()


            with gr.TabItem("Manage / Edit Existing Items", id="manage group", visible=True):
                create_media_edit_tab()
                create_manage_items_tab()
                create_media_edit_and_clone_tab()
                # FIXME
                #create_compare_transcripts_tab()


            with gr.TabItem("Embeddings Management", id="embeddings group", visible=True):
                create_embeddings_tab()
                create_view_embeddings_tab()
                create_purge_embeddings_tab()

            with gr.TabItem("Writing Tools", id="writing_tools group", visible=True):
                from App_Function_Libraries.Gradio_UI.Writing_tab import create_document_feedback_tab
                create_document_feedback_tab()
                from App_Function_Libraries.Gradio_UI.Writing_tab import create_grammar_style_check_tab
                create_grammar_style_check_tab()
                from App_Function_Libraries.Gradio_UI.Writing_tab import create_tone_adjustment_tab
                create_tone_adjustment_tab()
                from App_Function_Libraries.Gradio_UI.Writing_tab import create_creative_writing_tab
                create_creative_writing_tab()
                from App_Function_Libraries.Gradio_UI.Writing_tab import create_mikupad_tab
                create_mikupad_tab()


            with gr.TabItem("Keywords", id="keywords group", visible=True):
                create_view_keywords_tab()
                create_add_keyword_tab()
                create_delete_keyword_tab()
                create_export_keywords_tab()

            with gr.TabItem("Import", id="import group", visible=True):
                create_import_item_tab()
                create_import_obsidian_vault_tab()
                create_import_single_prompt_tab()
                create_import_multiple_prompts_tab()
                create_mediawiki_import_tab()
                create_mediawiki_config_tab()

            with gr.TabItem("Export", id="export group", visible=True):
                create_export_tab()

            with gr.TabItem("Backup Management", id="backup group", visible=True):
                create_backup_tab()
                create_view_backups_tab()
                create_restore_backup_tab()

            with gr.TabItem("Utilities", id="util group", visible=True):
                create_utilities_yt_video_tab()
                create_utilities_yt_audio_tab()
                create_utilities_yt_timestamp_tab()

            with gr.TabItem("Local LLM", id="local llm group", visible=True):
                create_chat_with_llamafile_tab()
                create_ollama_tab()
                #create_huggingface_tab()

            with gr.TabItem("Trashcan", id="trashcan group", visible=True):
                create_search_and_mark_trash_tab()
                create_view_trash_tab()
                create_delete_trash_tab()
                create_empty_trash_tab()

            with gr.TabItem("Evaluations", id="eval", visible=True):
                create_geval_tab()
                create_infinite_bench_tab()
                # FIXME
                #create_mmlu_pro_tab()

            with gr.TabItem("Introduction/Help", id="introduction group", visible=True):
                create_introduction_tab()

            with gr.TabItem("Config Editor", id="config group"):
                create_config_editor_tab()

    # Launch the interface
    server_port_variable = 7860
    os.environ['GRADIO_ANALYTICS_ENABLED'] = 'False'
    if share==True:
        iface.launch(share=True)
    elif server_mode and not share_public:
        iface.launch(share=False, server_name="0.0.0.0", server_port=server_port_variable, )
    else:
        try:
            iface.launch(share=False, server_name="0.0.0.0", server_port=server_port_variable, )
        except Exception as e:
            logging.error(f"Error launching interface: {str(e)}")
