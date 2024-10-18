# Video_transcription_tab.py
# Description: This file contains the code for the video transcription tab in the Gradio UI.
#
# Imports
import json
import logging
import os
from datetime import datetime
from typing import Dict, Any

#
# External Imports
import gradio as gr
import yt_dlp
#
# Local Imports
from App_Function_Libraries.DB.DB_Manager import load_preset_prompts, add_media_to_database, \
    check_media_and_whisper_model, check_existing_media, update_media_content_with_version
from App_Function_Libraries.Gradio_UI.Gradio_Shared import whisper_models, update_user_prompt
from App_Function_Libraries.Gradio_UI.Gradio_Shared import error_handler
from App_Function_Libraries.Summarization.Summarization_General_Lib import perform_transcription, perform_summarization, \
    save_transcription_and_summary
from App_Function_Libraries.Utils.Utils import convert_to_seconds, safe_read_file, format_transcription, \
    create_download_directory, generate_unique_identifier, extract_text_from_segments
from App_Function_Libraries.Video_DL_Ingestion_Lib import parse_and_expand_urls, extract_metadata, download_video
from App_Function_Libraries.Benchmarks_Evaluations.ms_g_eval import run_geval
# Import metrics logging
from App_Function_Libraries.Metrics.metrics_logger import log_counter, log_histogram
#
#######################################################################################################################
#
# Functions:

def create_video_transcription_tab():
    with gr.TabItem("Video Transcription + Summarization", visible=True):
        gr.Markdown("# Transcribe & Summarize Videos from URLs")
        with gr.Row():
            gr.Markdown("""Follow this project at [tldw - GitHub](https://github.com/rmusser01/tldw)""")
        with gr.Row():
            gr.Markdown(
                """If you're wondering what all this is, please see the 'Introduction/Help' tab up above for more detailed information and how to obtain an API Key.""")
        with gr.Row():
            with gr.Column():
                url_input = gr.Textbox(label="URL(s) (Mandatory)",
                                       placeholder="Enter video URLs here, one per line. Supports YouTube, Vimeo, other video sites and Youtube playlists.",
                                       lines=5)
                video_file_input = gr.File(label="Upload Video File (Optional)", file_types=["video/*"])
                diarize_input = gr.Checkbox(label="Enable Speaker Diarization", value=False)
                vad_checkbox = gr.Checkbox(label="Enable Voice-Audio-Detection(VAD)", value=True)
                whisper_model_input = gr.Dropdown(choices=whisper_models, value="medium", label="Whisper Model")

                with gr.Row():
                    custom_prompt_checkbox = gr.Checkbox(label="Use a Custom Prompt",
                                                         value=False,
                                                         visible=True)
                    preset_prompt_checkbox = gr.Checkbox(label="Use a pre-set Prompt",
                                                         value=False,
                                                         visible=True)
                with gr.Row():
                    preset_prompt = gr.Dropdown(label="Select Preset Prompt",
                                                choices=load_preset_prompts(),
                                                visible=False)
                with gr.Row():
                    custom_prompt_input = gr.Textbox(label="Custom Prompt",
                                                     placeholder="Enter custom prompt here",
                                                     lines=3,
                                                     visible=False)
                with gr.Row():
                    system_prompt_input = gr.Textbox(label="System Prompt",
                                                     value="""<s>You are a bulleted notes specialist. [INST]```When creating comprehensive bulleted notes, you should follow these guidelines: Use multiple headings based on the referenced topics, not categories like quotes or terms. Headings should be surrounded by bold formatting and not be listed as bullet points themselves. Leave no space between headings and their corresponding list items underneath. Important terms within the content should be emphasized by setting them in bold font. Any text that ends with a colon should also be bolded. Before submitting your response, review the instructions, and make any corrections necessary to adhered to the specified format. Do not reference these instructions within the notes.``` \nBased on the content between backticks create comprehensive bulleted notes.[/INST]
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
""",
                                                     lines=3,
                                                     visible=False,
                                                     interactive=True)
                custom_prompt_checkbox.change(
                    fn=lambda x: (gr.update(visible=x), gr.update(visible=x)),
                    inputs=[custom_prompt_checkbox],
                    outputs=[custom_prompt_input, system_prompt_input]
                )
                preset_prompt_checkbox.change(
                    fn=lambda x: gr.update(visible=x),
                    inputs=[preset_prompt_checkbox],
                    outputs=[preset_prompt]
                )

                def update_prompts(preset_name):
                    prompts = update_user_prompt(preset_name)
                    return (
                        gr.update(value=prompts["user_prompt"], visible=True),
                        gr.update(value=prompts["system_prompt"], visible=True)
                    )

                preset_prompt.change(
                    update_prompts,
                    inputs=preset_prompt,
                    outputs=[custom_prompt_input, system_prompt_input]
                )

                api_name_input = gr.Dropdown(
                    choices=[None, "Local-LLM", "OpenAI", "Anthropic", "Cohere", "Groq", "DeepSeek", "Mistral",
                             "OpenRouter",
                             "Llama.cpp", "Kobold", "Ooba", "Tabbyapi", "VLLM", "ollama", "HuggingFace", "Custom-OpenAI-API"],
                    value=None, label="API Name (Mandatory)")
                api_key_input = gr.Textbox(label="API Key (Optional - Set in Config.txt)", placeholder="Enter your API key here",
                                           type="password")
                keywords_input = gr.Textbox(label="Keywords", placeholder="Enter keywords here (comma-separated)",
                                            value="default,no_keyword_set")
                batch_size_input = gr.Slider(minimum=1, maximum=10, value=1, step=1,
                                             label="Batch Size (Number of videos to process simultaneously)")
                timestamp_option = gr.Checkbox(label="Include Timestamps", value=True)
                keep_original_video = gr.Checkbox(label="Keep Original Video", value=False)
                # First, create a checkbox to toggle the chunking options
                chunking_options_checkbox = gr.Checkbox(label="Show Chunking Options", value=False)
                summarize_recursively = gr.Checkbox(label="Enable Recursive Summarization", value=False)
                use_cookies_input = gr.Checkbox(label="Use cookies for authenticated download", value=False)
                use_time_input = gr.Checkbox(label="Use Start and End Time", value=False)
                confab_checkbox = gr.Checkbox(label="Perform Confabulation Check of Summary", value=False)
                overwrite_checkbox = gr.Checkbox(label="Overwrite Existing Media", value=False)
                with gr.Row(visible=False) as time_input_box:
                    gr.Markdown("### Start and End time")
                    with gr.Column():
                        start_time_input = gr.Textbox(label="Start Time (Optional)",
                                                      placeholder="e.g., 1:30 or 90 (in seconds)")
                        end_time_input = gr.Textbox(label="End Time (Optional)",
                                                    placeholder="e.g., 5:45 or 345 (in seconds)")

                use_time_input.change(
                    fn=lambda x: gr.update(visible=x),
                    inputs=[use_time_input],
                    outputs=[time_input_box]
                )

                cookies_input = gr.Textbox(
                    label="User Session Cookies",
                    placeholder="Paste your cookies here (JSON format)",
                    lines=3,
                    visible=False
                )

                use_cookies_input.change(
                    fn=lambda x: gr.update(visible=x),
                    inputs=[use_cookies_input],
                    outputs=[cookies_input]
                )
                # Then, create a Box to group the chunking options
                with gr.Row(visible=False) as chunking_options_box:
                    gr.Markdown("### Chunking Options")
                    with gr.Column():
                        chunk_method = gr.Dropdown(choices=['words', 'sentences', 'paragraphs', 'tokens'],
                                                   label="Chunking Method")
                        max_chunk_size = gr.Slider(minimum=100, maximum=8000, value=400, step=1,
                                                   label="Max Chunk Size")
                        chunk_overlap = gr.Slider(minimum=0, maximum=5000, value=100, step=1, label="Chunk Overlap")
                        use_adaptive_chunking = gr.Checkbox(
                            label="Use Adaptive Chunking (Adjust chunking based on text complexity)")
                        use_multi_level_chunking = gr.Checkbox(label="Use Multi-level Chunking")
                        chunk_language = gr.Dropdown(choices=['english', 'french', 'german', 'spanish'],
                                                     label="Chunking Language")

                # Add JavaScript to toggle the visibility of the chunking options box
                chunking_options_checkbox.change(
                    fn=lambda x: gr.update(visible=x),
                    inputs=[chunking_options_checkbox],
                    outputs=[chunking_options_box]
                )
                process_button = gr.Button("Process Videos")

            with gr.Column():
                progress_output = gr.Textbox(label="Progress")
                error_output = gr.Textbox(label="Errors", visible=False)
                results_output = gr.HTML(label="Results")
                confabulation_output = gr.Textbox(label="Confabulation Check Results", visible=False)
                download_transcription = gr.File(label="Download All Transcriptions as JSON")
                download_summary = gr.File(label="Download All Summaries as Text")

            @error_handler
            def process_videos_with_error_handling(inputs, start_time, end_time, diarize, vad_use, whisper_model,
                                                   custom_prompt_checkbox, custom_prompt, chunking_options_checkbox,
                                                   chunk_method, max_chunk_size, chunk_overlap, use_adaptive_chunking,
                                                   use_multi_level_chunking, chunk_language, api_name,
                                                   api_key, keywords, use_cookies, cookies, batch_size,
                                                   timestamp_option, keep_original_video, summarize_recursively, overwrite_existing=False,
                                                   progress: gr.Progress = gr.Progress()) -> tuple:
                try:
                    # Start overall processing timer
                    proc_start_time = datetime.utcnow()
                    # FIXME - summarize_recursively is not being used...
                    logging.info("Entering process_videos_with_error_handling")
                    logging.info(f"Received inputs: {inputs}")

                    if not inputs:
                        raise ValueError("No inputs provided")

                    logging.debug("Input(s) is(are) valid")

                    # Ensure batch_size is an integer
                    try:
                        batch_size = int(batch_size)
                    except (ValueError, TypeError):
                        batch_size = 1  # Default to processing one video at a time if invalid

                    # Separate URLs and local files
                    urls = [input for input in inputs if
                            isinstance(input, str) and input.startswith(('http://', 'https://'))]
                    local_files = [input for input in inputs if
                                   isinstance(input, str) and not input.startswith(('http://', 'https://'))]

                    # Parse and expand URLs if there are any
                    expanded_urls = parse_and_expand_urls(urls) if urls else []

                    valid_local_files = []
                    invalid_local_files = []

                    for file_path in local_files:
                        if os.path.exists(file_path):
                            valid_local_files.append(file_path)
                        else:
                            invalid_local_files.append(file_path)
                            error_message = f"Local file not found: {file_path}"
                            logging.error(error_message)

                    if invalid_local_files:
                        logging.warning(f"Found {len(invalid_local_files)} invalid local file paths")
                        # FIXME - Add more complete error handling for invalid local files

                    all_inputs = expanded_urls + valid_local_files
                    logging.info(f"Total valid inputs to process: {len(all_inputs)} "
                                 f"({len(expanded_urls)} URLs, {len(valid_local_files)} local files)")

                    all_inputs = expanded_urls + local_files
                    logging.info(f"Total inputs to process: {len(all_inputs)}")
                    results = []
                    errors = []
                    results_html = ""
                    all_transcriptions = {}
                    all_summaries = ""

                    # Start timing
                    # FIXME - utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
                    start_proc = datetime.utcnow()

                    for i in range(0, len(all_inputs), batch_size):
                        batch = all_inputs[i:i + batch_size]
                        batch_results = []

                        for input_item in batch:
                            # Start individual video processing timer
                            video_start_time = datetime.utcnow()
                            try:
                                start_seconds = convert_to_seconds(start_time)
                                end_seconds = convert_to_seconds(end_time) if end_time else None

                                logging.info(f"Attempting to extract metadata for {input_item}")

                                if input_item.startswith(('http://', 'https://')):
                                    logging.info(f"Attempting to extract metadata for URL: {input_item}")
                                    video_metadata = extract_metadata(input_item, use_cookies, cookies)
                                    if not video_metadata:
                                        raise ValueError(f"Failed to extract metadata for {input_item}")
                                else:
                                    logging.info(f"Processing local file: {input_item}")
                                    video_metadata = {"title": os.path.basename(input_item), "url": input_item}

                                chunk_options = {
                                    'method': chunk_method,
                                    'max_size': max_chunk_size,
                                    'overlap': chunk_overlap,
                                    'adaptive': use_adaptive_chunking,
                                    'multi_level': use_multi_level_chunking,
                                    'language': chunk_language
                                } if chunking_options_checkbox else None

                                if custom_prompt_checkbox:
                                    custom_prompt = custom_prompt
                                else:
                                    custom_prompt = ("""
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

                                logging.debug("Gradio_Related.py: process_url_with_metadata being called")
                                # FIXME - Would assume this is where the multi-processing for recursive summarization would occur
                                result = process_url_with_metadata(
                                    input_item, 2, whisper_model,
                                    custom_prompt,
                                    start_seconds, api_name, api_key,
                                    vad_use, False, False, False, 0.01, None, keywords, None, diarize,
                                    end_time=end_seconds,
                                    include_timestamps=timestamp_option,
                                    metadata=video_metadata,
                                    use_chunking=chunking_options_checkbox,
                                    chunk_options=chunk_options,
                                    keep_original_video=keep_original_video,
                                    current_whisper_model=whisper_model,
                                    overwrite_existing=overwrite_existing
                                )

                                if result[0] is None:
                                    error_message = "Processing failed without specific error"
                                    batch_results.append(
                                        (input_item, error_message, "Error", video_metadata, None, None))
                                    errors.append(f"Error processing {input_item}: {error_message}")

                                    # Log failure metric
                                    log_counter(
                                        metric_name="videos_failed_total",
                                        labels={"whisper_model": whisper_model, "api_name": api_name},
                                        value=1
                                    )

                                else:
                                    url, transcription, summary, json_file, summary_file, result_metadata = result
                                    if transcription is None:
                                        error_message = f"Processing failed for {input_item}: Transcription is None"
                                        batch_results.append(
                                            (input_item, error_message, "Error", result_metadata, None, None))
                                        errors.append(error_message)

                                        # Log failure metric
                                        log_counter(
                                            metric_name="videos_failed_total",
                                            labels={"whisper_model": whisper_model, "api_name": api_name},
                                            value=1
                                        )

                                    else:
                                        batch_results.append(
                                            (input_item, transcription, "Success", result_metadata, json_file,
                                             summary_file))

                                        # Log success metric
                                        log_counter(
                                            metric_name="videos_processed_total",
                                            labels={"whisper_model": whisper_model, "api_name": api_name},
                                            value=1
                                        )

                                        # Calculate processing time
                                        video_end_time = datetime.utcnow()
                                        processing_time = (video_end_time - video_start_time).total_seconds()
                                        log_histogram(
                                            metric_name="video_processing_time_seconds",
                                            value=processing_time,
                                            labels={"whisper_model": whisper_model, "api_name": api_name}
                                        )

                                        # Log transcription and summary metrics
                                        if transcription:
                                            log_counter(
                                                metric_name="transcriptions_generated_total",
                                                labels={"whisper_model": whisper_model},
                                                value=1
                                            )
                                        if summary:
                                            log_counter(
                                                metric_name="summaries_generated_total",
                                                labels={"whisper_model": whisper_model},
                                                value=1
                                            )

                            except Exception as e:
                                # Log failure
                                log_counter(
                                    metric_name="videos_failed_total",
                                    labels={"whisper_model": whisper_model, "api_name": api_name},
                                    value=1
                                )
                                error_message = f"Error processing {input_item}: {str(e)}"
                                logging.error(error_message, exc_info=True)
                                batch_results.append((input_item, error_message, "Error", {}, None, None))
                                errors.append(error_message)

                        results.extend(batch_results)
                        logging.debug(f"Processed {len(batch_results)} videos in batch")
                        if isinstance(progress, gr.Progress):
                            progress((i + len(batch)) / len(all_inputs),
                                     f"Processed {i + len(batch)}/{len(all_inputs)} videos")

                    # Generate HTML for results
                    logging.debug(f"Generating HTML for {len(results)} results")
                    for url, transcription, status, metadata, json_file, summary_file in results:
                        if status == "Success":
                            title = metadata.get('title', 'Unknown Title')

                            # Check if transcription is a string (which it should be now)
                            if isinstance(transcription, str):
                                # Split the transcription into metadata and actual transcription
                                parts = transcription.split('\n\n', 1)
                                if len(parts) == 2:
                                    metadata_text, transcription_text = parts
                                else:
                                    metadata_text = "Metadata not found"
                                    transcription_text = transcription
                            else:
                                metadata_text = "Metadata format error"
                                transcription_text = "Transcription format error"

                            summary = safe_read_file(summary_file) if summary_file else "No summary available"

                            # FIXME - Add to other functions that generate HTML
                            # Format the transcription
                            formatted_transcription = format_transcription(transcription_text)
                            # Format the summary
                            formatted_summary = format_transcription(summary)

                            results_html += f"""
                            <div class="result-box">
                                <gradio-accordion>
                                    <gradio-accordion-item label="{title}">
                                        <p><strong>URL:</strong> <a href="{url}" target="_blank">{url}</a></p>
                                        <h4>Metadata:</h4>
                                        <pre>{metadata_text}</pre>
                                        <h4>Transcription:</h4>
                                        <div class="transcription" style="white-space: pre-wrap; word-wrap: break-word;">
                                            {formatted_transcription}
                                        </div>
                                        <h4>Summary:</h4>
                                        <div class="summary">{formatted_summary}</div>
                                    </gradio-accordion-item>
                                </gradio-accordion>
                            </div>
                            """
                            logging.debug(f"Transcription for {url}: {transcription[:200]}...")
                            all_transcriptions[url] = transcription
                            all_summaries += f"Title: {title}\nURL: {url}\n\n{metadata_text}\n\nTranscription:\n{transcription_text}\n\nSummary:\n{summary}\n\n---\n\n"
                        else:
                            results_html += f"""
                            <div class="result-box error">
                                <h3>Error processing {url}</h3>
                                <p>{transcription}</p>
                            </div>
                            """

                    # Save all transcriptions and summaries to files
                    logging.debug("Saving all transcriptions and summaries to files")
                    with open('all_transcriptions.json', 'w', encoding='utf-8') as f:
                        json.dump(all_transcriptions, f, indent=2, ensure_ascii=False)

                    with open('all_summaries.txt', 'w', encoding='utf-8') as f:
                        f.write(all_summaries)

                    error_summary = "\n".join(errors) if errors else "No errors occurred."

                    total_inputs = len(all_inputs)

                    # End overall processing timer
                    proc_end_time = datetime.utcnow()
                    total_processing_time = (proc_end_time - proc_start_time).total_seconds()
                    log_histogram(
                        metric_name="total_processing_time_seconds",
                        value=total_processing_time,
                        labels={"whisper_model": whisper_model, "api_name": api_name}
                    )

                    return (
                        f"Processed {total_inputs} videos. {len(errors)} errors occurred.",
                        error_summary,
                        results_html,
                        'all_transcriptions.json',
                        'all_summaries.txt'
                    )
                except Exception as e:
                    logging.error(f"Unexpected error in process_videos_with_error_handling: {str(e)}", exc_info=True)

                    # Log unexpected failure metric
                    log_counter(
                        metric_name="videos_failed_total",
                        labels={"whisper_model": whisper_model, "api_name": api_name},
                        value=1
                    )

                    return (
                        f"An unexpected error occurred: {str(e)}",
                        str(e),
                        "<div class='result-box error'><h3>Unexpected Error</h3><p>" + str(e) + "</p></div>",
                        None,
                        None
                    )

            def process_videos_wrapper(url_input, video_file, start_time, end_time, diarize, vad_use, whisper_model,
                                       custom_prompt_checkbox, custom_prompt, chunking_options_checkbox,
                                       chunk_method, max_chunk_size, chunk_overlap, use_adaptive_chunking,
                                       use_multi_level_chunking, chunk_language, summarize_recursively, api_name,
                                       api_key, keywords, use_cookies, cookies, batch_size,
                                       timestamp_option, keep_original_video, confab_checkbox, overwrite_existing=False):
                global result
                try:
                    logging.info("process_videos_wrapper(): process_videos_wrapper called")

                    # Define file paths
                    transcriptions_file = os.path.join('all_transcriptions.json')
                    summaries_file = os.path.join('all_summaries.txt')

                    # Delete existing files if they exist
                    for file_path in [transcriptions_file, summaries_file]:
                        try:
                            if os.path.exists(file_path):
                                os.remove(file_path)
                                logging.info(f"Deleted existing file: {file_path}")
                        except Exception as e:
                            logging.warning(f"Failed to delete file {file_path}: {str(e)}")

                    # Handle both URL input and file upload
                    inputs = []
                    if url_input:
                        inputs.extend([url.strip() for url in url_input.split('\n') if url.strip()])
                    if video_file is not None:
                        # Assuming video_file is a file object with a 'name' attribute
                        inputs.append(video_file.name)

                    if not inputs:
                        raise ValueError("No input provided. Please enter URLs or upload a video file.")

                    result = process_videos_with_error_handling(
                        inputs, start_time, end_time, diarize, vad_use, whisper_model,
                        custom_prompt_checkbox, custom_prompt, chunking_options_checkbox,
                        chunk_method, max_chunk_size, chunk_overlap, use_adaptive_chunking,
                        use_multi_level_chunking, chunk_language, api_name,
                        api_key, keywords, use_cookies, cookies, batch_size,
                        timestamp_option, keep_original_video, summarize_recursively, overwrite_existing
                    )

                    confabulation_result = None
                    if confab_checkbox:
                        logging.info("Confabulation check enabled")
                        # Assuming result[1] contains the transcript and result[2] contains the summary
                        confabulation_result = run_geval(result[1], result[2], api_key, api_name)
                        logging.info(f"Simplified G-Eval result: {confabulation_result}")

                    # Ensure that result is a tuple with 5 elements
                    if not isinstance(result, tuple) or len(result) != 5:
                        raise ValueError(
                            f"process_videos_wrapper(): Expected 5 outputs, but got {len(result) if isinstance(result, tuple) else 1}")

                    # Return the confabulation result along with other outputs
                    return (*result, confabulation_result)

                except Exception as e:
                    logging.error(f"process_videos_wrapper(): Error in process_videos_wrapper: {str(e)}", exc_info=True)
                    # Return a tuple with 6 elements in case of any error (including None for simple_geval_result)
                    return (
                        f"process_videos_wrapper(): An error occurred: {str(e)}",  # progress_output
                        str(e),  # error_output
                        f"<div class='error'>Error: {str(e)}</div>",  # results_output
                        None,  # download_transcription
                        None,  # download_summary
                        None  # simple_geval_result
                    )

            # FIXME - remove dead args for process_url_with_metadata
            @error_handler
            def process_url_with_metadata(input_item, num_speakers, whisper_model, custom_prompt, offset, api_name,
                                          api_key, vad_filter, download_video_flag, download_audio,
                                          rolling_summarization,
                                          detail_level, question_box, keywords, local_file_path, diarize, end_time=None,
                                          include_timestamps=True, metadata=None, use_chunking=False,
                                          chunk_options=None, keep_original_video=False, current_whisper_model="Blank", overwrite_existing=False):

                try:
                    logging.info(f"Starting process_url_metadata for URL: {input_item}")
                    # Create download path

                    download_path = create_download_directory("Video_Downloads")
                    logging.info(f"Download path created at: {download_path}")

                    # Initialize info_dict
                    info_dict = {}

                    # Handle URL or local file
                    if os.path.isfile(input_item):
                        video_file_path = input_item
                        unique_id = generate_unique_identifier(input_item)
                        # Extract basic info from local file
                        info_dict = {
                            'webpage_url': unique_id,
                            'title': os.path.basename(input_item),
                            'description': "Local file",
                            'channel_url': None,
                            'duration': None,
                            'channel': None,
                            'uploader': None,
                            'upload_date': None
                        }
                    else:
                        # Extract video information
                        with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
                            try:
                                full_info = ydl.extract_info(input_item, download=False)

                                # Create a safe subset of info to log
                                safe_info = {
                                    'title': full_info.get('title', 'No title'),
                                    'duration': full_info.get('duration', 'Unknown duration'),
                                    'upload_date': full_info.get('upload_date', 'Unknown upload date'),
                                    'uploader': full_info.get('uploader', 'Unknown uploader'),
                                    'view_count': full_info.get('view_count', 'Unknown view count')
                                }

                                logging.debug(f"Full info extracted for {input_item}: {safe_info}")
                            except Exception as e:
                                logging.error(f"Error extracting video info: {str(e)}")
                                return None, None, None, None, None, None

                        # Filter the required metadata
                        if full_info:
                            info_dict = {
                                'webpage_url': full_info.get('webpage_url', input_item),
                                'title': full_info.get('title'),
                                'description': full_info.get('description'),
                                'channel_url': full_info.get('channel_url'),
                                'duration': full_info.get('duration'),
                                'channel': full_info.get('channel'),
                                'uploader': full_info.get('uploader'),
                                'upload_date': full_info.get('upload_date')
                            }
                            logging.debug(f"Filtered info_dict: {info_dict}")
                        else:
                            logging.error("Failed to extract video information")
                            return None, None, None, None, None, None

                        # FIXME - MAKE SURE THIS WORKS WITH LOCAL FILES
                        # FIXME - Add a toggle to force processing even if media exists
                        # Check if media already exists in the database
                        logging.info("Checking if media already exists in the database...")
                        media_exists, reason = check_media_and_whisper_model(
                            title=info_dict.get('title'),
                            url=info_dict.get('webpage_url'),
                            current_whisper_model=current_whisper_model
                        )

                        if not media_exists:
                            logging.info(
                                f"process_url_with_metadata: Media does not exist in the database. Reason: {reason}")
                        else:
                            if "same whisper model" in reason:
                                logging.info(
                                    f"process_url_with_metadata: Skipping download and processing as media exists and uses the same Whisper model. Reason: {reason}")
                                return input_item, None, None, None, None, info_dict
                            else:
                                logging.info(
                                    f"process_url_with_metadata: Media found, but with a different Whisper model. Reason: {reason}")

                        # Download video/audio
                        logging.info("Downloading video/audio...")
                        video_file_path = download_video(input_item, download_path, full_info, download_video_flag,
                                                         current_whisper_model=current_whisper_model)
                        if video_file_path is None:
                            logging.info(
                                f"process_url_with_metadata: Download skipped for {input_item}. Media might already exist or be processed.")
                            return input_item, None, None, None, None, info_dict

                    # FIXME - add check for existing media with different whisper model for local files
                    # FIXME Check to make sure this works
                    media_exists, reason = check_media_and_whisper_model(
                        title=info_dict.get('title'),
                        url=info_dict.get('webpage_url'),
                        current_whisper_model=current_whisper_model
                    )
                    if not media_exists:
                        logging.info(
                            f"process_url_with_metadata: Media does not exist in the database. Reason: {reason}")
                    else:
                        if "same whisper model" in reason:
                            logging.info(
                                f"process_url_with_metadata: Skipping download and processing as media exists and uses the same Whisper model. Reason: {reason}")
                            return input_item, None, None, None, None, info_dict
                        else:
                            same_whisper_model = True
                            logging.info(
                                f"process_url_with_metadata: Media found, but with a different Whisper model. Reason: {reason}")

                    logging.info(f"process_url_with_metadata: Processing file: {video_file_path}")

                    # Perform transcription
                    logging.info("process_url_with_metadata: Starting transcription...")
                    audio_file_path, segments = perform_transcription(video_file_path, offset, whisper_model,
                                                                      vad_filter, diarize)

                    if audio_file_path is None or segments is None:
                        logging.error("process_url_with_metadata: Transcription failed or segments not available.")
                        return None, None, None, None, None, None

                    logging.info(f"process_url_with_metadata: Transcription completed. Number of segments: {len(segments)}")

                    # Add metadata to segments
                    segments_with_metadata = {
                        "metadata": info_dict,
                        "segments": segments
                    }

                    # Save segments with metadata to JSON file
                    segments_json_path = os.path.splitext(audio_file_path)[0] + ".segments.json"
                    with open(segments_json_path, 'w') as f:
                        json.dump(segments_with_metadata, f, indent=2)

                    # Delete the .wav file after successful transcription
                    files_to_delete = [audio_file_path]
                    for file_path in files_to_delete:
                        if file_path and os.path.exists(file_path):
                            try:
                                os.remove(file_path)
                                logging.info(f"process_url_with_metadata: Successfully deleted file: {file_path}")
                            except Exception as e:
                                logging.warning(f"process_url_with_metadata: Failed to delete file {file_path}: {str(e)}")

                    # Delete the mp4 file after successful transcription if not keeping original audio
                    # Modify the file deletion logic to respect keep_original_video
                    if not keep_original_video:
                        files_to_delete = [audio_file_path, video_file_path]
                        for file_path in files_to_delete:
                            if file_path and os.path.exists(file_path):
                                try:
                                    os.remove(file_path)
                                    logging.info(f"process_url_with_metadata: Successfully deleted file: {file_path}")
                                except Exception as e:
                                    logging.warning(f"process_url_with_metadata: Failed to delete file {file_path}: {str(e)}")
                    else:
                        logging.info(f"process_url_with_metadata: Keeping original video file: {video_file_path}")
                        logging.info(f"process_url_with_metadata: Keeping original audio file: {audio_file_path}")

                    # Process segments based on the timestamp option
                    if not include_timestamps:
                        segments = [{'Text': segment['Text']} for segment in segments]

                    logging.info(f"Segments processed for timestamp inclusion: {segments}")

                    # Extract text from segments
                    transcription_text = extract_text_from_segments(segments)

                    if transcription_text.startswith("Error:"):
                        logging.error(f"process_url_with_metadata: Failed to extract transcription: {transcription_text}")
                        return None, None, None, None, None, None

                    # Use transcription_text instead of segments for further processing
                    full_text_with_metadata = f"{json.dumps(info_dict, indent=2)}\n\n{transcription_text}"

                    logging.debug(f"process_url_with_metadata: Full text with metadata extracted: {full_text_with_metadata[:100]}...")

                    # Perform summarization if API is provided
                    summary_text = None
                    if api_name:
                        # API key resolution handled at base of function if none provided
                        api_key = api_key if api_key else None
                        logging.info(f"process_url_with_metadata: Starting summarization with {api_name}...")
                        summary_text = perform_summarization(api_name, full_text_with_metadata, custom_prompt, api_key)
                        if summary_text is None:
                            logging.error("Summarization failed.")
                            return None, None, None, None, None, None
                        logging.debug(f"process_url_with_metadata: Summarization completed: {summary_text[:100]}...")

                    # Save transcription and summary
                    logging.info("process_url_with_metadata: Saving transcription and summary...")
                    download_path = create_download_directory("Audio_Processing")
                    json_file_path, summary_file_path = save_transcription_and_summary(full_text_with_metadata,
                                                                                       summary_text,
                                                                                       download_path, info_dict)
                    logging.info(f"process_url_with_metadata: Transcription saved to: {json_file_path}")
                    logging.info(f"process_url_with_metadata: Summary saved to: {summary_file_path}")

                    # Prepare keywords for database
                    if isinstance(keywords, str):
                        keywords_list = [kw.strip() for kw in keywords.split(',') if kw.strip()]
                    elif isinstance(keywords, (list, tuple)):
                        keywords_list = keywords
                    else:
                        keywords_list = []
                    logging.info(f"process_url_with_metadata: Keywords prepared: {keywords_list}")

                    existing_media = check_existing_media(info_dict['webpage_url'])

                    if existing_media:
                        # Update existing media with new version
                        media_id = existing_media['id']
                        update_result = update_media_content_with_version(media_id, info_dict, full_text_with_metadata,
                                                                          custom_prompt, summary_text, whisper_model)
                        logging.info(f"process_url_with_metadata: {update_result}")
                    else:
                        # Add new media to database
                        add_result = add_media_to_database(info_dict['webpage_url'], info_dict, full_text_with_metadata,
                                                           summary_text,
                                                           keywords_list, custom_prompt, whisper_model)
                        logging.info(f"process_url_with_metadata: {add_result}")

                    return info_dict[
                        'webpage_url'], full_text_with_metadata, summary_text, json_file_path, summary_file_path, info_dict

                except Exception as e:
                    logging.error(f"Error in process_url_with_metadata: {str(e)}", exc_info=True)
                    return None, None, None, None, None, None

            def toggle_confabulation_output(checkbox_value):
                return gr.update(visible=checkbox_value)

            confab_checkbox.change(
                fn=toggle_confabulation_output,
                inputs=[confab_checkbox],
                outputs=[confabulation_output]
            )

            process_button.click(
                fn=process_videos_wrapper,
                inputs=[
                    url_input,
                    video_file_input,
                    start_time_input,
                    end_time_input,
                    diarize_input,
                    vad_checkbox,
                    whisper_model_input,
                    custom_prompt_checkbox,
                    custom_prompt_input,
                    chunking_options_checkbox,
                    chunk_method,
                    max_chunk_size,
                    chunk_overlap,
                    use_adaptive_chunking,
                    use_multi_level_chunking,
                    chunk_language,
                    summarize_recursively,
                    api_name_input,
                    api_key_input,
                    keywords_input,
                    use_cookies_input,
                    cookies_input,
                    batch_size_input,
                    timestamp_option,
                    keep_original_video,
                    confab_checkbox,
                    overwrite_checkbox
                ],
                outputs=[progress_output, error_output, results_output, download_transcription, download_summary, confabulation_output]
            )
