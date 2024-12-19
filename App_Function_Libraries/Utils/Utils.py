# Utils.py
#########################################
# General Utilities Library
# This library is used to hold random utilities used by various other libraries.
#
####
####################
# Function Categories
#
#     Config loading
#     Misc-Functions
#     File-saving Function Definitions
#     UUID-Functions
#     Sanitization/Verification Functions
#     DB Config Loading
#     File Handling Functions
#
#
####################
# Function List
#
# 1. extract_text_from_segments(segments: List[Dict]) -> str
# 2. download_file(url, dest_path, expected_checksum=None, max_retries=3, delay=5)
# 3. verify_checksum(file_path, expected_checksum)
# 4. create_download_directory(title)
# 5. sanitize_filename(filename)
# 6. normalize_title(title)
# 7.
#
####################
#
# Import necessary libraries
import chardet
import configparser
import hashlib
import json
import logging
import os
import re
import tempfile
import time
import uuid
from datetime import timedelta
from typing import Union, AnyStr
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
#
# Non-Local Imports
import requests
import unicodedata
from tqdm import tqdm
#
#######################################################################################################################
#
# Function Definitions

def extract_text_from_segments(segments, include_timestamps=True):
    logging.debug(f"Segments received: {segments}")
    logging.debug(f"Type of segments: {type(segments)}")

    def extract_text_recursive(data, include_timestamps):
        if isinstance(data, dict):
            text = data.get('Text', '')
            if include_timestamps and 'Time_Start' in data and 'Time_End' in data:
                return f"{data['Time_Start']:.2f}s - {data['Time_End']:.2f}s | {text}"
            for key, value in data.items():
                if key == 'Text':
                    return value
                elif isinstance(value, (dict, list)):
                    result = extract_text_recursive(value, include_timestamps)
                    if result:
                        return result
        elif isinstance(data, list):
            return '\n'.join(filter(None, [extract_text_recursive(item, include_timestamps) for item in data]))
        return None

    text = extract_text_recursive(segments, include_timestamps)

    if text:
        return text.strip()
    else:
        logging.error(f"Unable to extract text from segments: {segments}")
        return "Error: Unable to extract transcription"

#
#
#######################
# Temp file cleanup
#
# Global list to keep track of downloaded files
downloaded_files = []

def cleanup_downloads():
    """Function to clean up downloaded files when the server exits."""
    for file_path in downloaded_files:
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                print(f"Cleaned up file: {file_path}")
        except Exception as e:
            print(f"Error cleaning up file {file_path}: {e}")

#
#
#######################################################################################################################


#######################################################################################################################
# Config loading
#
def load_comprehensive_config():
    # Get the directory of the current script (Utils.py)
    current_dir = os.path.dirname(os.path.abspath(__file__))
    logging.debug(f"Current directory: {current_dir}")

    # Go up two levels to the project root directory (tldw)
    project_root = os.path.dirname(os.path.dirname(current_dir))
    logging.debug(f"Project root directory: {project_root}")

    # Construct the path to the config file
    config_path = os.path.join(project_root, 'Config_Files', 'config.txt')
    logging.debug(f"Config file path: {config_path}")

    # Check if the config file exists
    if not os.path.exists(config_path):
        logging.error(f"Config file not found at {config_path}")
        raise FileNotFoundError(f"Config file not found at {config_path}")

    # Read the config file
    config = configparser.ConfigParser()
    config.read(config_path)

    # Log the sections found in the config file
    logging.debug("load_comprehensive_config(): Sections found in config: {config.sections()}")

    return config


def get_project_root():
    """Get the absolute path to the project root directory."""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(current_dir))
    logging.debug(f"Project root: {project_root}")
    return project_root


def get_database_dir():
    """Get the absolute path to the database directory."""
    db_dir = os.path.join(get_project_root(), 'Databases')
    os.makedirs(db_dir, exist_ok=True)
    logging.debug(f"Database directory: {db_dir}")
    return db_dir


def get_database_path(db_name: str) -> str:
    """
    Get the full absolute path for a database file.
    Ensures the path is always within the Databases directory.
    """
    # Remove any directory traversal attempts
    safe_db_name = os.path.basename(db_name)
    path = os.path.join(get_database_dir(), safe_db_name)
    logging.debug(f"Database path for {safe_db_name}: {path}")
    return path


def get_project_relative_path(relative_path: Union[str, os.PathLike[AnyStr]]) -> str:
    """Convert a relative path to a path relative to the project root."""
    path = os.path.join(get_project_root(), str(relative_path))
    logging.debug(f"Project relative path for {relative_path}: {path}")
    return path

def get_chromadb_path():
    path = os.path.join(get_project_root(), 'Databases', 'chroma_db')
    logging.debug(f"ChromaDB path: {path}")
    return path

def ensure_directory_exists(path):
    """Ensure that a directory exists, creating it if necessary."""
    os.makedirs(path, exist_ok=True)

# FIXME - update to include prompt path in return statement
def load_and_log_configs():
    try:
        config = load_comprehensive_config()
        if config is None:
            logging.error("Config is None, cannot proceed")
            return None
        # API Keys
        anthropic_api_key = config.get('API', 'anthropic_api_key', fallback=None)
        logging.debug(
            f"Loaded Anthropic API Key: {anthropic_api_key[:5]}...{anthropic_api_key[-5:] if anthropic_api_key else None}")

        cohere_api_key = config.get('API', 'cohere_api_key', fallback=None)
        logging.debug(
            f"Loaded Cohere API Key: {cohere_api_key[:5]}...{cohere_api_key[-5:] if cohere_api_key else None}")

        groq_api_key = config.get('API', 'groq_api_key', fallback=None)
        logging.debug(f"Loaded Groq API Key: {groq_api_key[:5]}...{groq_api_key[-5:] if groq_api_key else None}")

        openai_api_key = config.get('API', 'openai_api_key', fallback=None)
        logging.debug(
            f"Loaded OpenAI API Key: {openai_api_key[:5]}...{openai_api_key[-5:] if openai_api_key else None}")

        huggingface_api_key = config.get('API', 'huggingface_api_key', fallback=None)
        logging.debug(
            f"Loaded HuggingFace API Key: {huggingface_api_key[:5]}...{huggingface_api_key[-5:] if huggingface_api_key else None}")

        openrouter_api_key = config.get('API', 'openrouter_api_key', fallback=None)
        logging.debug(
            f"Loaded OpenRouter API Key: {openrouter_api_key[:5]}...{openrouter_api_key[-5:] if openrouter_api_key else None}")

        deepseek_api_key = config.get('API', 'deepseek_api_key', fallback=None)
        logging.debug(
            f"Loaded DeepSeek API Key: {deepseek_api_key[:5]}...{deepseek_api_key[-5:] if deepseek_api_key else None}")

        mistral_api_key = config.get('API', 'mistral_api_key', fallback=None)
        logging.debug(
            f"Loaded Mistral API Key: {mistral_api_key[:5]}...{mistral_api_key[-5:] if mistral_api_key else None}")

        google_api_key = config.get('API', 'google_api_key', fallback=None)
        logging.debug(
            f"Loaded Google API Key: {google_api_key[:5]}...{google_api_key[-5:] if google_api_key else None}")

        elevenlabs_api_key = config.get('API', 'elevenlabs_api_key', fallback=None)
        logging.debug(
            f"Loaded elevenlabs API Key: {elevenlabs_api_key[:5]}...{elevenlabs_api_key[-5:] if elevenlabs_api_key else None}")

        # Models
        anthropic_model = config.get('API', 'anthropic_model', fallback='claude-3-sonnet-20240229')
        cohere_model = config.get('API', 'cohere_model', fallback='command-r-plus')
        groq_model = config.get('API', 'groq_model', fallback='llama3-70b-8192')
        openai_model = config.get('API', 'openai_model', fallback='gpt-4-turbo')
        huggingface_model = config.get('API', 'huggingface_model', fallback='CohereForAI/c4ai-command-r-plus')
        openrouter_model = config.get('API', 'openrouter_model', fallback='microsoft/wizardlm-2-8x22b')
        deepseek_model = config.get('API', 'deepseek_model', fallback='deepseek-chat')
        mistral_model = config.get('API', 'mistral_model', fallback='mistral-large-latest')
        google_model = config.get('API', 'google_model', fallback='gemini-1.5-pro')

        logging.debug(f"Loaded Anthropic Model: {anthropic_model}")
        logging.debug(f"Loaded Cohere Model: {cohere_model}")
        logging.debug(f"Loaded Groq Model: {groq_model}")
        logging.debug(f"Loaded OpenAI Model: {openai_model}")
        logging.debug(f"Loaded HuggingFace Model: {huggingface_model}")
        logging.debug(f"Loaded OpenRouter Model: {openrouter_model}")
        logging.debug(f"Loaded Deepseek Model: {deepseek_model}")
        logging.debug(f"Loaded Mistral Model: {mistral_model}")

        # Local-Models
        kobold_api_ip = config.get('Local-API', 'kobold_api_IP', fallback='http://127.0.0.1:5000/api/v1/generate')
        kobold_openai_api_IP = config.get('Local-API', 'kobold_openai_api_IP', fallback='http://127.0.0.1:5001/v1/chat/completions')
        kobold_api_key = config.get('Local-API', 'kobold_api_key', fallback='')

        llama_api_IP = config.get('Local-API', 'llama_api_IP', fallback='http://127.0.0.1:8080/v1/chat/completions')
        llama_api_key = config.get('Local-API', 'llama_api_key', fallback='')

        ooba_api_IP = config.get('Local-API', 'ooba_api_IP', fallback='http://127.0.0.1:5000/v1/chat/completions')
        ooba_api_key = config.get('Local-API', 'ooba_api_key', fallback='')

        tabby_api_IP = config.get('Local-API', 'tabby_api_IP', fallback='http://127.0.0.1:5000/api/v1/generate')
        tabby_api_key = config.get('Local-API', 'tabby_api_key', fallback=None)
        tabby_model = config.get('models', 'tabby_model', fallback=None)

        vllm_api_url = config.get('Local-API', 'vllm_api_IP', fallback='http://127.0.0.1:500/api/v1/chat/completions')
        vllm_api_key = config.get('Local-API', 'vllm_api_key', fallback=None)
        vllm_model = config.get('Local-API', 'vllm_model', fallback=None)

        ollama_api_url = config.get('Local-API', 'ollama_api_IP', fallback='http://127.0.0.1:11434/api/generate')
        ollama_api_key = config.get('Local-API', 'ollama_api_key', fallback=None)
        ollama_model = config.get('Local-API', 'ollama_model', fallback=None)

        aphrodite_api_url = config.get('Local-API', 'aphrodite_api_IP', fallback='http://127.0.0.1:8080/v1/chat/completions')
        aphrodite_api_key = config.get('Local-API', 'aphrodite_api_key', fallback='')

        custom_openai_api_key = config.get('API', 'custom_openai_api_key', fallback=None)
        custom_openai_api_url = config.get('API', 'custom_openai_url', fallback=None)
        logging.debug(
            f"Loaded Custom openai-like endpoint API Key: {custom_openai_api_key[:5]}...{custom_openai_api_key[-5:] if custom_openai_api_key else None}")

        logging.debug(f"Loaded Kobold API IP: {kobold_api_ip}")
        logging.debug(f"Loaded Llama API IP: {llama_api_IP}")
        logging.debug(f"Loaded Ooba API IP: {ooba_api_IP}")
        logging.debug(f"Loaded Tabby API IP: {tabby_api_IP}")
        logging.debug(f"Loaded VLLM API URL: {vllm_api_url}")

        # Retrieve default API choices from the configuration file
        default_api = config.get('API', 'default_api', fallback='openai')

        # Retrieve output paths from the configuration file
        output_path = config.get('Paths', 'output_path', fallback='results')
        logging.debug(f"Output path set to: {output_path}")

        # Retrieve processing choice from the configuration file
        processing_choice = config.get('Processing', 'processing_choice', fallback='cpu')
        logging.debug(f"Processing choice set to: {processing_choice}")

        # Retrieve Embedding model settings from the configuration file
        embedding_model = config.get('Embeddings', 'embedding_model', fallback='')
        logging.debug(f"Embedding model set to: {embedding_model}")
        embedding_provider = config.get('Embeddings', 'embedding_provider', fallback='')
        embedding_model = config.get('Embeddings', 'embedding_model', fallback='')
        onnx_model_path = config.get('Embeddings', 'onnx_model_path', fallback="./App_Function_Libraries/onnx_models/text-embedding-3-small.onnx")
        model_dir = config.get('Embeddings', 'model_dir', fallback="./App_Function_Libraries/onnx_models")
        embedding_api_url = config.get('Embeddings', 'embedding_api_url', fallback="http://localhost:8080/v1/embeddings")
        embedding_api_key = config.get('Embeddings', 'embedding_api_key', fallback='')
        chunk_size = config.get('Embeddings', 'chunk_size', fallback=400)
        overlap = config.get('Embeddings', 'overlap', fallback=200)

        # Prompts - FIXME
        prompt_path = config.get('Prompts', 'prompt_path', fallback='Databases/prompts.db')

        # Auto-Save Values
        save_character_chats = config.get('Auto-Save', 'save_character_chats', fallback='False')
        save_rag_chats = config.get('Auto-Save', 'save_rag_chats', fallback='False')

        # Local API Timeout
        local_api_timeout = config.get('Local-API', 'local_api_timeout', fallback='90')

        # TTS Settings
        # FIXME
        tts_provider = config.get('TTS-Settings', 'default_tts_provider', fallback='openai')
        tts_voice = config.get('TTS-Settings', 'default_tts_voice', fallback='shimmer')
        # Open AI TTS
        default_openai_tts_model = config.get('TTS-Settings', 'default_openai_tts_model', fallback='tts-1-hd')
        default_openai_tts_voice = config.get('TTS-Settings', 'default_openai_tts_voice', fallback='shimmer')
        default_openai_tts_speed = config.get('TTS-Settings', 'default_openai_tts_speed', fallback='1')
        # Google TTS
        # FIXME - FIX THESE DEFAULTS
        default_google_tts_model = config.get('TTS-Settings', 'default_google_tts_model', fallback='en')
        default_google_tts_voice = config.get('TTS-Settings', 'default_google_tts_voice', fallback='en')
        default_google_tts_speed = config.get('TTS-Settings', 'default_google_tts_speed', fallback='1')
        # ElevenLabs TTS
        default_eleven_tts_model = config.get('TTS-Settings', 'default_eleven_tts_model', fallback='FIXME')
        default_eleven_tts_voice = config.get('TTS-Settings', 'default_eleven_tts_voice', fallback='FIXME')
        default_eleven_tts_language_code = config.get('TTS-Settings', 'default_eleven_tts_language_code', fallback='FIXME')
        default_eleven_tts_voice_stability = config.get('TTS-Settings', 'default_eleven_tts_voice_stability', fallback='FIXME')
        default_eleven_tts_voice_similiarity_boost = config.get('TTS-Settings', 'default_eleven_tts_voice_similiarity_boost', fallback='FIXME')
        default_eleven_tts_voice_style = config.get('TTS-Settings', 'default_eleven_tts_voice_style', fallback='FIXME')
        default_eleven_tts_voice_use_speaker_boost = config.get('TTS-Settings', 'default_eleven_tts_voice_use_speaker_boost', fallback='FIXME')
        default_eleven_tts_output_format = config.get('TTS-Settings', 'default_eleven_tts_output_format',
                                                      fallback='mp3_44100_192')

        return {
            'api_keys': {
                'anthropic': anthropic_api_key,
                'cohere': cohere_api_key,
                'groq': groq_api_key,
                'openai': openai_api_key,
                'huggingface': huggingface_api_key,
                'openrouter': openrouter_api_key,
                'deepseek': deepseek_api_key,
                'mistral': mistral_api_key,
                'google': google_api_key,
                'kobold': kobold_api_key,
                'llama': llama_api_key,
                'ooba': ooba_api_key,
                'tabby': tabby_api_key,
                'vllm': vllm_api_key,
                'ollama': ollama_api_key,
                'aphrodite': aphrodite_api_key,
                'elevenlabs': elevenlabs_api_key,
                'custom_openai_api_key': custom_openai_api_key
            },
            'models': {
                'anthropic': anthropic_model,
                'cohere': cohere_model,
                'groq': groq_model,
                'openai': openai_model,
                'huggingface': huggingface_model,
                'openrouter': openrouter_model,
                'deepseek': deepseek_model,
                'mistral': mistral_model,
                'google': google_model,
                'vllm': vllm_model,
                'tabby': tabby_model,
                'ollama': ollama_model

            },
            'local_api_ip': {
                'kobold': kobold_api_ip,
                'kobold_openai': kobold_openai_api_IP,
                'llama': llama_api_IP,
                'ooba': ooba_api_IP,
                'tabby': tabby_api_IP,
                'vllm': vllm_api_url,
                'ollama': ollama_api_url,
                'aphrodite': aphrodite_api_url,
                'custom_openai_api_ip': custom_openai_api_url
            },
            'output_path': output_path,
            'processing_choice': processing_choice,
            'db_config': {
                'prompt_path': get_project_relative_path(config.get('Prompts', 'prompt_path', fallback='Databases/prompts.db')),
                'db_type': config.get('Database', 'type', fallback='sqlite'),
                'sqlite_path': get_project_relative_path(config.get('Database', 'sqlite_path', fallback='Databases/media_summary.db')),
                'elasticsearch_host': config.get('Database', 'elasticsearch_host', fallback='localhost'),
                'elasticsearch_port': config.getint('Database', 'elasticsearch_port', fallback=9200),
                'chroma_db_path': get_project_relative_path(config.get('Database', 'chroma_db_path', fallback='Databases/chroma.db'))
            },
            'embedding_config': {
                'embedding_provider': embedding_provider,
                'embedding_model': embedding_model,
                'onnx_model_path': onnx_model_path,
                'model_dir': model_dir,
                'embedding_api_url': embedding_api_url,
                'embedding_api_key': embedding_api_key,
                'chunk_size': chunk_size,
                'overlap': overlap
            },
            'auto-save': {
                'save_character_chats': save_character_chats,
                'save_rag_chats': save_rag_chats,
            },
            'default_api': default_api,
            'local_api_timeout': local_api_timeout,
            'tts_settings': {
                'tts_provider': tts_provider,
                'tts_voice': tts_voice,
                # OpenAI
                'default_openai_tts_voice': default_openai_tts_voice,
                'default_openai_tts_speed': default_openai_tts_speed,
                'default_openai_tts_model': default_openai_tts_model,
                # Google
                'default_google_tts_model': default_google_tts_model,
                'default_google_tts_voice': default_google_tts_voice,
                'default_google_tts_speed': default_google_tts_speed,
                # ElevenLabs
                'default_eleven_tts_model': default_eleven_tts_model,
                'default_eleven_tts_voice': default_eleven_tts_voice,
                'default_eleven_tts_language_code': default_eleven_tts_language_code,
                'default_eleven_tts_voice_stability': default_eleven_tts_voice_stability,
                'default_eleven_tts_voice_similiarity_boost': default_eleven_tts_voice_similiarity_boost,
                'default_eleven_tts_voice_style': default_eleven_tts_voice_style,
                'default_eleven_tts_voice_use_speaker_boost': default_eleven_tts_voice_use_speaker_boost,
                'default_eleven_tts_output_format': default_eleven_tts_output_format
                # GPT Sovi-TTS
            }
        }

    except Exception as e:
        logging.error(f"Error loading config: {str(e)}")
        return None


global_api_endpoints = ["anthropic", "cohere", "groq", "openai", "huggingface", "openrouter", "deepseek", "mistral", "google", "custom_openai_api", "llama", "ooba", "kobold", "tabby", "vllm", "ollama", "aphrodite"]

openai_tts_voices = ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]

# Setup Default API Endpoint
loaded_config_data = load_and_log_configs()
default_api_endpoint = loaded_config_data['default_api']

def format_api_name(api):
    name_mapping = {
        "openai": "OpenAI",
        "anthropic": "Anthropic",
        "cohere": "Cohere",
        "groq": "Groq",
        "huggingface": "HuggingFace",
        "openrouter": "OpenRouter",
        "deepseek": "DeepSeek",
        "mistral": "Mistral",
        "google": "Google",
        "custom_openai_api": "Custom-OpenAI-API",
        "llama": "Llama.cpp",
        "ooba": "Ooba",
        "kobold": "Kobold",
        "tabby": "Tabbyapi",
        "vllm": "VLLM",
        "ollama": "Ollama",
        "aphrodite": "Aphrodite"
    }
    return name_mapping.get(api, api.title())


print(f"Default API Endpoint: {default_api_endpoint}")

#
# End of Config loading
#######################################################################################################################


#######################################################################################################################
#
# Misc-Functions

# Log file
# logging.basicConfig(filename='debug-runtime.log', encoding='utf-8', level=logging.DEBUG)

def format_metadata_as_text(metadata):
    if not metadata:
        return "No metadata available"

    formatted_text = "Video Metadata:\n"
    for key, value in metadata.items():
        if value is not None:
            if isinstance(value, list):
                # Join list items with commas
                formatted_value = ", ".join(str(item) for item in value)
            elif key == 'upload_date' and len(str(value)) == 8:
                # Format date as YYYY-MM-DD
                formatted_value = f"{value[:4]}-{value[4:6]}-{value[6:]}"
            elif key in ['view_count', 'like_count']:
                # Format large numbers with commas
                formatted_value = f"{value:,}"
            elif key == 'duration':
                # Convert seconds to HH:MM:SS format
                hours, remainder = divmod(value, 3600)
                minutes, seconds = divmod(remainder, 60)
                formatted_value = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
            else:
                formatted_value = str(value)

            # Replace underscores with spaces in the key name
            formatted_key = key.replace('_', ' ').capitalize()
            formatted_text += f"{formatted_key}: {formatted_value}\n"
    return formatted_text.strip()

# # Example usage:
# example_metadata = {
#     'title': 'Sample Video Title',
#     'uploader': 'Channel Name',
#     'upload_date': '20230615',
#     'view_count': 1000000,
#     'like_count': 50000,
#     'duration': 3725,  # 1 hour, 2 minutes, 5 seconds
#     'tags': ['tag1', 'tag2', 'tag3'],
#     'description': 'This is a sample video description.'
# }
#
# print(format_metadata_as_text(example_metadata))


def convert_to_seconds(time_str):
    if not time_str:
        return 0

    # If it's already a number, assume it's in seconds
    if time_str.isdigit():
        return int(time_str)

    # Parse time string in format HH:MM:SS, MM:SS, or SS
    time_parts = time_str.split(':')
    if len(time_parts) == 3:
        return int(timedelta(hours=int(time_parts[0]),
                             minutes=int(time_parts[1]),
                             seconds=int(time_parts[2])).total_seconds())
    elif len(time_parts) == 2:
        return int(timedelta(minutes=int(time_parts[0]),
                             seconds=int(time_parts[1])).total_seconds())
    elif len(time_parts) == 1:
        return int(time_parts[0])
    else:
        raise ValueError(f"Invalid time format: {time_str}")

#
# End of Misc-Functions
#######################################################################################################################


#######################################################################################################################
#
# File-saving Function Definitions
def save_to_file(video_urls, filename):
    with open(filename, 'w') as file:
        file.write('\n'.join(video_urls))
    print(f"Video URLs saved to {filename}")


def save_segments_to_json(segments, file_name="transcription_segments.json"):
    """
    Save transcription segments to a JSON file.

    Parameters:
    segments (list): List of transcription segments
    file_name (str): Name of the JSON file to save (default: "transcription_segments.json")

    Returns:
    str: Path to the saved JSON file
    """
    # Ensure the Results directory exists
    os.makedirs("Results", exist_ok=True)

    # Full path for the JSON file
    json_file_path = os.path.join("Results", file_name)

    # Save segments to JSON file
    with open(json_file_path, 'w', encoding='utf-8') as json_file:
        json.dump(segments, json_file, ensure_ascii=False, indent=4)

    return json_file_path


def download_file(url, dest_path, expected_checksum=None, max_retries=3, delay=5):
    temp_path = dest_path + '.tmp'

    for attempt in range(max_retries):
        try:
            # Check if a partial download exists and get its size
            resume_header = {}
            if os.path.exists(temp_path):
                resume_header = {'Range': f'bytes={os.path.getsize(temp_path)}-'}

            response = requests.get(url, stream=True, headers=resume_header)
            response.raise_for_status()

            # Get the total file size from headers
            total_size = int(response.headers.get('content-length', 0))
            initial_pos = os.path.getsize(temp_path) if os.path.exists(temp_path) else 0

            mode = 'ab' if 'Range' in response.headers else 'wb'
            with open(temp_path, mode) as temp_file, tqdm(
                total=total_size, unit='B', unit_scale=True, desc=dest_path, initial=initial_pos, ascii=True
            ) as pbar:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:  # filter out keep-alive new chunks
                        temp_file.write(chunk)
                        pbar.update(len(chunk))

            # Verify the checksum if provided
            if expected_checksum:
                if not verify_checksum(temp_path, expected_checksum):
                    os.remove(temp_path)
                    raise ValueError("Downloaded file's checksum does not match the expected checksum")

            # Move the file to the final destination
            os.rename(temp_path, dest_path)
            print("Download complete and verified!")
            return dest_path

        except Exception as e:
            print(f"Attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                print(f"Retrying in {delay} seconds...")
                time.sleep(delay)
            else:
                print("Max retries reached. Download failed.")
                raise

def create_download_directory(title):
    base_dir = "Results"
    # Remove characters that are illegal in Windows filenames and normalize
    safe_title = normalize_title(title, preserve_spaces=False)
    logging.debug(f"{title} successfully normalized")
    session_path = os.path.join(base_dir, safe_title)
    if not os.path.exists(session_path):
        os.makedirs(session_path, exist_ok=True)
        logging.debug(f"Created directory for downloaded video: {session_path}")
    else:
        logging.debug(f"Directory already exists for downloaded video: {session_path}")
    return session_path


def safe_read_file(file_path):
    encodings = ['utf-8', 'utf-16', 'ascii', 'latin-1', 'iso-8859-1', 'cp1252', 'utf-8-sig']

    logging.info(f"Attempting to read file: {file_path}")

    try:
        with open(file_path, 'rb') as file:
            raw_data = file.read()
    except FileNotFoundError:
        logging.error(f"File not found: {file_path}")
        return f"File not found: {file_path}"
    except Exception as e:
        logging.error(f"An error occurred while reading the file: {e}")
        return f"An error occurred while reading the file: {e}"

    if not raw_data:
        logging.warning(f"File is empty: {file_path}")
        return ""

    # Use chardet to detect the encoding
    detected = chardet.detect(raw_data)
    if detected['encoding'] is not None:
        encodings.insert(0, detected['encoding'])
        logging.info(f"Detected encoding: {detected['encoding']}")

    for encoding in encodings:
        try:
            decoded_content = raw_data.decode(encoding)
            # Check if the content is mostly printable
            if sum(c.isprintable() for c in decoded_content) / len(decoded_content) > 0.95:
                logging.info(f"Successfully decoded file with encoding: {encoding}")
                return decoded_content
        except UnicodeDecodeError:
            logging.debug(f"Failed to decode with {encoding}")
            continue

    # If all decoding attempts fail, return the error message
    logging.error(f"Unable to decode the file {file_path}")
    return f"Unable to decode the file {file_path}"


#
# End of Files-saving Function Definitions
#######################################################################################################################


#######################################################################################################################
#
# UUID-Functions

def generate_unique_filename(base_path, base_filename):
    """Generate a unique filename by appending a counter if necessary."""
    filename = base_filename
    counter = 1
    while os.path.exists(os.path.join(base_path, filename)):
        name, ext = os.path.splitext(base_filename)
        filename = f"{name}_{counter}{ext}"
        counter += 1
    return filename


def generate_unique_identifier(file_path):
    filename = os.path.basename(file_path)
    timestamp = int(time.time())

    # Generate a hash of the file content
    hasher = hashlib.md5()
    with open(file_path, 'rb') as f:
        buf = f.read()
        hasher.update(buf)
    content_hash = hasher.hexdigest()[:8]  # Use first 8 characters of the hash

    return f"local:{timestamp}:{content_hash}:{filename}"

#
# End of UUID-Functions
#######################################################################################################################


#######################################################################################################################
#
# Sanitization/Verification Functions

# Helper function to validate URL format
def is_valid_url(url: str) -> bool:
    regex = re.compile(
        r'^(?:http|ftp)s?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}|'  # ...or ipv4
        r'\[?[A-F0-9]*:[A-F0-9:]+\]?)'  # ...or ipv6
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    return re.match(regex, url) is not None


def verify_checksum(file_path, expected_checksum):
    sha256_hash = hashlib.sha256()
    with open(file_path, 'rb') as f:
        for byte_block in iter(lambda: f.read(4096), b''):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest() == expected_checksum


def normalize_title(title, preserve_spaces=False):
    # Normalize the string to 'NFKD' form and encode to 'ascii' ignoring non-ascii characters
    title = unicodedata.normalize('NFKD', title).encode('ascii', 'ignore').decode('ascii')

    if preserve_spaces:
        # Replace special characters with underscores, but keep spaces
        title = re.sub(r'[^\w\s\-.]', '_', title)
    else:
        # Replace special characters and spaces with underscores
        title = re.sub(r'[^\w\-.]', '_', title)

    # Replace multiple consecutive underscores with a single underscore
    title = re.sub(r'_+', '_', title)

    # Replace specific characters with underscores
    title = title.replace('/', '_').replace('\\', '_').replace(':', '_').replace('"', '_').replace('*', '_').replace(
        '?', '_').replace(
        '<', '_').replace('>', '_').replace('|', '_')

    return title.strip('_')


def clean_youtube_url(url):
    parsed_url = urlparse(url)
    query_params = parse_qs(parsed_url.query)
    if 'list' in query_params:
        query_params.pop('list')
    cleaned_query = urlencode(query_params, doseq=True)
    cleaned_url = urlunparse(parsed_url._replace(query=cleaned_query))
    return cleaned_url

def sanitize_filename(filename):
    # Remove invalid characters and replace spaces with underscores
    sanitized = re.sub(r'[<>:"/\\|?*]', '', filename)
    sanitized = re.sub(r'\s+', ' ', sanitized).strip()
    return sanitized


def format_transcription(content):
    # Replace '\n' with actual line breaks
    content = content.replace('\\n', '\n')
    # Split the content by newlines first
    lines = content.split('\n')
    formatted_lines = []
    for line in lines:
        # Add extra space after periods for better readability
        line = line.replace('.', '. ').replace('.  ', '. ')

        # Split into sentences using a more comprehensive regex
        sentences = re.split('(?<=[.!?]) +', line)

        # Trim whitespace from each sentence and add a line break
        formatted_sentences = [sentence.strip() for sentence in sentences if sentence.strip()]

        # Join the formatted sentences
        formatted_lines.append(' '.join(formatted_sentences))

    # Join the lines with HTML line breaks
    formatted_content = '<br>'.join(formatted_lines)

    return formatted_content

def sanitize_user_input(message):
    """
    Removes or escapes '{{' and '}}' to prevent placeholder injection.

    Args:
        message (str): The user's message.

    Returns:
        str: Sanitized message.
    """
    # Replace '{{' and '}}' with their escaped versions
    message = re.sub(r'\{\{', '{ {', message)
    message = re.sub(r'\}\}', '} }', message)
    return message

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

#
# End of Sanitization/Verification Functions
#######################################################################################################################


#######################################################################################################################
#
# DB Config Loading


def get_db_config():
    # Get the directory of the current script
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # Go up two levels to the project root directory (tldw)
    project_root = os.path.dirname(os.path.dirname(current_dir))
    # Construct the path to the config file
    config_path = os.path.join(project_root, 'Config_Files', 'config.txt')
    # Read the config file
    config = configparser.ConfigParser()
    config.read(config_path)
    # Return the database configuration
    return {
        'type': config['Database']['type'],
        'sqlite_path': config.get('Database', 'sqlite_path', fallback='./Databases/media_summary.db'),
        'elasticsearch_host': config.get('Database', 'elasticsearch_host', fallback='localhost'),
        'elasticsearch_port': config.getint('Database', 'elasticsearch_port', fallback=9200)
    }

#
# End of DB Config Loading
#######################################################################################################################

def format_text_with_line_breaks(text):
    # Split the text into sentences and add line breaks
    sentences = text.replace('. ', '.<br>').replace('? ', '?<br>').replace('! ', '!<br>')
    return sentences

#######################################################################################################################
#
# File Handling Functions

# Track temp files for cleanup
temp_files = []

temp_file_paths = []

def save_temp_file(file):
    global temp_files
    temp_dir = tempfile.gettempdir()
    temp_path = os.path.join(temp_dir, file.name)
    with open(temp_path, 'wb') as f:
        f.write(file.read())
    temp_files.append(temp_path)
    return temp_path

def cleanup_temp_files():
    global temp_files
    for file_path in temp_files:
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                logging.info(f"Removed temporary file: {file_path}")
            except Exception as e:
                logging.error(f"Failed to remove temporary file {file_path}: {e}")
    temp_files.clear()

def generate_unique_id():
    return f"uploaded_file_{uuid.uuid4()}"

#
# End of File Handling Functions
#######################################################################################################################
