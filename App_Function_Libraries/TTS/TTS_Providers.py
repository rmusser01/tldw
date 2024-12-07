# TTS_Providers.py
# Description: This file contains the functions to allow for usage of different TTS providers.
#
# Imports
import os
import tempfile
from typing import List
# External Imports
import edge_tts
from elevenlabs import client as elevenlabs_client
import openai
#
# Local Imports
#
#######################################################################################################################
#
# Functions:

tts_providers = ["elevenlabs", "openai", "edge"]

def test_all_tts_providers():
    try:
        # Load configuration
        #config = load_config()

        # Override default TTS model to use edge for tests
        test_config = {"text_to_speech": {"default_tts_model": "edge"}}

        # Read input text from file
        with open(
                "tests/data/transcript_336aa9f955cd4019bc1287379a5a2820.txt", "r"
        ) as file:
            input_text = file.read()

        # Test ElevenLabs
        tts_elevenlabs = TextToSpeech(model="elevenlabs")
        elevenlabs_output_file = "tests/data/response_elevenlabs.mp3"
        tts_elevenlabs.convert_to_speech(input_text, elevenlabs_output_file)
        logger.info(
            f"ElevenLabs TTS completed. Output saved to {elevenlabs_output_file}"
        )

        # Test OpenAI
        tts_openai = TextToSpeech(model="openai")
        openai_output_file = "tests/data/response_openai.mp3"
        tts_openai.convert_to_speech(input_text, openai_output_file)
        logger.info(f"OpenAI TTS completed. Output saved to {openai_output_file}")

        # Test Edge
        tts_edge = TextToSpeech(model="edge")
        edge_output_file = "tests/data/response_edge.mp3"
        tts_edge.convert_to_speech(input_text, edge_output_file)
        logger.info(f"Edge TTS completed. Output saved to {edge_output_file}")

    except Exception as e:
        logger.error(f"An error occurred during text-to-speech conversion: {str(e)}")
        raise

#######################################################
#
# OpenAI TTS Provider Functions

def generate_audio_openai(text, voice, model):
    """OpenAI Text-to-Speech provider / Generate audio using OpenAI API."""
    # Provider-specific SSML tags
    openai_ssml_tags: List[str] = ['break', 'emphasis']

    # FIXME - Add API Key check + model loading
    # if api_key:
    #     openai.api_key = api_key
    # elif not openai.api_key:
    #     raise ValueError("OpenAI API key must be provided or set in environment")
    # self.model = model

    # FIXME - add check for model, voice, input values
    try:
        response = openai.audio.speech.create(
            model=model,
            voice=voice,
            input=text
        )
        return response.content
    except Exception as e:
        raise RuntimeError(f"Failed to generate audio: {str(e)}") from e

#
# End of OpenAI TTS Provider Functions
#######################################################


#######################################################
#
# MS Edge TTS Provider Functions

# https://github.com/rany2/edge-tts

def generate_audio_edge(text, voice, model=None, voice2=None):
    # Edge doesn't use a selectable model for TTS
    # FIXME - SSML tags
    common_ssml_tags = ['lang', 'p', 'phoneme', 's', 'sub']
    def generate_audio(self, text: str, voice: str, model: str, voice2: str = None) -> bytes:
        """Generate audio using Edge TTS."""
        import nest_asyncio
        import asyncio

        # Apply nest_asyncio to allow nested event loops
        nest_asyncio.apply()

        async def _generate():
            communicate = edge_tts.Communicate(text, voice)
            # Create a temporary file with proper context management
            with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as tmp_file:
                temp_path = tmp_file.name

            try:
                # Save audio to temporary file
                await communicate.save(temp_path)
                # Read the audio data
                with open(temp_path, 'rb') as f:
                    return f.read()
            finally:
                # Clean up temporary file
                if os.path.exists(temp_path):
                    os.remove(temp_path)

        # Use nest_asyncio to handle nested event loops
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(_generate())
    result = generate_audio(text, voice, model, voice2)
    return result

#
# End of MS Edge TTS Provider Functions
#######################################################


#######################################################
#
# ElvenLabs TTS Provider Functions

def generate_audio_elevenlabs(text, voice, model, voice2=None):
    """Generate audio using ElevenLabs API."""
    # FIXME - add check for config settings
    # FIXME - add check + load for API key
    # FIXME - add check + load for model, voice, input values
    # FIXME - add SSML tags

    elvenlabs_ssml_tags = ['lang', 'p', 'phoneme', 's', 'sub']

    # FIXME - IDE says '.generate' doesn't exist?
    audio = elevenlabs_client.generate(
        text=text,
        voice=voice,
        model=model
    )
    return b''.join(chunk for chunk in audio if chunk)

# End of ElvenLabs TTS Provider Functions
#######################################################


#######################################################
#
# Google Gemini TTS Provider Functions


#
# End of Google Gemini TTS Provider Functions
#######################################################

#
# End of TTS_Providers.py
#######################################################################################################################
