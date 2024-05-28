#!/usr/bin/env python3
# Std Lib Imports
import argparse
import asyncio
import atexit
import configparser
from datetime import datetime
import hashlib
import json
import logging
import os
import platform
import re
import shutil
import signal
import sqlite3
import subprocess
import sys
import time
import unicodedata
from multiprocessing import process
from typing import Callable, Dict, List, Optional, Tuple
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
import webbrowser
import zipfile

# Local Module Imports (Libraries specific to this project)
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'App_Function_Libraries')))
from App_Function_Libraries import *
from App_Function_Libraries.Web_UI_Lib import *
from App_Function_Libraries.Article_Extractor_Lib import *
from App_Function_Libraries.Article_Summarization_Lib import *
from App_Function_Libraries.Audio_Transcription_Lib import *
from App_Function_Libraries.Chunk_Lib import *
from App_Function_Libraries.Diarization_Lib import *
from App_Function_Libraries.Local_File_Processing_Lib import *
from App_Function_Libraries.Local_LLM_Inference_Engine_Lib import *
from App_Function_Libraries.Local_Summarization_Lib import *
from App_Function_Libraries.Summarization_General_Lib import *
from App_Function_Libraries.System_Checks_Lib import *
from App_Function_Libraries.Tokenization_Methods_Lib import *
from App_Function_Libraries.Video_DL_Ingestion_Lib import *
#from App_Function_Libraries.Web_UI_Lib import *


# 3rd-Party Module Imports
from bs4 import BeautifulSoup
import gradio as gr
import nltk
from playwright.async_api import async_playwright
import requests
from requests.exceptions import RequestException
import trafilatura
import yt_dlp


# OpenAI Tokenizer support
from openai import OpenAI
from tqdm import tqdm
import tiktoken

# Other Tokenizers
from transformers import GPT2Tokenizer

#######################
# Logging Setup
#

log_level = "DEBUG"
logging.basicConfig(level=getattr(logging, log_level), format='%(asctime)s - %(levelname)s - %(message)s')
os.environ["GRADIO_ANALYTICS_ENABLED"] = "False"

#############
# Global variables setup
global DEFAULT_CHUNK_DURATION
DEFAULT_CHUNK_DURATION = 30
global WORDS_PER_SECOND
WORDS_PER_SECOND = 3
global custom_prompt
custom_prompt = None

#
#
#######################

#######################
# Function Sections
#


abc_xyz = """
    Database Setup
    Config Loading
    System Checks
    DataBase Functions
    Processing Paths and local file handling
    Video Download/Handling
    Audio Transcription
    Diarization
    Chunking-related Techniques & Functions
    Tokenization-related Techniques & Functions
    Summarizers
    Gradio UI
    Main
"""

#
#
#######################


#######################
#
#       TL/DW: Too Long Didn't Watch
#
#  Project originally created by https://github.com/the-crypt-keeper
#  Modifications made by https://github.com/rmusser01
#  All credit to the original authors, I've just glued shit together.
#
#
# Usage:
#
#   Download Audio only from URL -> Transcribe audio:
#       python summarize.py https://www.youtube.com/watch?v=4nd1CDZP21s`
#
#   Download Audio+Video from URL -> Transcribe audio from Video:**
#       python summarize.py -v https://www.youtube.com/watch?v=4nd1CDZP21s`
#
#   Download Audio only from URL -> Transcribe audio -> Summarize using (`anthropic`/`cohere`/`openai`/`llama` (llama.cpp)/`ooba` (oobabooga/text-gen-webui)/`kobold` (kobold.cpp)/`tabby` (Tabbyapi)) API:**
#       python summarize.py -v https://www.youtube.com/watch?v=4nd1CDZP21s -api <your choice of API>` - Make sure to put your API key into `config.txt` under the appropriate API variable
#
#   Download Audio+Video from a list of videos in a text file (can be file paths or URLs) and have them all summarized:**
#       python summarize.py ./local/file_on_your/system --api_name <API_name>`
#
#   Run it as a WebApp**
#       python summarize.py -gui` - This requires you to either stuff your API keys into the `config.txt` file, or pass them into the app every time you want to use it.
#           Can be helpful for setting up a shared instance, but not wanting people to perform inference on your server.
#
#######################


#######################
# Random issues I've encountered and how I solved them:
#   1. Something about cuda nn library missing, even though cuda is installed...
#       https://github.com/tensorflow/tensorflow/issues/54784 - Basically, installing zlib made it go away. idk.
#       Or https://github.com/SYSTRAN/faster-whisper/issues/85
#
#   2. ERROR: Could not install packages due to an OSError: [WinError 2] The system cannot find the file specified: 'C:\\Python312\\Scripts\\dateparser-download.exe' -> 'C:\\Python312\\Scripts\\dateparser-download.exe.deleteme'
#       Resolved through adding --user to the pip install command
#
#   3. ?
#
#######################


#######################
# DB Setup

# Handled by SQLite_DB.py

#######################


#######################
# Config loading
#

# Read configuration from file
config = configparser.ConfigParser()
config.read('config.txt')

# API Keys
anthropic_api_key = config.get('API', 'anthropic_api_key', fallback=None)
logging.debug(f"Loaded Anthropic API Key: {anthropic_api_key}")

cohere_api_key = config.get('API', 'cohere_api_key', fallback=None)
logging.debug(f"Loaded cohere API Key: {cohere_api_key}")

groq_api_key = config.get('API', 'groq_api_key', fallback=None)
logging.debug(f"Loaded groq API Key: {groq_api_key}")

openai_api_key = config.get('API', 'openai_api_key', fallback=None)
logging.debug(f"Loaded openAI Face API Key: {openai_api_key}")

huggingface_api_key = config.get('API', 'huggingface_api_key', fallback=None)
logging.debug(f"Loaded HuggingFace Face API Key: {huggingface_api_key}")

openrouter_api_key = config.get('Local-API', 'openrouter', fallback=None)
logging.debug(f"Loaded OpenRouter API Key: {openrouter_api_key}")

# Models
anthropic_model = config.get('API', 'anthropic_model', fallback='claude-3-sonnet-20240229')
cohere_model = config.get('API', 'cohere_model', fallback='command-r-plus')
groq_model = config.get('API', 'groq_model', fallback='llama3-70b-8192')
openai_model = config.get('API', 'openai_model', fallback='gpt-4-turbo')
huggingface_model = config.get('API', 'huggingface_model', fallback='CohereForAI/c4ai-command-r-plus')
openrouter_model = config.get('API', 'openrouter_model', fallback='microsoft/wizardlm-2-8x22b')

# Local-Models
kobold_api_IP = config.get('Local-API', 'kobold_api_IP', fallback='http://127.0.0.1:5000/api/v1/generate')
kobold_api_key = config.get('Local-API', 'kobold_api_key', fallback='')

llama_api_IP = config.get('Local-API', 'llama_api_IP', fallback='http://127.0.0.1:8080/v1/chat/completions')
llama_api_key = config.get('Local-API', 'llama_api_key', fallback='')

ooba_api_IP = config.get('Local-API', 'ooba_api_IP', fallback='http://127.0.0.1:5000/v1/chat/completions')
ooba_api_key = config.get('Local-API', 'ooba_api_key', fallback='')

tabby_api_IP = config.get('Local-API', 'tabby_api_IP', fallback='http://127.0.0.1:5000/api/v1/generate')
tabby_api_key = config.get('Local-API', 'tabby_api_key', fallback=None)

vllm_api_url = config.get('Local-API', 'vllm_api_IP', fallback='http://127.0.0.1:500/api/v1/chat/completions')
vllm_api_key = config.get('Local-API', 'vllm_api_key', fallback=None)

# Chunk settings for timed chunking summarization
DEFAULT_CHUNK_DURATION = config.getint('Settings', 'chunk_duration', fallback='30')
WORDS_PER_SECOND = config.getint('Settings', 'words_per_second', fallback='3')

# Retrieve output paths from the configuration file
output_path = config.get('Paths', 'output_path', fallback='results')

# Retrieve processing choice from the configuration file
processing_choice = config.get('Processing', 'processing_choice', fallback='cpu')

# Log file
# logging.basicConfig(filename='debug-runtime.log', encoding='utf-8', level=logging.DEBUG)

#
#
#######################


#######################
# System Startup Notice
#

# Dirty hack - sue me. - FIXME - fix this...
os.environ['KMP_DUPLICATE_LIB_OK'] = 'True'

whisper_models = ["small", "medium", "small.en", "medium.en"]
source_languages = {
    "en": "English",
    "zh": "Chinese",
    "de": "German",
    "es": "Spanish",
    "ru": "Russian",
    "ko": "Korean",
    "fr": "French"
}
source_language_list = [key[0] for key in source_languages.items()]


def print_hello():
    print(r"""_____  _          ________  _    _                                 
|_   _|| |        / /|  _  \| |  | | _                              
  | |  | |       / / | | | || |  | |(_)                             
  | |  | |      / /  | | | || |/\| |                                
  | |  | |____ / /   | |/ / \  /\  / _                              
  \_/  \_____//_/    |___/   \/  \/ (_)                             


 _                   _                                              
| |                 | |                                             
| |_   ___    ___   | |  ___   _ __    __ _                         
| __| / _ \  / _ \  | | / _ \ | '_ \  / _` |                        
| |_ | (_) || (_) | | || (_) || | | || (_| | _                      
 \__| \___/  \___/  |_| \___/ |_| |_| \__, |( )                     
                                       __/ ||/                      
                                      |___/                         
     _  _      _         _  _                      _          _     
    | |(_)    | |       ( )| |                    | |        | |    
  __| | _   __| | _ __  |/ | |_  __      __  __ _ | |_   ___ | |__  
 / _` || | / _` || '_ \    | __| \ \ /\ / / / _` || __| / __|| '_ \ 
| (_| || || (_| || | | |   | |_   \ V  V / | (_| || |_ | (__ | | | |
 \__,_||_| \__,_||_| |_|    \__|   \_/\_/   \__,_| \__| \___||_| |_|
""")
    time.sleep(1)
    return


#
#
#######################


#######################
# System Check Functions
#
# 1. platform_check()
# 2. cuda_check()
# 3. decide_cpugpu()
# 4. check_ffmpeg()
# 5. download_ffmpeg()
#
#######################


#######################
# DB Functions
#
#     create_tables()
#     add_keyword()
#     delete_keyword()
#     add_keyword()
#     add_media_with_keywords()
#     search_db()
#     format_results()
#     search_and_display()
#     export_to_csv()
#     is_valid_url()
#     is_valid_date()
#
########################################################################################################################


########################################################################################################################
# Processing Paths and local file handling
#
# Function List
# 1. read_paths_from_file(file_path)
# 2. process_path(path)
# 3. process_local_file(file_path)
# 4. read_paths_from_file(file_path: str) -> List[str]
#
#
########################################################################################################################


#######################################################################################################################
# Online Article Extraction / Handling
#
# Function List
# 1. get_page_title(url)
# 2. get_article_text(url)
# 3. get_article_title(article_url_arg)
#
#
#######################################################################################################################


#######################################################################################################################
# Video Download/Handling
# Video-DL-Ingestion-Lib
#
# Function List
# 1. get_video_info(url)
# 2. create_download_directory(title)
# 3. sanitize_filename(title)
# 4. normalize_title(title)
# 5. get_youtube(video_url)
# 6. get_playlist_videos(playlist_url)
# 7. download_video(video_url, download_path, info_dict, download_video_flag)
# 8. save_to_file(video_urls, filename)
# 9. save_summary_to_file(summary, file_path)
# 10. process_url(url, num_speakers, whisper_model, custom_prompt, offset, api_name, api_key, vad_filter, download_video, download_audio, rolling_summarization, detail_level, question_box, keywords, chunk_summarization, chunk_duration_input, words_per_second_input)
#
#
#######################################################################################################################


#######################################################################################################################
# Audio Transcription
#
# Function List
# 1. convert_to_wav(video_file_path, offset=0, overwrite=False)
# 2. speech_to_text(audio_file_path, selected_source_lang='en', whisper_model='small.en', vad_filter=False)
#
#
#######################################################################################################################


#######################################################################################################################
# Diarization
#
# Function List 1. speaker_diarize(video_file_path, segments, embedding_model = "pyannote/embedding",
#                                   embedding_size=512, num_speakers=0)
#
#
#######################################################################################################################


#######################################################################################################################
# Chunking-related Techniques & Functions
#
#
# FIXME
#
#
#######################################################################################################################


#######################################################################################################################
# Tokenization-related Functions
#
#

# FIXME

#
#
#######################################################################################################################


#######################################################################################################################
# Website-related Techniques & Functions
#
#

#
#
#######################################################################################################################


#######################################################################################################################
# Summarizers
#
# Function List
# 1. extract_text_from_segments(segments: List[Dict]) -> str
# 2. summarize_with_openai(api_key, file_path, custom_prompt_arg)
# 3. summarize_with_claude(api_key, file_path, model, custom_prompt_arg, max_retries=3, retry_delay=5)
# 4. summarize_with_cohere(api_key, file_path, model, custom_prompt_arg)
# 5. summarize_with_groq(api_key, file_path, model, custom_prompt_arg)
#
#################################
# Local Summarization
#
# Function List
#
# 1. summarize_with_local_llm(file_path, custom_prompt_arg)
# 2. summarize_with_llama(api_url, file_path, token, custom_prompt)
# 3. summarize_with_kobold(api_url, file_path, kobold_api_token, custom_prompt)
# 4. summarize_with_oobabooga(api_url, file_path, ooba_api_token, custom_prompt)
# 5. summarize_with_vllm(vllm_api_url, vllm_api_key_function_arg, llm_model, text, vllm_custom_prompt_function_arg)
# 6. summarize_with_tabbyapi(tabby_api_key, tabby_api_IP, text, tabby_model, custom_prompt)
# 7. save_summary_to_file(summary, file_path)
#
#######################################################################################################################


#######################################################################################################################
# Summarization with Detail
#

# FIXME - see 'Old_Chunking_Lib.py'

#
#
#######################################################################################################################


#######################################################################################################################
# Gradio UI
#
#######################################################################################################################
# Function Definitions
#

# Only to be used when configured with Gradio for HF Space


def format_transcription(transcription_result_arg):
    if transcription_result_arg:
        json_data = transcription_result_arg['transcription']
        return json.dumps(json_data, indent=2)
    else:
        return ""


def format_file_path(file_path, fallback_path=None):
    if file_path and os.path.exists(file_path):
        logging.debug(f"File exists: {file_path}")
        return file_path
    elif fallback_path and os.path.exists(fallback_path):
        logging.debug(f"File does not exist: {file_path}. Returning fallback path: {fallback_path}")
        return fallback_path
    else:
        logging.debug(f"File does not exist: {file_path}. No fallback path available.")
        return None


def search_media(query, fields, keyword, page):
    try:
        results = search_and_display(query, fields, keyword, page)
        return results
    except Exception as e:
        logger.error(f"Error searching media: {e}")
        return str(e)


# FIXME - Change to use 'check_api()' function - also, create 'check_api()' function
def ask_question(transcription, question, api_name, api_key):
    if not question.strip():
        return "Please enter a question."

        prompt = f"""Transcription:\n{transcription}

        Given the above transcription, please answer the following:\n\n{question}"""

        # FIXME - Refactor main API checks so they're their own function - api_check()
        # Call api_check() function here

        if api_name.lower() == "openai":
            openai_api_key = api_key if api_key else config.get('API', 'openai_api_key', fallback=None)
            headers = {
                'Authorization': f'Bearer {openai_api_key}',
                'Content-Type': 'application/json'
            }
            if openai_model:
                pass
            else:
                openai_model = 'gpt-4-turbo'
            data = {
                "model": openai_model,
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a helpful assistant that answers questions based on the given "
                                   "transcription and summary."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "max_tokens": 150000,
                "temperature": 0.1
            }
            response = requests.post('https://api.openai.com/v1/chat/completions', headers=headers, json=data)

        if response.status_code == 200:
            answer = response.json()['choices'][0]['message']['content'].strip()
            return answer
        else:
            return "Failed to process the question."
    else:
        return "Question answering is currently only supported with the OpenAI API."


summarizers: Dict[str, Callable[[str, str], str]] = {
    'tabbyapi': summarize_with_tabbyapi,
    'openai': summarize_with_openai,
    'anthropic': summarize_with_claude,
    'cohere': summarize_with_cohere,
    'groq': summarize_with_groq,
    'llama': summarize_with_llama,
    'kobold': summarize_with_kobold,
    'oobabooga': summarize_with_oobabooga,
    'local-llm': summarize_with_local_llm,
    'huggingface': summarize_with_huggingface,
    'openrouter': summarize_with_openrouter
    # Add more APIs here as needed
}


# def gradio UI
def launch_ui(demo_mode=False):
    whisper_models = ["small.en", "medium.en", "large"]
    global DEFAULT_CHUNK_DURATION
    DEFAULT_CHUNK_DURATION = 30
    global WORDS_PER_SECOND
    WORDS_PER_SECOND = 3
    with gr.Blocks() as iface:
        # Tab 1: Audio Transcription + Summarization
        with gr.Tab("Audio Transcription + Summarization"):

            with gr.Row():
                # Light/Dark mode toggle switch
                theme_toggle = gr.Radio(choices=["Light", "Dark"], value="Light",
                                        label="Light/Dark Mode Toggle (Toggle to change UI color scheme)")

                # UI Mode toggle switch
                ui_mode_toggle = gr.Radio(choices=["Simple", "Advanced"], value="Simple",
                                          label="UI Mode (Toggle to show all options)")

                # Add the new toggle switch
                chunk_summarization_toggle = gr.Radio(choices=["Non-Chunked", "Chunked-Summarization"],
                                                      value="Non-Chunked",
                                                      label="Summarization Mode")
            with gr.Row():

                # Add the additional input components
                chunk_text_by_words_checkbox = gr.Checkbox(label="Chunk Text by Words", value=False, visible=False)
                max_words_input = gr.Number(label="Max Words", value=0, precision=0, visible=False)

                chunk_text_by_sentences_checkbox = gr.Checkbox(label="Chunk Text by Sentences", value=False,
                                                               visible=False)
                max_sentences_input = gr.Number(label="Max Sentences", value=0, precision=0, visible=False)

                chunk_text_by_paragraphs_checkbox = gr.Checkbox(label="Chunk Text by Paragraphs", value=False,
                                                                visible=False)
                max_paragraphs_input = gr.Number(label="Max Paragraphs", value=0, precision=0, visible=False)

                chunk_text_by_tokens_checkbox = gr.Checkbox(label="Chunk Text by Tokens", value=False, visible=False)
                max_tokens_input = gr.Number(label="Max Tokens", value=0, precision=0, visible=False)

            # URL input is always visible
            url_input = gr.Textbox(label="URL (Mandatory) --> Playlist URLs will be stripped and only the linked video"
                                         " will be downloaded)", placeholder="Enter the video URL here")

            # Inputs to be shown or hidden
            num_speakers_input = gr.Number(value=2, label="Number of Speakers(Optional - Currently has no effect)",
                                           visible=False)
            whisper_model_input = gr.Dropdown(choices=whisper_models, value="small.en",
                                              label="Whisper Model(This is the ML model used for transcription.)",
                                              visible=False)
            custom_prompt_input = gr.Textbox(
                label="Custom Prompt (Customize your summarization, or ask a question about the video and have it "
                      "answered)\n Does not work against the summary currently.",
                placeholder="Above is the transcript of a video. Please read "
                            "through the transcript carefully. Identify the main topics that are discussed over the "
                            "course of the transcript. Then, summarize the key points about each main topic in a "
                            "concise bullet point. The bullet points should cover the key information conveyed about "
                            "each topic in the video, but should be much shorter than the full transcript. Please "
                            "output your bullet point summary inside <bulletpoints> tags.",
                lines=3, visible=True)
            offset_input = gr.Number(value=0, label="Offset (Seconds into the video to start transcribing at)",
                                     visible=False)
            api_name_input = gr.Dropdown(
                choices=[None, "Local-LLM", "OpenAI", "Anthropic", "Cohere", "Groq", "OpenRouter", "Llama.cpp",
                         "Kobold", "Ooba", "HuggingFace"],
                value=None,
                label="API Name (Mandatory) --> Unless you just want a Transcription", visible=True)
            api_key_input = gr.Textbox(
                label="API Key (Mandatory) --> Unless you're running a local model/server OR have no API selected",
                placeholder="Enter your API key here; Ignore if using Local API or Built-in API('Local-LLM')",
                visible=True)
            vad_filter_input = gr.Checkbox(label="VAD Filter (WIP)", value=False,
                                           visible=False)
            rolling_summarization_input = gr.Checkbox(label="Enable Rolling Summarization", value=False,
                                                      visible=False)
            download_video_input = gr.components.Checkbox(label="Download Video(Select to allow for file download of "
                                                                "selected video)", value=False, visible=False)
            download_audio_input = gr.components.Checkbox(label="Download Audio(Select to allow for file download of "
                                                                "selected Video's Audio)", value=False, visible=False)
            detail_level_input = gr.Slider(minimum=0.01, maximum=1.0, value=0.01, step=0.01, interactive=True,
                                           label="Summary Detail Level (Slide me) (Only OpenAI currently supported)",
                                           visible=False)
            keywords_input = gr.Textbox(label="Keywords", placeholder="Enter keywords here (comma-separated Example: "
                                                                      "tag_one,tag_two,tag_three)",
                                        value="default,no_keyword_set",
                                        visible=True)
            question_box_input = gr.Textbox(label="Question",
                                            placeholder="Enter a question to ask about the transcription",
                                            visible=False)
            chunk_summarization_input = gr.Checkbox(label="Time-based Chunk Summarization",
                                                    value=False,
                                                    visible=False)
            chunk_duration_input = gr.Number(label="Chunk Duration (seconds)", value=DEFAULT_CHUNK_DURATION,
                                             visible=False)
            words_per_second_input = gr.Number(label="Words per Second", value=WORDS_PER_SECOND,
                                               visible=False)
            # time_based_summarization_input = gr.Checkbox(label="Enable Time-based Summarization", value=False,
            # visible=False) time_chunk_duration_input = gr.Number(label="Time Chunk Duration (seconds)", value=60,
            # visible=False) llm_model_input = gr.Dropdown(label="LLM Model", choices=["gpt-4o", "gpt-4-turbo",
            # "claude-3-sonnet-20240229", "command-r-plus", "CohereForAI/c4ai-command-r-plus", "llama3-70b-8192"],
            # value="gpt-4o", visible=False)

            inputs = [
                num_speakers_input, whisper_model_input, custom_prompt_input, offset_input, api_name_input,
                api_key_input, vad_filter_input, download_video_input, download_audio_input,
                rolling_summarization_input, detail_level_input, question_box_input, keywords_input,
                chunk_summarization_input, chunk_duration_input, words_per_second_input,
                chunk_text_by_words_checkbox, max_words_input,
                chunk_text_by_sentences_checkbox, max_sentences_input,
                chunk_text_by_paragraphs_checkbox, max_paragraphs_input,
                chunk_text_by_tokens_checkbox, max_tokens_input
            ]
            # inputs_1 = [
            #     url_input_1,
            #     num_speakers_input, whisper_model_input, custom_prompt_input_1, offset_input, api_name_input_1,
            #     api_key_input_1, vad_filter_input, download_video_input, download_audio_input,
            #     rolling_summarization_input, detail_level_input, question_box_input, keywords_input_1,
            #     chunk_summarization_input, chunk_duration_input, words_per_second_input,
            #     time_based_summarization_input, time_chunk_duration_input, llm_model_input
            # ]

            outputs = [
                gr.Textbox(label="Transcription (Resulting Transcription from your input URL)"),
                gr.Textbox(label="Summary or Status Message (Current status of Summary or Summary itself)"),
                gr.File(label="Download Transcription as JSON (Download the Transcription as a file)"),
                gr.File(label="Download Summary as Text (Download the Summary as a file)"),
                gr.File(label="Download Video (Download the Video as a file)", visible=False),
                gr.File(label="Download Audio (Download the Audio as a file)", visible=False),
            ]

            def toggle_chunk_summarization(mode):
                visible = (mode == "Chunked-Summarization")
                return [
                    gr.update(visible=visible),  # chunk_text_by_words_checkbox
                    gr.update(visible=visible),  # max_words_input
                    gr.update(visible=visible),  # chunk_text_by_sentences_checkbox
                    gr.update(visible=visible),  # max_sentences_input
                    gr.update(visible=visible),  # chunk_text_by_paragraphs_checkbox
                    gr.update(visible=visible),  # max_paragraphs_input
                    gr.update(visible=visible),  # chunk_text_by_tokens_checkbox
                    gr.update(visible=visible)  # max_tokens_input
                ]

            chunk_summarization_toggle.change(fn=toggle_chunk_summarization, inputs=chunk_summarization_toggle,
                                              outputs=[
                                                  chunk_text_by_words_checkbox, max_words_input,
                                                  chunk_text_by_sentences_checkbox, max_sentences_input,
                                                  chunk_text_by_paragraphs_checkbox, max_paragraphs_input,
                                                  chunk_text_by_tokens_checkbox, max_tokens_input
                                              ])

            def start_llamafile(prompt, temperature, top_k, top_p, min_p, stream, stop, typical_p, repeat_penalty,
                                repeat_last_n,
                                penalize_nl, presence_penalty, frequency_penalty, penalty_prompt, ignore_eos,
                                system_prompt):
                # Code to start llamafile with the provided configuration
                local_llm_gui_function(prompt, temperature, top_k, top_p, min_p, stream, stop, typical_p,
                                       repeat_penalty,
                                       repeat_last_n,
                                       penalize_nl, presence_penalty, frequency_penalty, penalty_prompt, ignore_eos,
                                       system_prompt)
                # FIXME
                return "Llamafile started"

            def stop_llamafile():
                # Code to stop llamafile
                # ...
                return "Llamafile stopped"

            def toggle_light(mode):
                if mode == "Dark":
                    return """
                    <style>
                        body {
                            background-color: #1c1c1c;
                            color: #ffffff;
                        }
                        .gradio-container {
                            background-color: #1c1c1c;
                            color: #ffffff;
                        }
                        .gradio-button {
                            background-color: #4c4c4c;
                            color: #ffffff;
                        }
                        .gradio-input {
                            background-color: #4c4c4c;
                            color: #ffffff;
                        }
                        .gradio-dropdown {
                            background-color: #4c4c4c;
                            color: #ffffff;
                        }
                        .gradio-slider {
                            background-color: #4c4c4c;
                        }
                        .gradio-checkbox {
                            background-color: #4c4c4c;
                        }
                        .gradio-radio {
                            background-color: #4c4c4c;
                        }
                        .gradio-textbox {
                            background-color: #4c4c4c;
                            color: #ffffff;
                        }
                        .gradio-label {
                            color: #ffffff;
                        }
                    </style>
                    """
                else:
                    return """
                    <style>
                        body {
                            background-color: #ffffff;
                            color: #000000;
                        }
                        .gradio-container {
                            background-color: #ffffff;
                            color: #000000;
                        }
                        .gradio-button {
                            background-color: #f0f0f0;
                            color: #000000;
                        }
                        .gradio-input {
                            background-color: #f0f0f0;
                            color: #000000;
                        }
                        .gradio-dropdown {
                            background-color: #f0f0f0;
                            color: #000000;
                        }
                        .gradio-slider {
                            background-color: #f0f0f0;
                        }
                        .gradio-checkbox {
                            background-color: #f0f0f0;
                        }
                        .gradio-radio {
                            background-color: #f0f0f0;
                        }
                        .gradio-textbox {
                            background-color: #f0f0f0;
                            color: #000000;
                        }
                        .gradio-label {
                            color: #000000;
                        }
                    </style>
                    """

            # Set the event listener for the Light/Dark mode toggle switch
            theme_toggle.change(fn=toggle_light, inputs=theme_toggle, outputs=gr.HTML())

            # Function to toggle visibility of advanced inputs
            def toggle_ui(mode):
                visible = (mode == "Advanced")
                return [
                    gr.update(visible=True) if i in [0, 3, 5, 6, 13] else gr.update(visible=visible)
                    for i in range(len(inputs))
                ]

            # Set the event listener for the UI Mode toggle switch
            ui_mode_toggle.change(fn=toggle_ui, inputs=ui_mode_toggle, outputs=inputs)

            # Combine URL input and inputs lists
            all_inputs = [url_input] + inputs

            gr.Interface(
                fn=process_url,
                inputs=all_inputs,
                outputs=outputs,
                title="Video Transcription and Summarization",
                description="Submit a video URL for transcription and summarization. Ensure you input all necessary "
                            "information including API keys."
            )

        # Tab 2: Scrape & Summarize Articles/Websites
        with gr.Tab("Scrape & Summarize Articles/Websites"):
            url_input = gr.Textbox(label="Article URL", placeholder="Enter the article URL here")
            custom_article_title_input = gr.Textbox(label="Custom Article Title (Optional)",
                                                    placeholder="Enter a custom title for the article")
            custom_prompt_input = gr.Textbox(
                label="Custom Prompt (Optional)",
                placeholder="Provide a custom prompt for summarization",
                lines=3
            )
            api_name_input = gr.Dropdown(
                choices=[None, "huggingface", "openrouter", "openai", "anthropic", "cohere", "groq", "llama", "kobold",
                         "ooba"],
                value=None,
                label="API Name (Mandatory for Summarization)"
            )
            api_key_input = gr.Textbox(label="API Key (Mandatory if API Name is specified)",
                                       placeholder="Enter your API key here; Ignore if using Local API or Built-in API")
            keywords_input = gr.Textbox(label="Keywords", placeholder="Enter keywords here (comma-separated)",
                                        value="default,no_keyword_set", visible=True)

            scrape_button = gr.Button("Scrape and Summarize")
            result_output = gr.Textbox(label="Result")

            scrape_button.click(scrape_and_summarize, inputs=[url_input, custom_prompt_input, api_name_input,
                                                              api_key_input, keywords_input,
                                                              custom_article_title_input], outputs=result_output)

            gr.Markdown("### Or Paste Unstructured Text Below (Will use settings from above)")
            text_input = gr.Textbox(label="Unstructured Text", placeholder="Paste unstructured text here", lines=10)
            text_ingest_button = gr.Button("Ingest Unstructured Text")
            text_ingest_result = gr.Textbox(label="Result")

            text_ingest_button.click(ingest_unstructured_text,
                                     inputs=[text_input, custom_prompt_input, api_name_input, api_key_input,
                                             keywords_input, custom_article_title_input], outputs=text_ingest_result)

        with gr.Tab("Ingest & Summarize Documents"):
            gr.Markdown("Plan to put ingestion form for documents here")
            gr.Markdown("Will ingest documents and store into SQLite DB")
            gr.Markdown("RAG here we come....:/")

        with gr.Tab("Prompt Examples & Questions Library"):
            gr.Markdown("Plan to put Sample prompts/questions here")
            gr.Markdown("Fabric prompts/live UI?")
            # Searchable list
            with gr.Row():
                search_box = gr.Textbox(label="Search prompts", placeholder="Type to filter prompts")
                search_result = gr.Textbox(label="Matching prompts", interactive=False)
                search_box.change(search_prompts, inputs=search_box, outputs=search_result)

            # Interactive list
            with gr.Row():
                prompt_selector = gr.Radio(choices=all_prompts, label="Select a prompt")
                selected_output = gr.Textbox(label="Selected prompt")
                prompt_selector.change(handle_prompt_selection, inputs=prompt_selector, outputs=selected_output)

            # Categorized display
            with gr.Accordion("Category 1"):
                gr.Markdown("\n".join(prompts_category_1))
            with gr.Accordion("Category 2"):
                gr.Markdown("\n".join(prompts_category_2))

        # Function to update the visibility of the UI elements for Llamafile Settings
        def toggle_advanced_llamafile_mode(is_advanced):
            if is_advanced:
                return [gr.update(visible=True)] * 14
            else:
                return [gr.update(visible=False)] * 11 + [gr.update(visible=True)] * 3

        with gr.Tab("Llamafile Settings"):
            gr.Markdown("Settings for Llamafile")

            # Toggle switch for Advanced/Simple mode
            advanced_mode_toggle = gr.Checkbox(label="Advanced Mode - Click->Click again to only show 'simple' settings. Is a known bug...", value=False)

            # Start/Stop buttons
            start_button = gr.Button("Start Llamafile")
            stop_button = gr.Button("Stop Llamafile")

            # Configuration inputs
            prompt_input = gr.Textbox(label="Prompt", value="")
            temperature_input = gr.Number(label="Temperature", value=0.8)
            top_k_input = gr.Number(label="Top K", value=40)
            top_p_input = gr.Number(label="Top P", value=0.95)
            min_p_input = gr.Number(label="Min P", value=0.05)
            stream_input = gr.Checkbox(label="Stream", value=False)
            stop_input = gr.Textbox(label="Stop", value="[]")
            typical_p_input = gr.Number(label="Typical P", value=1.0)
            repeat_penalty_input = gr.Number(label="Repeat Penalty", value=1.1)
            repeat_last_n_input = gr.Number(label="Repeat Last N", value=64)
            penalize_nl_input = gr.Checkbox(label="Penalize New Lines", value=False)
            presence_penalty_input = gr.Number(label="Presence Penalty", value=0.0)
            frequency_penalty_input = gr.Number(label="Frequency Penalty", value=0.0)
            penalty_prompt_input = gr.Textbox(label="Penalty Prompt", value="")
            ignore_eos_input = gr.Checkbox(label="Ignore EOS", value=False)
            system_prompt_input = gr.Textbox(label="System Prompt", value="")

            # Output display
            output_display = gr.Textbox(label="Llamafile Output")

            # Function calls local_llm_gui_function() with the provided arguments
            # local_llm_gui_function() is found in 'Local_LLM_Inference_Engine_Lib.py' file
            start_button.click(start_llamafile,
                               inputs=[prompt_input, temperature_input, top_k_input, top_p_input, min_p_input,
                                       stream_input, stop_input, typical_p_input, repeat_penalty_input,
                                       repeat_last_n_input, penalize_nl_input, presence_penalty_input,
                                       frequency_penalty_input, penalty_prompt_input, ignore_eos_input,
                                       system_prompt_input], outputs=output_display)

            # This function is not implemented yet...
            # FIXME - Implement this function
            stop_button.click(stop_llamafile, outputs=output_display)

        # Toggle event for Advanced/Simple mode
        advanced_mode_toggle.change(toggle_advanced_llamafile_mode,
                                    inputs=[advanced_mode_toggle],
                                    outputs=[top_k_input, top_p_input, min_p_input, stream_input, stop_input,
                                             typical_p_input, repeat_penalty_input, repeat_last_n_input,
                                             penalize_nl_input, presence_penalty_input, frequency_penalty_input,
                                             penalty_prompt_input, ignore_eos_input])

        with gr.Tab("Llamafile Chat Interface"):
            gr.Markdown("Page to interact with Llamafile Server (iframe to Llamafile server port)")
            # Define the HTML content with the iframe
            html_content = """
            <!DOCTYPE html>
                <html lang="en">
                <head>
                    <meta charset="UTF-8">
                    <meta name="viewport" content="width=device-width, initial-scale=1.0">
                    <title>Llama.cpp Server Chat Interface - Loaded from  http://127.0.0.1:8080</title>
                    <style>
                        body, html {
                        height: 100%;
                        margin: 0;
                        padding: 0;
                    }
                    iframe {
                        border: none;
                        width: 85%;
                        height: 85vh; /* Full viewport height */
                    }
                </style>
            </head>
            <body>
                <iframe src="http://127.0.0.1:8080" title="Llama.cpp Server Chat Interface - Loaded from  http://127.0.0.1:8080"></iframe>
            </body>
            </html>
            """
            gr.HTML(html_content)

    with gr.Blocks() as search_interface:
        with gr.Tab("Search & Detailed View"):
            search_query_input = gr.Textbox(label="Search Query", placeholder="Enter your search query here...")
            search_fields_input = gr.CheckboxGroup(label="Search Fields",
                                                   choices=["Title", "Content", "URL", "Type", "Author"],
                                                   value=["Title"])
            keywords_input = gr.Textbox(label="Keywords to Match against",
                                        placeholder="Enter keywords here (comma-separated)...")
            page_input = gr.Slider(label="Pages of results to display", minimum=1, maximum=10, step=1, value=1)

            search_button = gr.Button("Search")
            results_output = gr.Dataframe()
            index_input = gr.Number(label="Select index of the result", value=None)
            details_button = gr.Button("Show Details")
            details_output = gr.HTML()

            search_button.click(
                fn=search_and_display,
                inputs=[search_query_input, search_fields_input, keywords_input, page_input],
                outputs=results_output
            )

            details_button.click(
                fn=display_details,
                inputs=[index_input, results_output],
                outputs=details_output
            )
    # search_tab = gr.Interface(
    #     fn=search_and_display,
    #     inputs=[
    #         gr.Textbox(label="Search Query", placeholder="Enter your search query here..."),
    #         gr.CheckboxGroup(label="Search Fields", choices=["Title", "Content", "URL", "Type", "Author"],
    #                          value=["Title"]),
    #         gr.Textbox(label="Keywords", placeholder="Enter keywords here (comma-separated)..."),
    #         gr.Slider(label="Page", minimum=1, maximum=10, step=1, value=1)
    #     ],
    #     outputs=gr.Dataframe(label="Search Results", height=300)  # Height in pixels
    #     #outputs=gr.Dataframe(label="Search Results")
    # )

    export_keywords_interface = gr.Interface(
        fn=export_keywords_to_csv,
        inputs=[],
        outputs=[gr.File(label="Download Exported Keywords"), gr.Textbox(label="Status")],
        title="Export Keywords",
        description="Export all keywords in the database to a CSV file."
    )

    # Gradio interface for importing data
    def import_data(file):
        # Placeholder for actual import functionality
        return "Data imported successfully"

    import_interface = gr.Interface(
        fn=import_data,
        inputs=gr.File(label="Upload file for import"),
        outputs="text",
        title="Import Data",
        description="Import data into the database from a CSV file."
    )

    import_export_tab = gr.TabbedInterface(
        [gr.TabbedInterface(
            [gr.Interface(
                fn=export_to_csv,
                inputs=[
                    gr.Textbox(label="Search Query", placeholder="Enter your search query here..."),
                    gr.CheckboxGroup(label="Search Fields", choices=["Title", "Content"], value=["Title"]),
                    gr.Textbox(label="Keyword (Match ALL, can use multiple keywords, separated by ',' (comma) )",
                               placeholder="Enter keywords here..."),
                    gr.Number(label="Page", value=1, precision=0),
                    gr.Number(label="Results per File", value=1000, precision=0)
                ],
                outputs="text",
                title="Export Search Results to CSV",
                description="Export the search results to a CSV file."
            ),
                export_keywords_interface],
            ["Export Search Results", "Export Keywords"]
        ),
            import_interface],
        ["Export", "Import"]
    )

    keyword_add_interface = gr.Interface(
        fn=add_keyword,
        inputs=gr.Textbox(label="Add Keywords (comma-separated)", placeholder="Enter keywords here..."),
        outputs="text",
        title="Add Keywords",
        description="Add one, or multiple keywords to the database.",
        allow_flagging="never"
    )

    keyword_delete_interface = gr.Interface(
        fn=delete_keyword,
        inputs=gr.Textbox(label="Delete Keyword", placeholder="Enter keyword to delete here..."),
        outputs="text",
        title="Delete Keyword",
        description="Delete a keyword from the database.",
        allow_flagging="never"
    )

    browse_keywords_interface = gr.Interface(
        fn=keywords_browser_interface,
        inputs=[],
        outputs="markdown",
        title="Browse Keywords",
        description="View all keywords currently stored in the database."
    )

    keyword_tab = gr.TabbedInterface(
        [browse_keywords_interface, keyword_add_interface, keyword_delete_interface],
        ["Browse Keywords", "Add Keywords", "Delete Keywords"]
    )

    # Combine interfaces into a tabbed interface
    tabbed_interface = gr.TabbedInterface([iface, search_interface, import_export_tab, keyword_tab],
                                          ["Transcription + Summarization", "Search and Detail View", "Export/Import",
                                           "Keywords"])
    # Launch the interface
    server_port_variable = 7860
    global server_mode, share_public
    if server_mode is True and share_public is False:
        tabbed_interface.launch(share=True, server_port=server_port_variable, server_name="http://0.0.0.0")
    elif share_public == True:
        tabbed_interface.launch(share=True, )
    else:
        tabbed_interface.launch(share=False, )


def clean_youtube_url(url):
    parsed_url = urlparse(url)
    query_params = parse_qs(parsed_url.query)
    if 'list' in query_params:
        query_params.pop('list')
    cleaned_query = urlencode(query_params, doseq=True)
    cleaned_url = urlunparse(parsed_url._replace(query=cleaned_query))
    return cleaned_url

def process_url(url,
                num_speakers,
                whisper_model,
                custom_prompt,
                offset,
                api_name,
                api_key,
                vad_filter,
                download_video,
                download_audio,
                rolling_summarization,
                detail_level,
                question_box,
                keywords,
                chunk_summarization,
                chunk_duration_input,
                words_per_second_input,
                chunk_text_by_words,
                max_words,
                chunk_text_by_sentences,
                max_sentences,
                chunk_text_by_paragraphs,
                max_paragraphs,
                chunk_text_by_tokens,
                max_tokens,
                ):
    # Handle the chunk summarization options
    set_chunk_txt_by_words = chunk_text_by_words
    set_max_txt_chunk_words = max_words
    set_chunk_txt_by_sentences = chunk_text_by_sentences
    set_max_txt_chunk_sentences = max_sentences
    set_chunk_txt_by_paragraphs = chunk_text_by_paragraphs
    set_max_txt_chunk_paragraphs = max_paragraphs
    set_chunk_txt_by_tokens = chunk_text_by_tokens
    set_max_txt_chunk_tokens = max_tokens

    # Validate input
    if not url:
        return "No URL provided.", "No URL provided.", None, None, None, None, None, None

    if not is_valid_url(url):
        return "Invalid URL format.", "Invalid URL format.", None, None, None, None, None, None

    # Clean the URL to remove playlist parameters if any
    url = clean_youtube_url(url)

    print("API Name received:", api_name)  # Debugging line

    logging.info(f"Processing URL: {url}")
    video_file_path = None

    try:
        # Instantiate the database, db as a instance of the Database class
        db = Database()
        media_url = url

        info_dict = get_youtube(url)  # Extract video information using yt_dlp
        media_title = info_dict['title'] if 'title' in info_dict else 'Untitled'

        results = main(url, api_name=api_name, api_key=api_key,
                       num_speakers=num_speakers,
                       whisper_model=whisper_model,
                       offset=offset,
                       vad_filter=vad_filter,
                       download_video_flag=download_video,
                       custom_prompt=custom_prompt,
                       overwrite=args.overwrite,
                       rolling_summarization=rolling_summarization,
                       detail=detail_level,
                       keywords=keywords,
                       chunk_summarization=chunk_summarization,
                       chunk_duration=chunk_duration_input,
                       words_per_second=words_per_second_input,
                       )

        if not results:
            return "No URL provided.", "No URL provided.", None, None, None, None, None, None

        transcription_result = results[0]
        transcription_text = json.dumps(transcription_result['transcription'], indent=2)
        summary_text = transcription_result.get('summary', 'Summary not available')

        # Prepare file paths for transcription and summary
        # Sanitize filenames
        audio_file_sanitized = sanitize_filename(transcription_result['audio_file'])
        json_pretty_file_path = os.path.join('Results', audio_file_sanitized.replace('.wav', '.segments_pretty.json'))
        json_file_path = os.path.join('Results', audio_file_sanitized.replace('.wav', '.segments.json'))
        summary_file_path = os.path.join('Results', audio_file_sanitized.replace('.wav', '_summary.txt'))

        logging.debug(f"Transcription result: {transcription_result}")
        logging.debug(f"Audio file path: {transcription_result['audio_file']}")

        # Write the transcription to the JSON File
        try:
            with open(json_file_path, 'w') as json_file:
                json.dump(transcription_result['transcription'], json_file, indent=2)
        except IOError as e:
            logging.error(f"Error writing transcription to JSON file: {e}")

        # Write the summary to the summary file
        with open(summary_file_path, 'w') as summary_file:
            summary_file.write(summary_text)

        if download_video:
            video_file_path = transcription_result['video_path'] if 'video_path' in transcription_result else None

        # Check if files exist before returning paths
        if not os.path.exists(json_file_path):
            raise FileNotFoundError(f"File not found: {json_file_path}")
        if not os.path.exists(summary_file_path):
            raise FileNotFoundError(f"File not found: {summary_file_path}")

        formatted_transcription = format_transcription(transcription_result)

        # Check for chunk summarization
        if chunk_summarization:
            chunk_duration = chunk_duration_input if chunk_duration_input else DEFAULT_CHUNK_DURATION
            words_per_second = words_per_second_input if words_per_second_input else WORDS_PER_SECOND
            summary_text = summarize_chunks(api_name, api_key, transcription_result['transcription'], chunk_duration,
                                            words_per_second)

        # FIXME - This is a mess
        # # Check for time-based chunking summarization
        # if time_based_summarization:
        #     logging.info("MAIN: Time-based Summarization")
        #
        #     # Set the json_file_path
        #     json_file_path = audio_file.replace('.wav', '.segments.json')
        #
        #     # Perform time-based summarization
        #     summary = time_chunk_summarize(api_name, api_key, json_file_path, time_chunk_duration, custom_prompt)
        #
        #     # Handle the summarized output
        #     if summary:
        #         transcription_result['summary'] = summary
        #         logging.info("MAIN: Time-based Summarization successful.")
        #         save_summary_to_file(summary, json_file_path)
        #     else:
        #         logging.warning("MAIN: Time-based Summarization failed.")

        # Add media to the database
        try:
            # Ensure these variables are correctly populated
            custom_prompt = args.custom_prompt if args.custom_prompt else ("\n\nabove is the transcript of a video "
                                                                           "Please read through the transcript carefully. Identify the main topics that are discussed over the "
                                                                           "course of the transcript. Then, summarize the key points about each main topic in a concise bullet "
                                                                           "point. The bullet points should cover the key information conveyed about each topic in the video, "
                                                                           "but should be much shorter than the full transcript. Please output your bullet point summary inside "
                                                                           "<bulletpoints> tags.")

            db = Database()
            create_tables()
            media_url = url
            # FIXME  - IDK?
            video_info = get_video_info(media_url)
            media_title = get_page_title(media_url)
            media_type = "video"
            media_content = transcription_text
            keyword_list = keywords.split(',') if keywords else ["default"]
            media_keywords = ', '.join(keyword_list)
            media_author = "auto_generated"
            media_ingestion_date = datetime.now().strftime('%Y-%m-%d')
            transcription_model = whisper_model  # Add the transcription model used

            # Log the values before calling the function
            logging.info(f"Media URL: {media_url}")
            logging.info(f"Media Title: {media_title}")
            logging.info(f"Media Type: {media_type}")
            logging.info(f"Media Content: {media_content}")
            logging.info(f"Media Keywords: {media_keywords}")
            logging.info(f"Media Author: {media_author}")
            logging.info(f"Ingestion Date: {media_ingestion_date}")
            logging.info(f"Custom Prompt: {custom_prompt}")
            logging.info(f"Summary Text: {summary_text}")
            logging.info(f"Transcription Model: {transcription_model}")

            # Check if any required field is empty
            if not media_url or not media_title or not media_type or not media_content or not media_keywords or not custom_prompt or not summary_text:
                raise InputError("Please provide all required fields.")

            add_media_with_keywords(
                url=media_url,
                title=media_title,
                media_type=media_type,
                content=media_content,
                keywords=media_keywords,
                prompt=custom_prompt,
                summary=summary_text,
                transcription_model=transcription_model,  # Pass the transcription model
                author=media_author,
                ingestion_date=media_ingestion_date
            )
        except Exception as e:
            logging.error(f"Failed to add media to the database: {e}")

        if summary_file_path and os.path.exists(summary_file_path):
            return transcription_text, summary_text, json_file_path, summary_file_path, video_file_path, None
        else:
            return transcription_text, summary_text, json_file_path, None, video_file_path, None


    except Exception as e:
        logging.error(f"Error processing URL: {e}")
        return str(e), 'Error processing the request.', None, None, None, None


# FIXME - Prompt sample box

# Sample data
prompts_category_1 = [
    "What are the key points discussed in the video?",
    "Summarize the main arguments made by the speaker.",
    "Describe the conclusions of the study presented."
]

prompts_category_2 = [
    "How does the proposed solution address the problem?",
    "What are the implications of the findings?",
    "Can you explain the theory behind the observed phenomenon?"
]

all_prompts = prompts_category_1 + prompts_category_2


# Search function
def search_prompts(query):
    filtered_prompts = [prompt for prompt in all_prompts if query.lower() in prompt.lower()]
    return "\n".join(filtered_prompts)


# Handle prompt selection
def handle_prompt_selection(prompt):
    return f"You selected: {prompt}"


#
#
#######################################################################################################################


#######################################################################################################################
# Local LLM Setup / Running
#
# Function List
# 1. download_latest_llamafile(repo, asset_name_prefix, output_filename)
# 2. download_file(url, dest_path, expected_checksum=None, max_retries=3, delay=5)
# 3. verify_checksum(file_path, expected_checksum)
# 4. cleanup_process()
# 5. signal_handler(sig, frame)
# 6. local_llm_function()
# 7. launch_in_new_terminal_windows(executable, args)
# 8. launch_in_new_terminal_linux(executable, args)
# 9. launch_in_new_terminal_mac(executable, args)
#
#
#######################################################################################################################


#######################################################################################################################
# Main()
#

def main(input_path, api_name=None, api_key=None,
         num_speakers=2,
         whisper_model="small.en",
         offset=0,
         vad_filter=False,
         download_video_flag=False,
         custom_prompt=None,
         overwrite=False,
         rolling_summarization=False,
         detail=0.01,
         keywords=None,
         chunk_summarization=False,
         chunk_duration=None,
         words_per_second=None,
         llm_model=None,
         time_based=False,
         set_chunk_txt_by_words=False,
         set_max_txt_chunk_words=0,
         set_chunk_txt_by_sentences=False,
         set_max_txt_chunk_sentences=0,
         set_chunk_txt_by_paragraphs=False,
         set_max_txt_chunk_paragraphs=0,
         set_chunk_txt_by_tokens=False,
         set_max_txt_chunk_tokens=0,
         ):
    global detail_level_number, summary, audio_file, transcription_result

    global detail_level, summary, audio_file

    detail_level = detail

    print(f"Keywords: {keywords}")

    if input_path is None and args.user_interface:
        return []
    start_time = time.monotonic()
    paths = []  # Initialize paths as an empty list
    if os.path.isfile(input_path) and input_path.endswith('.txt'):
        logging.debug("MAIN: User passed in a text file, processing text file...")
        paths = read_paths_from_file(input_path)
    elif os.path.exists(input_path):
        logging.debug("MAIN: Local file path detected")
        paths = [input_path]
    elif (info_dict := get_youtube(input_path)) and 'entries' in info_dict:
        logging.debug("MAIN: YouTube playlist detected")
        print(
            "\n\nSorry, but playlists aren't currently supported. You can run the following command to generate a "
            "text file that you can then pass into this script though! (It may not work... playlist support seems "
            "spotty)" + """\n\n\tpython Get_Playlist_URLs.py <Youtube Playlist URL>\n\n\tThen,\n\n\tpython 
            diarizer.py <playlist text file name>\n\n""")
        return
    else:
        paths = [input_path]
    results = []

    for path in paths:
        try:
            if path.startswith('http'):
                logging.debug("MAIN: URL Detected")
                info_dict = get_youtube(path)
                json_file_path = None
                if info_dict:
                    logging.debug("MAIN: Creating path for video file...")
                    download_path = create_download_directory(info_dict['title'])
                    logging.debug("MAIN: Path created successfully\n MAIN: Now Downloading video from yt_dlp...")
                    try:
                        video_path = download_video(path, download_path, info_dict, download_video_flag)
                    except RuntimeError as e:
                        logging.error(f"Error downloading video: {str(e)}")
                        # FIXME - figure something out for handling this situation....
                        continue
                    logging.debug("MAIN: Video downloaded successfully")
                    logging.debug("MAIN: Converting video file to WAV...")
                    audio_file = convert_to_wav(video_path, offset)
                    logging.debug("MAIN: Audio file converted successfully")
            else:
                if os.path.exists(path):
                    logging.debug("MAIN: Local file path detected")
                    download_path, info_dict, audio_file = process_local_file(path)
                else:
                    logging.error(f"File does not exist: {path}")
                    continue

            if info_dict:
                logging.debug("MAIN: Creating transcription file from WAV")
                segments = speech_to_text(audio_file, whisper_model=whisper_model, vad_filter=vad_filter)

                transcription_result = {
                    'video_path': path,
                    'audio_file': audio_file,
                    'transcription': segments
                }

                if isinstance(segments, dict) and "error" in segments:
                    logging.error(f"Error transcribing audio: {segments['error']}")
                    transcription_result['error'] = segments['error']

                results.append(transcription_result)
                logging.info(f"MAIN: Transcription complete: {audio_file}")

                # Check if segments is a dictionary before proceeding with summarization
                if isinstance(segments, dict):
                    logging.warning("Skipping summarization due to transcription error")
                    continue

                # FIXME
                # Perform rolling summarization based on API Name, detail level, and if an API key exists
                # Will remove the API key once rolling is added for llama.cpp
                if rolling_summarization:
                    logging.info("MAIN: Rolling Summarization")

                    # Extract the text from the segments
                    text = extract_text_from_segments(segments)

                    # Set the json_file_path
                    json_file_path = audio_file.replace('.wav', '.segments.json')

                    # Perform rolling summarization
                    summary = summarize_with_detail_openai(text, detail=detail_level, verbose=False)

                    # Handle the summarized output
                    if summary:
                        transcription_result['summary'] = summary
                        logging.info("MAIN: Rolling Summarization successful.")
                        save_summary_to_file(summary, json_file_path)
                    else:
                        logging.warning("MAIN: Rolling Summarization failed.")
                # Perform summarization based on the specified API
                elif api_name:
                    logging.debug(f"MAIN: Summarization being performed by {api_name}")
                    json_file_path = audio_file.replace('.wav', '.segments.json')
                    if api_name.lower() == 'openai':
                        try:
                            logging.debug(f"MAIN: trying to summarize with openAI")
                            summary = summarize_with_openai(openai_api_key, json_file_path, custom_prompt)
                            if summary != "openai: Error occurred while processing summary":
                                transcription_result['summary'] = summary
                                logging.info(f"Summary generated using {api_name} API")
                                save_summary_to_file(summary, json_file_path)
                                # Add media to the database
                                add_media_with_keywords(
                                    url=path,
                                    title=info_dict.get('title', 'Untitled'),
                                    media_type='video',
                                    content=' '.join([segment['text'] for segment in segments]),
                                    keywords=','.join(keywords),
                                    prompt=custom_prompt or 'No prompt provided',
                                    summary=summary or 'No summary provided',
                                    transcription_model=whisper_model,
                                    author=info_dict.get('uploader', 'Unknown'),
                                    ingestion_date=datetime.now().strftime('%Y-%m-%d')
                                )
                            else:
                                logging.warning(f"Failed to generate summary using {api_name} API")
                        except requests.exceptions.ConnectionError:
                            requests.status_code = "Connection: "
                    elif api_name.lower() == "anthropic":
                        anthropic_api_key = api_key if api_key else config.get('API', 'anthropic_api_key',
                                                                               fallback=None)
                        try:
                            logging.debug(f"MAIN: Trying to summarize with anthropic")
                            summary = summarize_with_claude(anthropic_api_key, json_file_path, anthropic_model,
                                                            custom_prompt)
                        except requests.exceptions.ConnectionError:
                            requests.status_code = "Connection: "
                    elif api_name.lower() == "cohere":
                        cohere_api_key = api_key if api_key else config.get('API', 'cohere_api_key', fallback=None)
                        try:
                            logging.debug(f"MAIN: Trying to summarize with cohere")
                            summary = summarize_with_cohere(cohere_api_key, json_file_path, cohere_model, custom_prompt)
                        except requests.exceptions.ConnectionError:
                            requests.status_code = "Connection: "
                    elif api_name.lower() == "groq":
                        groq_api_key = api_key if api_key else config.get('API', 'groq_api_key', fallback=None)
                        try:
                            logging.debug(f"MAIN: Trying to summarize with Groq")
                            summary = summarize_with_groq(groq_api_key, json_file_path, groq_model, custom_prompt)
                        except requests.exceptions.ConnectionError:
                            requests.status_code = "Connection: "
                    elif api_name.lower() == "openrouter":
                        openrouter_api_key = api_key if api_key else config.get('API', 'openrouter_api_key',
                                                                                fallback=None)
                        try:
                            logging.debug(f"MAIN: Trying to summarize with OpenRouter")
                            summary = summarize_with_openrouter(openrouter_api_key, json_file_path, custom_prompt)
                        except requests.exceptions.ConnectionError:
                            requests.status_code = "Connection: "
                    elif api_name.lower() == "llama":
                        llama_token = api_key if api_key else config.get('API', 'llama_api_key', fallback=None)
                        llama_ip = llama_api_IP
                        try:
                            logging.debug(f"MAIN: Trying to summarize with Llama.cpp")
                            summary = summarize_with_llama(llama_ip, json_file_path, llama_token, custom_prompt)
                        except requests.exceptions.ConnectionError:
                            requests.status_code = "Connection: "
                    elif api_name.lower() == "kobold":
                        kobold_token = api_key if api_key else config.get('API', 'kobold_api_key', fallback=None)
                        kobold_ip = kobold_api_IP
                        try:
                            logging.debug(f"MAIN: Trying to summarize with kobold.cpp")
                            summary = summarize_with_kobold(kobold_ip, json_file_path, kobold_token, custom_prompt)
                        except requests.exceptions.ConnectionError:
                            requests.status_code = "Connection: "
                    elif api_name.lower() == "ooba":
                        ooba_token = api_key if api_key else config.get('API', 'ooba_api_key', fallback=None)
                        ooba_ip = ooba_api_IP
                        try:
                            logging.debug(f"MAIN: Trying to summarize with oobabooga")
                            summary = summarize_with_oobabooga(ooba_ip, json_file_path, ooba_token, custom_prompt)
                        except requests.exceptions.ConnectionError:
                            requests.status_code = "Connection: "
                    elif api_name.lower() == "tabbyapi":
                        tabbyapi_key = api_key if api_key else config.get('API', 'tabby_api_key', fallback=None)
                        tabbyapi_ip = tabby_api_IP
                        try:
                            logging.debug(f"MAIN: Trying to summarize with tabbyapi")
                            tabby_model = llm_model
                            summary = summarize_with_tabbyapi(tabby_api_key, tabby_api_IP, json_file_path, tabby_model,
                                                              custom_prompt)
                        except requests.exceptions.ConnectionError:
                            requests.status_code = "Connection: "
                    elif api_name.lower() == "vllm":
                        logging.debug(f"MAIN: Trying to summarize with VLLM")
                        summary = summarize_with_vllm(vllm_api_url, vllm_api_key, llm_model, json_file_path,
                                                      custom_prompt)
                    elif api_name.lower() == "local-llm":
                        logging.debug(f"MAIN: Trying to summarize with the local LLM, Mistral Instruct v0.2")
                        local_llm_url = "http://127.0.0.1:8080"
                        summary = summarize_with_local_llm(json_file_path, custom_prompt)
                    elif api_name.lower() == "huggingface":
                        huggingface_api_key = api_key if api_key else config.get('API', 'huggingface_api_key',
                                                                                 fallback=None)
                        try:
                            logging.debug(f"MAIN: Trying to summarize with huggingface")
                            summarize_with_huggingface(huggingface_api_key, json_file_path, custom_prompt)
                        except requests.exceptions.ConnectionError:
                            requests.status_code = "Connection: "

                    else:
                        logging.warning(f"Unsupported API: {api_name}")
                        summary = None

                    if summary:
                        transcription_result['summary'] = summary
                        logging.info(f"Summary generated using {api_name} API")
                        save_summary_to_file(summary, json_file_path)
                    # FIXME
                    # elif final_summary:
                    #     logging.info(f"Rolling summary generated using {api_name} API")
                    #     logging.info(f"Final Rolling summary is {final_summary}\n\n")
                    #     save_summary_to_file(final_summary, json_file_path)
                    else:
                        logging.warning(f"Failed to generate summary using {api_name} API")
                else:
                    logging.info("MAIN: #2 - No API specified. Summarization will not be performed")

                # Add media to the database
                add_media_with_keywords(
                    url=path,
                    title=info_dict.get('title', 'Untitled'),
                    media_type='video',
                    content=' '.join([segment['text'] for segment in segments]),
                    keywords=','.join(keywords),
                    prompt=custom_prompt or 'No prompt provided',
                    summary=summary or 'No summary provided',
                    transcription_model=whisper_model,
                    author=info_dict.get('uploader', 'Unknown'),
                    ingestion_date=datetime.now().strftime('%Y-%m-%d')
                )

        except Exception as e:
            logging.error(f"Error processing {path}: {str(e)}")
            logging.error(str(e))
            continue
        # end_time = time.monotonic()
        # print("Total program execution time: " + timedelta(seconds=end_time - start_time))

    return results


def signal_handler(signal, frame):
    logging.info('Signal received, exiting...')
    sys.exit(0)


############################## MAIN ##############################
#
#

if __name__ == "__main__":
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    # Establish logging baseline
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    print_hello()
    parser = argparse.ArgumentParser(
        description='Transcribe and summarize videos.',
        epilog='''
Sample commands:
    1. Simple Sample command structure:
        summarize.py <path_to_video> -api openai -k tag_one tag_two tag_three

    2. Rolling Summary Sample command structure:
        summarize.py <path_to_video> -api openai -prompt "custom_prompt_goes_here-is-appended-after-transcription" -roll -detail 0.01 -k tag_one tag_two tag_three

    3. FULL Sample command structure:
        summarize.py <path_to_video> -api openai -ns 2 -wm small.en -off 0 -vad -log INFO -prompt "custom_prompt" -overwrite -roll -detail 0.01 -k tag_one tag_two tag_three

    4. Sample command structure for UI:
        summarize.py -gui -log DEBUG
        ''',
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument('input_path', type=str, help='Path or URL of the video', nargs='?')
    parser.add_argument('-v', '--video', action='store_true', help='Download the video instead of just the audio')
    parser.add_argument('-api', '--api_name', type=str, help='API name for summarization (optional)')
    parser.add_argument('-key', '--api_key', type=str, help='API key for summarization (optional)')
    parser.add_argument('-ns', '--num_speakers', type=int, default=2, help='Number of speakers (default: 2)')
    parser.add_argument('-wm', '--whisper_model', type=str, default='small.en',
                        help='Whisper model (default: small.en)')
    parser.add_argument('-off', '--offset', type=int, default=0, help='Offset in seconds (default: 0)')
    parser.add_argument('-vad', '--vad_filter', action='store_true', help='Enable VAD filter')
    parser.add_argument('-log', '--log_level', type=str, default='INFO',
                        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'], help='Log level (default: INFO)')
    parser.add_argument('-gui', '--user_interface', action='store_true', help="Launch the Gradio user interface")
    parser.add_argument('-demo', '--demo_mode', action='store_true', help='Enable demo mode')
    parser.add_argument('-prompt', '--custom_prompt', type=str,
                        help='Pass in a custom prompt to be used in place of the existing one.\n (Probably should just '
                             'modify the script itself...)')
    parser.add_argument('-overwrite', '--overwrite', action='store_true', help='Overwrite existing files')
    parser.add_argument('-roll', '--rolling_summarization', action='store_true', help='Enable rolling summarization')
    parser.add_argument('-detail', '--detail_level', type=float, help='Mandatory if rolling summarization is enabled, '
                                                                      'defines the chunk  size.\n Default is 0.01(lots '
                                                                      'of chunks) -> 1.00 (few chunks)\n Currently '
                                                                      'only OpenAI works. ',
                        default=0.01, )
    # FIXME - This or time based...
    parser.add_argument('--chunk_duration', type=int, default=DEFAULT_CHUNK_DURATION,
                        help='Duration of each chunk in seconds')
    # FIXME - This or chunk_duration.... -> Maybe both???
    parser.add_argument('-time', '--time_based', type=int,
                        help='Enable time-based summarization and specify the chunk duration in seconds (minimum 60 seconds, increments of 30 seconds)')
    parser.add_argument('-model', '--llm_model', type=str, default='',
                        help='Model to use for LLM summarization (only used for vLLM/TabbyAPI)')
    parser.add_argument('-k', '--keywords', nargs='+', default=['cli_ingest_no_tag'],
                        help='Keywords for tagging the media, can use multiple separated by spaces (default: cli_ingest_no_tag)')
    parser.add_argument('--log_file', type=str, help='Where to save logfile (non-default)')
    parser.add_argument('--local_llm', action='store_true',
                        help="Use a local LLM from the script(Downloads llamafile from github and 'mistral-7b-instruct-v0.2.Q8' - 8GB model from Huggingface)")
    parser.add_argument('--server_mode', action='store_true',
                        help='Run in server mode (This exposes the GUI/Server to the network)')
    parser.add_argument('--share_public', type=int, default=7860,
                        help="This will use Gradio's built-in ngrok tunneling to share the server publicly on the internet. Specify the port to use (default: 7860)")
    parser.add_argument('--port', type=int, default=7860, help='Port to run the server on')
    #parser.add_argument('--offload', type=int, default=20, help='Numbers of layers to offload to GPU for Llamafile usage')
    # parser.add_argument('-o', '--output_path', type=str, help='Path to save the output file')

    args = parser.parse_args()
    if args.share_public:
        share_public = args.share_public
    else:
        share_public = None
    if args.server_mode:
        server_mode = args.server_mode
    else:
        server_mode = None
    if args.server_mode is True:
        server_mode = True
    if args.port:
        server_port = args.port
    else:
        server_port = None

    ########## Logging setup
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, args.log_level))

    # Create console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(getattr(logging, args.log_level))
    console_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(console_formatter)

    if args.log_file:
        # Create file handler
        file_handler = logging.FileHandler(args.log_file)
        file_handler.setLevel(getattr(logging, args.log_level))
        file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
        logger.info(f"Log file created at: {args.log_file}")

    ########## Custom Prompt setup
    custom_prompt = args.custom_prompt

    if not args.custom_prompt:
        logging.debug("No custom prompt defined, will use default")
        args.custom_prompt = (
            "\n\nabove is the transcript of a video. "
            "Please read through the transcript carefully. Identify the main topics that are "
            "discussed over the course of the transcript. Then, summarize the key points about each "
            "main topic in a concise bullet point. The bullet points should cover the key "
            "information conveyed about each topic in the video, but should be much shorter than "
            "the full transcript. Please output your bullet point summary inside <bulletpoints> "
            "tags."
        )
        print("No custom prompt defined, will use default")

        custom_prompt = args.custom_prompt
    else:
        logging.debug(f"Custom prompt defined, will use \n\nf{custom_prompt} \n\nas the prompt")
        print(f"Custom Prompt has been defined. Custom prompt: \n\n {args.custom_prompt}")

    # Check if the user wants to use the local LLM from the script
    local_llm = args.local_llm
    logging.info(f'Local LLM flag: {local_llm}')

    if args.user_interface:
        if local_llm:
            local_llm_function()
            time.sleep(2)
            webbrowser.open_new_tab('http://127.0.0.1:7860')
        launch_ui(demo_mode=False)
    else:
        if not args.input_path:
            parser.print_help()
            sys.exit(1)

        logging.info('Starting the transcription and summarization process.')
        logging.info(f'Input path: {args.input_path}')
        logging.info(f'API Name: {args.api_name}')
        logging.info(f'Number of speakers: {args.num_speakers}')
        logging.info(f'Whisper model: {args.whisper_model}')
        logging.info(f'Offset: {args.offset}')
        logging.info(f'VAD filter: {args.vad_filter}')
        logging.info(f'Log Level: {args.log_level}')
        logging.info(f'Demo Mode: {args.demo_mode}')
        logging.info(f'Custom Prompt: {args.custom_prompt}')
        logging.info(f'Overwrite: {args.overwrite}')
        logging.info(f'Rolling Summarization: {args.rolling_summarization}')
        logging.info(f'User Interface: {args.user_interface}')
        logging.info(f'Video Download: {args.video}')
        # logging.info(f'Save File location: {args.output_path}')
        # logging.info(f'Log File location: {args.log_file}')

        # Get all API keys from the config
        api_keys = {key: value for key, value in config.items('API') if key.endswith('_api_key')}

        api_name = args.api_name

        # Rolling Summarization will only be performed if an API is specified and the API key is available
        # and the rolling summarization flag is set
        #
        summary = None  # Initialize to ensure it's always defined
        if args.detail_level == None:
            args.detail_level = 0.01
        if args.api_name and args.rolling_summarization and any(
                key.startswith(args.api_name) and value is not None for key, value in api_keys.items()):
            logging.info(f'MAIN: API used: {args.api_name}')
            logging.info('MAIN: Rolling Summarization will be performed.')

        elif args.api_name:
            logging.info(f'MAIN: API used: {args.api_name}')
            logging.info('MAIN: Summarization (not rolling) will be performed.')

        else:
            logging.info('No API specified. Summarization will not be performed.')

        logging.debug("Platform check being performed...")
        platform_check()
        logging.debug("CUDA check being performed...")
        cuda_check()
        logging.debug("ffmpeg check being performed...")
        check_ffmpeg()

        llm_model = args.llm_model or None

        try:
            results = main(args.input_path, api_name=args.api_name,
                           api_key=args.api_key,
                           num_speakers=args.num_speakers,
                           whisper_model=args.whisper_model,
                           offset=args.offset,
                           vad_filter=args.vad_filter,
                           download_video_flag=args.video,
                           custom_prompt=args.custom_prompt,
                           overwrite=args.overwrite,
                           rolling_summarization=args.rolling_summarization,
                           detail=args.detail_level,
                           keywords=args.keywords,
                           chunk_summarization=False,
                           chunk_duration=None,
                           words_per_second=None,
                           llm_model=args.llm_model,
                           time_based=args.time_based,
                           set_chunk_txt_by_words=set_chunk_txt_by_words_,
                           set_max_txt_chunk_words=set_max_txt_chunk_words,
                           set_chunk_txt_by_sentences=set_chunk_txt_by_sentences,
                           set_max_txt_chunk_sentences=set_max_txt_chunk_sentences,
                           set_chunk_txt_by_paragraphs=set_chunk_txt_by_paragraphs,
                           set_max_txt_chunk_paragraphs=set_max_txt_chunk_paragraphs,
                           set_chunk_txt_by_tokens=set_chunk_txt_by_tokens,
                           set_max_txt_chunk_tokens=set_max_txt_chunk_tokens,
                           )

            logging.info('Transcription process completed.')
            atexit.register(cleanup_process)
        except Exception as e:
            logging.error('An error occurred during the transcription process.')
            logging.error(str(e))
            sys.exit(1)

        finally:
            cleanup_process()
