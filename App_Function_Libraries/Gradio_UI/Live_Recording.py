# Live_Recording.py
# Description: Gradio UI for live audio recording and transcription.
#
# Import necessary modules and functions
import logging
import os
import time

# External Imports
import gradio as gr
# Local Imports
from App_Function_Libraries.Audio.Audio_Transcription_Lib import (record_audio, speech_to_text, save_audio_temp,
                                                                  stop_recording)
from App_Function_Libraries.DB.DB_Manager import add_media_to_database
from App_Function_Libraries.Metrics.metrics_logger import log_counter, log_histogram
#
#######################################################################################################################
#
# Functions:

whisper_models = ["small", "medium", "small.en", "medium.en", "medium", "large", "large-v1", "large-v2", "large-v3",
                  "distil-large-v2", "distil-medium.en", "distil-small.en"]

def create_live_recording_tab():
    with gr.Tab("Live Recording and Transcription", visible=True):
        gr.Markdown("# Live Audio Recording and Transcription")
        with gr.Row():
            with gr.Column():
                duration = gr.Slider(minimum=1, maximum=8000, value=15, label="Recording Duration (seconds)")
                whisper_models_input = gr.Dropdown(choices=whisper_models, value="medium", label="Whisper Model")
                vad_filter = gr.Checkbox(label="Use VAD Filter")
                save_recording = gr.Checkbox(label="Save Recording")
                save_to_db = gr.Checkbox(label="Save Transcription to Database(Must be checked to save - can be checked afer transcription)", value=False)
                custom_title = gr.Textbox(label="Custom Title (for database)", visible=False)
                record_button = gr.Button("Start Recording")
                stop_button = gr.Button("Stop Recording")
            with gr.Column():
                output = gr.Textbox(label="Transcription", lines=10)
                audio_output = gr.Audio(label="Recorded Audio", visible=False)

        recording_state = gr.State(value=None)

        def start_recording(duration):
            log_counter("live_recording_start_attempt", labels={"duration": duration})
            p, stream, audio_queue, stop_event, audio_thread = record_audio(duration)
            log_counter("live_recording_start_success", labels={"duration": duration})
            return (p, stream, audio_queue, stop_event, audio_thread)

        def end_recording_and_transcribe(recording_state, whisper_model, vad_filter, save_recording, save_to_db, custom_title):
            log_counter("live_recording_end_attempt", labels={"model": whisper_model})
            start_time = time.time()

            if recording_state is None:
                log_counter("live_recording_end_error", labels={"error": "Recording hasn't started yet"})
                return "Recording hasn't started yet.", None

            p, stream, audio_queue, stop_event, audio_thread = recording_state
            audio_data = stop_recording(p, stream, audio_queue, stop_event, audio_thread)

            temp_file = save_audio_temp(audio_data)
            segments = speech_to_text(temp_file, whisper_model=whisper_model, vad_filter=vad_filter)
            transcription = "\n".join([segment["Text"] for segment in segments])

            if save_recording:
                log_counter("live_recording_saved", labels={"model": whisper_model})
            else:
                os.remove(temp_file)

            end_time = time.time() - start_time
            log_histogram("live_recording_end_duration", end_time, labels={"model": whisper_model})
            log_counter("live_recording_end_success", labels={"model": whisper_model})
            return transcription, temp_file if save_recording else None

        def save_transcription_to_db(transcription, custom_title):
            log_counter("save_transcription_to_db_attempt")
            start_time = time.time()
            if custom_title.strip() == "":
                custom_title = "Self-recorded Audio"

            try:
                url = "self_recorded"
                info_dict = {
                    "title": custom_title,
                    "uploader": "self-recorded",
                    "webpage_url": url
                }
                segments = [{"Text": transcription}]
                summary = ""
                keywords = ["self-recorded", "audio"]
                custom_prompt_input = ""
                whisper_model = "self-recorded"
                media_type = "audio"

                result = add_media_to_database(
                    url=url,
                    info_dict=info_dict,
                    segments=segments,
                    summary=summary,
                    keywords=keywords,
                    custom_prompt_input=custom_prompt_input,
                    whisper_model=whisper_model,
                    media_type=media_type
                )
                end_time = time.time() - start_time
                log_histogram("save_transcription_to_db_duration", end_time)
                log_counter("save_transcription_to_db_success")
                return f"Transcription saved to database successfully. {result}"
            except Exception as e:
                logging.error(f"Error saving transcription to database: {str(e)}")
                log_counter("save_transcription_to_db_error", labels={"error": str(e)})
                return f"Error saving transcription to database: {str(e)}"

        def update_custom_title_visibility(save_to_db):
            return gr.update(visible=save_to_db)

        record_button.click(
            fn=start_recording,
            inputs=[duration],
            outputs=[recording_state]
        )

        stop_button.click(
            fn=end_recording_and_transcribe,
            inputs=[recording_state, whisper_models_input, vad_filter, save_recording, save_to_db, custom_title],
            outputs=[output, audio_output]
        )

        save_to_db.change(
            fn=update_custom_title_visibility,
            inputs=[save_to_db],
            outputs=[custom_title]
        )

        gr.Button("Save to Database").click(
            fn=save_transcription_to_db,
            inputs=[output, custom_title],
            outputs=gr.Textbox(label="Database Save Status")
        )

#
# End of Functions
########################################################################################################################
