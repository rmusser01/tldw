# TTS_Providers.py
# Description: This file contains the functions to allow for usage of different TTS providers.
#
# Imports
import logging
import os
import tempfile
import uuid

#
# External Imports
import edge_tts
import requests
#
# Local Imports
from App_Function_Libraries.Utils.Utils import load_and_log_configs, loaded_config_data
#
#######################################################################################################################
#
# Functions:

#######################################################
#
# OpenAI TTS Provider Functions

# https://github.com/leokwsw/OpenAI-TTS-Gradio/blob/main/app.py
def generate_audio_openai(api_key, input_text, voice, model, response_format="mp3", output_file="speech.mp3"):
    """
    Generate audio using OpenAI's Text-to-Speech API.

    Args:
        api_key (str): OpenAI API key.
        input_text (str): Text input for speech synthesis.
        voice (str): Voice to use for the synthesis.
        model (str): Model to use for the synthesis (e.g., "tts-1").
        response_format (str): Format of the response audio file (default is "mp3").
        output_file (str): Name of the output file to save the audio.

    Returns:
        str: Path to the saved audio file if successful.

    Raises:
        ValueError: If required inputs are missing or invalid.
        RuntimeError: If the API request fails.
    """
    # Validate inputs
    loaded_config_data = load_and_log_configs()
    openai_api_key = api_key

    # API key validation
    try:
        if not openai_api_key:
            logging.info("OpenAI: API key not provided as parameter")
            logging.info("OpenAI: Attempting to use API key from config file")
            openai_api_key = loaded_config_data['api_keys']['openai']

        if not openai_api_key:
            logging.error("OpenAI: API key not found or is empty")
            return "OpenAI: API Key Not Provided/Found in Config file or is empty"

        logging.debug(f"OpenAI: Using API Key: {openai_api_key[:5]}...{openai_api_key[-5:]}")
    except Exception as e:
        logging.error(f"OpenAI: Error loading API Key: {str(e)}")
        return f"OpenAI: Error loading API Key: {str(e)}"

    # Input data handling
    try:
        if not input_text:
            raise ValueError("Text input is required.")
        logging.debug(f"OpenAI: Raw input data type: {type(input_text)}")
        logging.debug(f"OpenAI: Raw input data (first 500 chars): {str(input_text)[:500]}...")
    except Exception as e:
        logging.error(f"OpenAI: Error loading input text: {str(e)}")
        return f"OpenAI: Error loading input text: {str(e)}"

    # Voice selection handling
    try:
        if not voice:
            logging.info("OpenAI: Speaker Voice not provided as parameter")
            logging.info("OpenAI: Attempting to use Speaker Voice from config file")
            voice = loaded_config_data['tts_settings']['default_openai_tts_voice']

        if not voice:
            raise ValueError("Voice is required. Default voice not found in config file and no voice selection was passed.")
    except Exception as e:
        logging.error(f"OpenAI: Error loading Speaker Voice: {str(e)}")
        return f"OpenAI: Error loading Speaker Voice: {str(e)}"

    # Model selection handling
    try:
        if not model:
            logging.info("OpenAI: Model not provided as parameter")
            logging.info("OpenAI: Attempting to use Model from config file")
            model = loaded_config_data['tts_settings']['default_openai+tts_model']

        if not model:
            raise ValueError("Model is required. Default model not found in config and no model selection was passed.")
    except Exception as e:
        logging.error(f"OpenAI: Error Selecting Model: {str(e)}")
        return f"OpenAI: Error Selecting Model: {str(e)}"

    # API endpoint
    endpoint = "https://api.openai.com/v1/audio/speech"

    # Headers for the API request
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    # Payload for the API request
    payload = {
        "model": model,
        "input": input_text,
        "voice": voice,
    }

    try:
        # Make the request to the API
        response = requests.post(endpoint, headers=headers, json=payload, stream=True)
        response.raise_for_status()  # Raise an error for HTTP status codes >= 400

        # Save the audio response to a file
        with open(output_file, "wb") as f:
            f.write(response.content)

        print(f"Audio successfully generated and saved to {output_file}.")
        return output_file

    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"Failed to generate audio: {str(e)}") from e


def test_generate_audio_openai(api_key, input_text, voice, model, response_format="mp3", output_file="speech.mp3"):
    try:
        if not api_key:
            logging.info("OpenAI: API key not provided as parameter")
            logging.info("OpenAI: Attempting to use API key from config file")
            openai_api_key = loaded_config_data['api_keys']['openai']

        if not api_key:
            logging.error("OpenAI: API key not found or is empty")
            return "OpenAI: API Key Not Provided/Found in Config file or is empty"

        logging.debug(f"OpenAI: Using API Key: {api_key[:5]}...{api_key[-5:]}")
    except Exception as e:
        logging.error(f"OpenAI: Error loading API Key: {str(e)}")
        return f"OpenAI: Error loading API Key: {str(e)}"

    input_text = "The quick brown fox jumped over the lazy dog."

    voice = "alloy"

    model = "tts-1"

    try:
        output_file = generate_audio_openai(api_key, input_text, voice, model)
        print(f"Generated audio file: {output_file}")
    except Exception as e:
        print(f"Error: {e}")

#
# End of OpenAI TTS Provider Functions
#######################################################


#######################################################
#
# MS Edge TTS Provider Functions - NOPE
#
# # https://github.com/rany2/edge-tts
#
# def generate_audio_edge(text, voice, model=None, voice2=None):
#     # FIXME - SSML tags
#     common_ssml_tags = ['lang', 'p', 'phoneme', 's', 'sub']
#     def generate_audio(self, text: str, voice: str, model: str, voice2: str = None) -> bytes:
#         """Generate audio using Edge TTS."""
#         import nest_asyncio
#         import asyncio
#
#         # Apply nest_asyncio to allow nested event loops
#         nest_asyncio.apply()
#
#         async def _generate():
#             communicate = edge_tts.Communicate(text, voice)
#             # Create a temporary file with proper context management
#             with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as tmp_file:
#                 temp_path = tmp_file.name
#
#             try:
#                 # Save audio to temporary file
#                 await communicate.save(temp_path)
#                 # Read the audio data
#                 with open(temp_path, 'rb') as f:
#                     return f.read()
#             finally:
#                 # Clean up temporary file
#                 if os.path.exists(temp_path):
#                     os.remove(temp_path)
#
#         # Use nest_asyncio to handle nested event loops
#         loop = asyncio.get_event_loop()
#         return loop.run_until_complete(_generate())
#     result = generate_audio(text, voice, model, voice2)
#     return result

#
# End of MS Edge TTS Provider Functions
#######################################################


#######################################################
#
# ElvenLabs TTS Provider Functions
# FIXME - all of this

#https://elevenlabs.io/docs/api-reference/text-to-speech
def generate_audio_elevenlabs(input_text, voice, model=None, api_key=None):
    """Generate audio using ElevenLabs API."""
    CHUNK_SIZE = 1024
    # API key validation
    elevenlabs_api_key = api_key
    try:
        if not elevenlabs_api_key:
            logging.info("ElevenLabs: API key not provided as parameter")
            logging.info("ElevenLabs: Attempting to use API key from config file")
            elevenlabs_api_key = loaded_config_data['api_keys']['elevenlabs']

        if not elevenlabs_api_key:
            logging.error("ElevenLabs: API key not found or is empty")
            return "ElevenLabs: API Key Not Provided/Found in Config file or is empty"

        logging.debug(f"ElevenLabs: Using API Key: {elevenlabs_api_key[:5]}...{elevenlabs_api_key[-5:]}")
    except Exception as e:
        logging.error(f"ElevenLabs: Error loading API Key: {str(e)}")
        return f"ElevenLabs: Error loading API Key: {str(e)}"

    # Input data handling
    try:
        if not input_text:
            raise ValueError("Text input is required.")
        logging.debug(f"ElevenLabs: Raw input data type: {type(input_text)}")
        logging.debug(f"ElevenLabs: Raw input data (first 500 chars): {str(input_text)[:500]}...")
    except Exception as e:
        logging.error(f"ElevenLabs: Error loading input text: {str(e)}")
        return f"ElevenLabs: Error loading input text: {str(e)}"

    # Handle Voice ID
    try:
        if not voice:
            logging.info("ElevenLabs: Speaker ID(Voice) not provided as parameter")
            logging.info("ElevenLabs: Attempting to use Speaker ID(Voice) from config file")
            voice = loaded_config_data['tts_settings']['default_eleven_tts_voice']

        if not voice:
            raise ValueError("Voice is required. Default voice not found in config file and no voice selection was passed.")
    except Exception as e:
        logging.error(f"ElevenLabs: Error loading Speaker ID(Voice): {str(e)}")
        return f"ElevenLabs: Error loading Speaker ID(Voice): {str(e)}"

    # Handle Model ID/Selection
    # Set Voice Model
    model="eleven_turbo_v2_5", # use the turbo model for low latency
    try:
        if not model:
            logging.info("ElevenLabs: Model not provided as parameter")
            logging.info("ElevenLabs: Attempting to use Model from config file")
            model = loaded_config_data['tts_settings']['default_eleven_tts_model']

        if not model:
            raise ValueError("Model is required. Default model not found in config file and no model selection was passed.")
    except Exception as e:
        logging.error(f"ElevenLabs: Error Selecting Model: {str(e)}")
        return f"ElevenLabs: Error Selecting Model: {str(e)}"

    # FIXME - add SSML tags

    # File output (non-streaming)
    output_format="mp3_22050_32",

    # Set the parameters for the TTS conversion
    try:
        default_eleven_tts_voice_stability = loaded_config_data['tts_settings'].get('default_eleven_tts_voice_stability', 0.0)
    except Exception as e:
        logging.error(f"ElevenLabs: Error loading Stability: {str(e)}")
        return f"ElevenLabs: Error loading Stability: {str(e)}"

    try:
        # Similarity Boost
        default_eleven_tts_voice_similiarity_boost = loaded_config_data['tts_settings'].get('default_eleven_tts_voice_similiarity_boost', 1.0)
    except Exception as e:
        logging.error(f"ElevenLabs: Error loading Similarity Boost: {str(e)}")
        return f"ElevenLabs: Error loading Similarity Boost: {str(e)}"

    try:
        # Style
        default_eleven_tts_voice_style = loaded_config_data['tts_settings'].get('default_eleven_tts_voice_style', 0.0)
    except Exception as e:
        logging.error(f"ElevenLabs: Error loading Style: {str(e)}")
        return f"ElevenLabs: Error loading Style: {str(e)}"

    try:
        # Use Speaker Boost
        default_eleven_tts_voice_use_speaker_boost = loaded_config_data['tts_settings'].get('default_eleven_tts_voice_use_speaker_boost', True)
    except Exception as e:
        logging.error(f"ElevenLabs: Error loading Use Speaker Boost: {str(e)}")
        return f"ElevenLabs: Error loading Use Speaker Boost: {str(e)}"

    try:
        # Output Format
        default_eleven_tts_output_format = loaded_config_data['tts_settings'].get('default_eleven_tts_output_format', "mp3_44100_192")
    except Exception as e:
        logging.error(f"ElevenLabs: Error loading Output Format: {str(e)}")
        return f"ElevenLabs: Error loading Output Format: {str(e)}"

    # Make the API request
    # Construct the URL for the Text-to-Speech API request
    tts_url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice}/stream?output_format=mp3_44100_192"

    # Set up headers for the API request, including the API key for authentication
    headers = {
        "Accept": "application/json",
        "xi-api-key": elevenlabs_api_key
    }

    # Set up the data payload for the API request, including the text and voice settings
    data = {
        "text": input_text,
        "model_id": model,
        "output_format": default_eleven_tts_output_format,
        "voice_settings": {
            "stability": default_eleven_tts_voice_stability,
            "similarity_boost": default_eleven_tts_voice_similiarity_boost,
            "style": default_eleven_tts_voice_style,
            "use_speaker_boost": default_eleven_tts_voice_use_speaker_boost
        }
    }
    try:
        # Make the POST request to the TTS API with headers and data, enabling streaming response
        with requests.post(tts_url, headers=headers, json=data, stream=True) as response:
            # Check if the request was successful
            if response.ok:
                # Create a temporary file - FIXME
                with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp_file:
                    # Read the response in chunks and write to the file
                    for chunk in response.iter_content(chunk_size=CHUNK_SIZE):
                        tmp_file.write(chunk)
                    temp_file_path = tmp_file.name
                # Inform the user of success
                print(f"Audio stream saved successfully to {temp_file_path}.")
            if not response.ok:
                logging.error(f"API request failed: {response.status_code} - {response.text}")
                return f"API request failed: {response.status_code} - {response.text}"
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"Failed to generate audio: {str(e)}") from e

    save_file_path = f"{uuid.uuid4()}.mp3"

    # Writing the audio to a file
    with open(save_file_path, "wb") as f:
        for chunk in response:
            if chunk:
                f.write(chunk)

    print(f"{save_file_path}: A new audio file was saved successfully!")

    # Return the path of the saved audio file
    return save_file_path

# End of ElvenLabs TTS Provider Functions
#######################################################


#######################################################
#
# Google Gemini TTS Provider Functions

# https://github.com/google-gemini/cookbook/blob/main/quickstarts/Audio.ipynb
# Fuck google. lets wait for their docs to not be complete fucking shit.

#
# End of Google Gemini TTS Provider Functions
#######################################################


#######################################################
#
# gpt-soviTTS TTS Provider Functions
# https://github.com/RVC-Boss/GPT-SoVITS

#
# End of gpt-soviTTS TTS Provider Functions
#######################################################

#
# End of TTS_Providers.py
#######################################################################################################################
