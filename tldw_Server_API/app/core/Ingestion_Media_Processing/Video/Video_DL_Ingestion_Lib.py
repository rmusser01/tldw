# Video_DL_Ingestion_Lib.py
#########################################
# Video Downloader and Ingestion Library
# This library is used to handle downloading videos from YouTube and other platforms.
# It also handles the ingestion of the videos into the database.
# It uses yt-dlp to extract video information and download the videos.
####
import json
####################
# Function List
#
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
####################
# Import necessary libraries to run solo for testing
import os
import re
import sys
import tempfile
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any
from urllib.parse import urlparse, parse_qs

# 3rd-Party Imports
import yt_dlp
import unicodedata
# Import Local
from tldw_Server_API.app.core.Evaluations.ms_g_eval import run_geval
from tldw_Server_API.app.core.Utils.Utils import (
    convert_to_seconds,
    generate_unique_identifier,
    extract_text_from_segments,
    logging
)
from tldw_Server_API.app.core.Utils.Chunk_Lib import improved_chunking_process
from tldw_Server_API.app.core.Metrics.metrics_logger import (
    log_counter, log_histogram
)
#
#######################################################################################################################
# Function Definitions
#

def normalize_title(title):
    # Normalize the string to 'NFKD' form and encode to 'ascii' ignoring non-ascii characters
    title = unicodedata.normalize('NFKD', title).encode('ascii', 'ignore').decode('ascii')
    title = title.replace('/', '_').replace('\\', '_').replace(':', '_').replace('"', '').replace('*', '').replace('?',
                                                                                                                   '').replace(
        '<', '').replace('>', '').replace('|', '')
    return title

def get_video_info(url: str) -> dict:
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'skip_download': True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info_dict = ydl.extract_info(url, download=False)
            return info_dict
        except Exception as e:
            logging.error(f"Error extracting video info: {e}")
            return None


def get_youtube(video_url):
    ydl_opts = {
        'format': 'bestaudio[ext=m4a]',
        'noplaylist': False,
        'quiet': True,
        'extract_flat': True
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        logging.debug("About to extract youtube info")
        info_dict = ydl.extract_info(video_url, download=False)
        logging.debug("Youtube info successfully extracted")
    return info_dict


def get_playlist_videos(playlist_url):
    ydl_opts = {
        'extract_flat': True,
        'skip_download': True,
        'quiet': True
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(playlist_url, download=False)

        if 'entries' in info:
            video_urls = [entry['url'] for entry in info['entries']]
            playlist_title = info['title']
            return video_urls, playlist_title
        else:
            print("No videos found in the playlist.")
            return [], None


def download_video(video_url, download_path, info_dict, download_video_flag, current_whisper_model):
    global video_file_path, ffmpeg_path
    global audio_file_path

    # Normalize Video Title name
    logging.debug("About to normalize downloaded video title")
    if 'title' not in info_dict or 'ext' not in info_dict:
        logging.error("info_dict is missing 'title' or 'ext'")
        return None

    normalized_video_title = normalize_title(info_dict['title'])
    video_file_path = os.path.join(download_path, f"{normalized_video_title}.{info_dict['ext']}")

    # Check for existence of video file
    if os.path.exists(video_file_path):
        logging.info(f"Video file already exists: {video_file_path}")
        return video_file_path

    # Setup path handling for ffmpeg on different OSs
    if sys.platform.startswith('win'):
        ffmpeg_path = os.path.join(os.getcwd(), 'Bin', 'ffmpeg.exe')
    elif sys.platform.startswith('linux'):
        ffmpeg_path = 'ffmpeg'
    elif sys.platform.startswith('darwin'):
        ffmpeg_path = 'ffmpeg'

    if download_video_flag:
        video_file_path = os.path.join(download_path, f"{normalized_video_title}.mp4")
        ydl_opts_video = {
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]',
            'outtmpl': video_file_path,
            'ffmpeg_location': ffmpeg_path
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts_video) as ydl:
                logging.debug("yt_dlp: About to download video with youtube-dl")
                ydl.download([video_url])
                logging.debug("yt_dlp: Video successfully downloaded with youtube-dl")
                if os.path.exists(video_file_path):
                    return video_file_path
                else:
                    logging.error("yt_dlp: Video file not found after download")
                    return None
        except Exception as e:
            logging.error(f"yt_dlp: Error downloading video: {e}")
            return None
    elif not download_video_flag:
        video_file_path = os.path.join(download_path, f"{normalized_video_title}.mp4")
        # Set options for video and audio
        ydl_opts = {
            'format': 'bestaudio[ext=m4a]',
            'quiet': True,
            'outtmpl': video_file_path
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                logging.debug("yt_dlp: About to download video with youtube-dl")
                ydl.download([video_url])
                logging.debug("yt_dlp: Video successfully downloaded with youtube-dl")
                if os.path.exists(video_file_path):
                    return video_file_path
                else:
                    logging.error("yt_dlp: Video file not found after download")
                    return None
        except Exception as e:
            logging.error(f"yt_dlp: Error downloading video: {e}")
            return None

    else:
        logging.debug("download_video: Download video flag is set to False and video file path is not found")
        return None


def extract_video_info(url):
    try:
        with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
            info = ydl.extract_info(url, download=False)

            # Log only a subset of the info to avoid overwhelming the logs
            log_info = {
                'title': info.get('title'),
                'duration': info.get('duration'),
                'upload_date': info.get('upload_date')
            }
            logging.debug(f"Extracted info for {url}: {log_info}")

            return info
    except Exception as e:
        logging.error(f"Error extracting video info for {url}: {str(e)}", exc_info=True)
        return None


def get_youtube_playlist_urls(playlist_id):
    ydl_opts = {
        'extract_flat': True,
        'quiet': True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        result = ydl.extract_info(f'https://www.youtube.com/playlist?list={playlist_id}', download=False)
        return [entry['url'] for entry in result['entries'] if entry.get('url')]


def parse_and_expand_urls(urls):
    logging.info(f"Starting parse_and_expand_urls with input: {urls}")
    expanded_urls = []

    for url in urls:
        try:
            logging.info(f"Processing URL: {url}")
            parsed_url = urlparse(url)
            logging.debug(f"Parsed URL components: {parsed_url}")

            # YouTube playlist handling
            if 'youtube.com' in parsed_url.netloc and 'list' in parsed_url.query:
                playlist_id = parse_qs(parsed_url.query)['list'][0]
                logging.info(f"Detected YouTube playlist with ID: {playlist_id}")
                playlist_urls = get_youtube_playlist_urls(playlist_id)
                logging.info(f"Expanded playlist URLs: {playlist_urls}")
                expanded_urls.extend(playlist_urls)

            # YouTube short URL handling
            elif 'youtu.be' in parsed_url.netloc:
                video_id = parsed_url.path.lstrip('/')
                full_url = f'https://www.youtube.com/watch?v={video_id}'
                logging.info(f"Expanded YouTube short URL to: {full_url}")
                expanded_urls.append(full_url)

            # Vimeo handling
            elif 'vimeo.com' in parsed_url.netloc:
                video_id = parsed_url.path.lstrip('/')
                full_url = f'https://vimeo.com/{video_id}'
                logging.info(f"Processed Vimeo URL: {full_url}")
                expanded_urls.append(full_url)

            # Add more platform-specific handling here

            else:
                logging.info(f"URL not recognized as special case, adding as-is: {url}")
                expanded_urls.append(url)

        except Exception as e:
            logging.error(f"Error processing URL {url}: {str(e)}", exc_info=True)
            # Optionally, you might want to add the problematic URL to expanded_urls
            # expanded_urls.append(url)

    logging.info(f"Final expanded URLs: {expanded_urls}")
    return expanded_urls


def extract_metadata(url, use_cookies=False, cookies=None):
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'extract_flat': True,
        'skip_download': True,
    }

    if use_cookies and cookies:
        try:
            cookie_dict = json.loads(cookies)
            ydl_opts['cookiefile'] = cookie_dict
        except json.JSONDecodeError:
            logging.warning("Invalid cookie format. Proceeding without cookies.")

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(url, download=False)
            metadata = {
                'title': info.get('title'),
                'uploader': info.get('uploader'),
                'upload_date': info.get('upload_date'),
                'view_count': info.get('view_count'),
                'like_count': info.get('like_count'),
                'duration': info.get('duration'),
                'tags': info.get('tags'),
                'description': info.get('description')
            }

            # Create a safe subset of metadata to log
            safe_metadata = {
                'title': metadata.get('title', 'No title'),
                'duration': metadata.get('duration', 'Unknown duration'),
                'upload_date': metadata.get('upload_date', 'Unknown upload date'),
                'uploader': metadata.get('uploader', 'Unknown uploader')
            }

            logging.info(f"Successfully extracted metadata for {url}: {safe_metadata}")
            return metadata
        except Exception as e:
            logging.error(f"Error extracting metadata for {url}: {str(e)}", exc_info=True)
            return None


def generate_timestamped_url(url, hours, minutes, seconds):
    # Extract video ID from the URL
    video_id_match = re.search(r'(?:v=|)([0-9A-Za-z_-]{11}).*', url)
    if not video_id_match:
        return "Invalid YouTube URL"

    video_id = video_id_match.group(1)

    # Calculate total seconds
    total_seconds = int(hours) * 3600 + int(minutes) * 60 + int(seconds)

    # Generate the new URL
    new_url = f"https://www.youtube.com/watch?v={video_id}&t={total_seconds}s"

    return new_url


# New FastAPI ingestion functions
def process_videos(
    inputs: List[str],
    start_time: Optional[str],
    end_time: Optional[str],
    diarize: bool,
    vad_use: bool,
    transcription_model: str,
    transcription_language: Optional[str],
    custom_prompt: Optional[str],
    system_prompt: Optional[str],
    perform_chunking: bool,
    chunk_method: Optional[str],
    max_chunk_size: int,
    chunk_overlap: int,
    use_adaptive_chunking: bool,
    use_multi_level_chunking: bool,
    chunk_language: Optional[str],
    summarize_recursively: bool,
    api_name: Optional[str],
    api_key: Optional[str],
    use_cookies: bool,
    cookies: Optional[str],
    timestamp_option: bool,
    perform_confabulation_check: bool, # Renamed from confab_checkbox
    temp_dir: Optional[str] = None, # Added temp_dir argument
    # keep_original: bool = False, # Add if needed for intermediate files
) -> Dict[str, Any]:
    """
    Processes multiple videos or local file paths, transcribes, summarizes,
    and optionally stores in the DB (if store_in_db=True).

    This function was adapted from your old `process_videos_with_error_handling()`
    but with Gradio references removed.

    :param inputs: A list of either URLs or local file paths.
    :param start_time: Start time for partial transcription (e.g. "1:30" or "90").
    :param end_time: End time for partial transcription.
    :param diarize: Enable speaker diarization.
    :param vad_use: Enable Voice Activity Detection.
    :param transcription_model: Name of the transcription model to use.
    :param custom_prompt: The user’s custom text prompt for summarization.
    :param system_prompt: The system prompt for the LLM.
    :param perform_chunking: If True, break transcripts into chunks before summarizing.
    :param chunk_method: "words", "sentences", etc.
    :param max_chunk_size: Maximum chunk size for chunking.
    :param chunk_overlap: Overlap size for chunking.
    :param use_adaptive_chunking: Whether to adapt chunk sizes by text complexity.
    :param use_multi_level_chunking: If True, chunk in multiple passes.
    :param chunk_language: The language for chunking logic.
    :param summarize_recursively: If True, do multi-pass summarization of chunk summaries.
    :param api_name: The LLM API name (e.g., "openai").
    :param api_key: The user’s (or system) API key for the LLM.
    :param use_cookies: If True, use cookies for authenticated video downloads.
    :param cookies: The user-supplied cookies in JSON or Netscape format.
    :param timestamp_option: If True, keep timestamps in final transcript.
    :param confab_checkbox: If True, run confabulation check on the summary.
    :return: A dict with the overall results, e.g.:
             {
               "processed_count": int,
               "errors_count": int,
               "errors": [...],
               "results": [...],
               "confabulation_results": "..."
             }
    """
    logging.info(f"Starting process_videos (DB-agnostic) for {len(inputs)} inputs.")
    errors = []
    results = []
    all_transcripts_for_confab = {} # Renamed for clarity
    all_summaries_for_confab = {} # Renamed for clarity

    # Save all transcriptions and summaries to these dict/strings:
    all_transcriptions = {}
    all_summaries = ""

    # Convert user times to seconds
    start_seconds = convert_to_seconds(start_time) if start_time else 0
    end_seconds = convert_to_seconds(end_time) if end_time else None

    # If user typed no inputs, bail out
    if not inputs:
        logging.warning("No input provided to process_videos()")
        return {
            "processed_count": 0,
            "errors_count": 1,
            "errors": ["No inputs provided."],
            "results": []
        }

    processing_temp_dir = Path(temp_dir) if temp_dir else Path(tempfile.gettempdir()) / f"video_proc_{uuid.uuid4().hex[:8]}"
    if not temp_dir: # If API didn't provide one, create it (less ideal)
        processing_temp_dir.mkdir(parents=True, exist_ok=True)
        # Note: If created here, cleanup responsibility is less clear. Better to rely on API layer's TempDirManager.
        logging.warning(f"process_videos created its own temp dir: {processing_temp_dir}. Cleanup may not be guaranteed.")

    for video_input in inputs:
        video_start_time = datetime.now()
        try:
            # Pass necessary parameters down, including temp_dir
            single_result = process_single_video(
                video_input=video_input,
                start_seconds=start_seconds,
                end_seconds=end_seconds, # Pass end_seconds down
                diarize=diarize,
                vad_use=vad_use,
                transcription_model=transcription_model,
                transcription_language=transcription_language,
                custom_prompt=custom_prompt,
                system_prompt=system_prompt,
                perform_chunking=perform_chunking,
                chunk_method=chunk_method,
                max_chunk_size=max_chunk_size,
                chunk_overlap=chunk_overlap,
                use_adaptive_chunking=use_adaptive_chunking,
                use_multi_level_chunking=use_multi_level_chunking,
                chunk_language=chunk_language,
                summarize_recursively=summarize_recursively,
                api_name=api_name,
                api_key=api_key,
                use_cookies=use_cookies,
                cookies=cookies,
                timestamp_option=timestamp_option,
                temp_dir=str(processing_temp_dir), # Pass temp dir path
                # keep_intermediate_audio=keep_original, # Pass if needed
            )
            if single_result["status"] == "Success":
                # Append to results list
                results.append(single_result)

            results.append(single_result) # Append regardless of status

            if single_result.get("status") == "Success":
                log_counter(...) # Metrics are fine if DB-free

                # Prepare for potential confabulation check
                transcript_text = single_result.get("transcript", "") # Use 'transcript' key returned by single
                summary_text = single_result.get("summary", "") # Use 'summary' key returned by single
                if transcript_text and summary_text:
                     all_transcripts_for_confab[video_input] = transcript_text
                     all_summaries_for_confab[video_input] = summary_text

                # Logging the timing
                video_end_time = datetime.now()
                processing_time = (video_end_time - video_start_time).total_seconds()
                log_histogram(
                    metric_name="video_processing_time_seconds",
                    value=processing_time,
                    labels={"whisper_model": transcription_model, "api_name": (api_name or "none")}
                )
            else:
                # If status is "Error"
                errors.append(single_result["error"])
                results.append(single_result)

                # Log failure metric
                log_counter(
                    metric_name="videos_failed_total",
                    labels={"whisper_model": transcription_model, "api_name": (api_name or "none")},
                    value=1
                )
        except Exception as exc:
            msg = f"Exception processing '{video_input}': {exc}"
            logging.error(msg, exc_info=True)
            errors.append(msg)
            # Append an error result structure
            results.append({
                "status": "Error",
                "input_ref": video_input,
                "processing_source": video_input,
                "media_type": "video",
                "error": msg,
                # Fill other fields with None/defaults
                "metadata": {}, "transcript": None, "segments": None, "chunks": None, "summary": None,
                "analysis_details": None, "warnings": None
            })
            log_counter("videos_failed_total", ...)

            # Log failure metric
            log_counter(
                metric_name="videos_failed_total",
                labels={"whisper_model": transcription_model, "api_name": (api_name or 'none')},
                value=1
            )

    # Optionally, run a confabulation check on the entire set of summaries
    confabulation_results = None
    if confabulation_results and all_transcriptions:
        confab_results = []
        # Process each transcript-summary pair individually for g_eval check
        for url, transcript in all_transcriptions.items():
            # Extract the corresponding summary for this URL
            url_pattern = f"Video Input: {re.escape(url)}\nTranscription:.*?\nSummary:\n(.*?)\n\n---\n\n"
            summary_match = re.search(url_pattern, all_summaries, re.DOTALL)

            if summary_match:
                # FIXME - validate this call
                individual_summary = summary_match.group(1)
                # Create single-item collections for this transcript-summary pair
                single_transcript_dict = f"URL: + {url} : {transcript}"
                single_summary = f"Video Input: {url}\nTranscription:\n{transcript}\n\nSummary:\n{individual_summary}\n\n"

                # Run g_eval on this single pair
                pair_result = run_geval(single_transcript_dict, single_summary, api_key, api_name)
                confab_results.append(f"URL: {url} - {pair_result}")
            else:
                logging.warning(f"Could not find matching summary for URL: {url}")

        confabulation_results = f"Confabulation checks completed:\n" + "\n".join(confab_results)

    # Remove temp dir ONLY if it was created here (less ideal)
    # if not temp_dir and processing_temp_dir.exists():
    #     try: shutil.rmtree(processing_temp_dir)
    #     except Exception as e: logging.warning(f"Failed to clean up self-created temp dir {processing_temp_dir}: {e}")

    return {
        "processed_count": sum(1 for r in results if r.get("status") == "Success"), # Count only success
        "errors_count": sum(1 for r in results if r.get("status") == "Error"),
        "warnings_count": sum(1 for r in results if r.get("status") == "Warning"), # Optional: track warnings
        "errors": errors, # Collect specific error messages
        "results": results, # Return the list of individual result dicts
        "confabulation_results": confabulation_results
    }


def process_single_video(
    video_input: str,
    start_seconds: int,
    end_seconds: Optional[int], # Added end_seconds
    diarize: bool,
    vad_use: bool,
    transcription_model: str,
        transcription_language: Optional[str],
    custom_prompt: Optional[str],
    system_prompt: Optional[str],
    perform_chunking: bool,
    chunk_method: Optional[str],
    max_chunk_size: int,
    chunk_overlap: int,
    use_adaptive_chunking: bool,
    use_multi_level_chunking: bool,
    chunk_language: Optional[str],
    summarize_recursively: bool,
    api_name: Optional[str],
    api_key: Optional[str],
    use_cookies: bool,
    cookies: Optional[str],
    timestamp_option: bool,
    temp_dir: str, # Expect temp_dir path
    keep_intermediate_audio: bool = False # Add flag if needed
) -> Dict[str, Any]:
    """
    Processes a single video/file: Extracts metadata, transcribes, optionally summarizes.
    **DOES NOT interact with the database.**
    Returns a dict matching MediaItemProcessResponse structure (using 'transcript' and 'summary' keys).
    """
    # Initialize result structure (closer to MediaItemProcessResponse)
    processing_result = {
        "status": "Pending",
        "input_ref": video_input, # Use 'input_ref' for consistency
        "processing_source": video_input,
        "media_type": "video",
        "metadata": {},
        "content": "",
        "segments": None,
        "chunks": None,
        "analysis": None,
        "analysis_details": {},
        "error": None,
        "warnings": [], # Initialize as list
    }
    audio_file_path_to_clean = None # Track intermediate file

    try:
        logging.info(f"Processing single video input (DB-agnostic): {video_input}")

        # Distinguish remote vs. local
        is_remote = video_input.startswith(("http://", "https://"))
        processing_temp_dir = Path(temp_dir) # Use the provided temp dir

        # If is_remote, get metadata from extract_metadata
        info_dict: Dict[str, Any] = {}

        # 1. Get Metadata & Determine Processing Source
        if is_remote:
            # Use your existing extract_metadata or yt-dlp directly here
            # Assume info_dict = extract_metadata(video_input, use_cookies, cookies)
            # Assume download_path = download_video_if_needed(video_input, ...) # Needs refactoring too
            # Let's simplify for now: Assume transcription handles download/path
            processing_source = video_input # Placeholder - transcription needs the actual path
            info_dict = extract_metadata(video_input, use_cookies, cookies) # Keep metadata extraction
            if not info_dict:
                raise ValueError(f"Failed to extract metadata for URL: {video_input}")
            processing_result["metadata"] = info_dict
            # Note: The actual download/file access happens in transcription library
            processing_source_for_transcription = video_input # Pass URL or path
        else:
            # Local file
            if not os.path.exists(video_input):
                raise FileNotFoundError(f"Local file not found: {video_input}")
            processing_source_for_transcription = video_input
            # Create minimal metadata for local files
            info_dict = {
                "id": generate_unique_identifier(video_input), # Or hash?
                "title": Path(video_input).stem,
                "description": "Local file",
                "webpage_url": f"local://{Path(video_input).resolve()}", # Example local identifier
                "uploader": None, "upload_date": None, "duration": None, # Add more if extractable locally
            }
            processing_result["metadata"] = info_dict

        video_path = video_input

        # Perform transcription
        from tldw_Server_API.app.core.LLM_Calls.Summarization_General_Lib import perform_transcription, \
            perform_summarization

        audio_file_path, segments = perform_transcription(
            video_path, start_seconds, transcription_model, vad_use,
            diarize,
        )
        if audio_file_path is None or segments is None:
            processing_result = {
                "video_input": video_input,
                "status": "Error",
                "error": "Transcription failed or segments is None"
            }
            return processing_result

        # Store segments and analysis details
        processing_result["segments"] = segments
        processing_result["analysis_details"]["whisper_model"] = transcription_model
        # FIXME - add other details

        # Clean up intermediate audio file (if applicable and not requested to keep)
        if audio_file_path and os.path.exists(audio_file_path):# and not keep_intermediate_audio:
             try:
                 os.remove(audio_file_path)
             except Exception as e:
                 logging.warning(f"Failed to remove intermediate audio file: {e}")
                 # Optionally add to warnings list
                 # processing_result["warnings"] = processing_result.get("warnings", []) + [f"Failed cleanup: {e}"]

        # Possibly strip timestamps
        if not timestamp_option:
            # remove timestamps
            for seg in segments:
                seg.pop("Start", None)
                seg.pop("End", None)

        # Prepare content string
        transcription_text = extract_text_from_segments(segments, include_timestamps=timestamp_option)
        processing_result["content"] = transcription_text # Store the main content

        # Analyze video transcript if API is set
        analysis_text = None
        if api_name and api_name.lower() != "none":
            processing_result["analysis_details"]["llm_api"] = api_name
            processing_result["analysis_details"]["custom_prompt"] = custom_prompt
            processing_result["analysis_details"]["system_prompt"] = system_prompt

            text_to_analyze = processing_result["content"] # Use the generated transcript
            # Add metadata to analysis input
            text_to_analyze = f"{json.dumps(info_dict, indent=2)}\n\n{transcription_text}"

            # Apply chunking if needed before summarization
            if perform_chunking:
                chunk_opts = {
                    'method': chunk_method,
                    'max_size': max_chunk_size,
                    'overlap': chunk_overlap,
                    'adaptive': use_adaptive_chunking,
                    'multi_level': use_multi_level_chunking,
                    'language': chunk_language
                }
                # Assuming improved_chunking_process returns list of dicts like [{"text": "...", "metadata": ...}]
                chunked_texts_list = improved_chunking_process(text_to_analyze, chunk_opts)
                processing_result["chunks"] = chunked_texts_list # Store the chunks

                if chunked_texts_list:
                    chunk_summaries = []
                    # FIXME - Possibly setup async analysis ot analyze chunks as they become available instead of all at once
                    for chunk_block in chunked_texts_list:
                        csum = perform_summarization(api_name, chunk_block["text"], custom_prompt, api_key, system_message=system_prompt)
                        if csum:
                            chunk_summaries.append(csum)
                    if chunk_summaries:
                        # Combine chunk summaries (recursive or simple join)
                        if summarize_recursively and len(chunk_summaries) > 1:
                            combined_chunk_summaries = "\n\n".join(chunk_summaries)
                            analysis_text = perform_summarization(api_name, combined_chunk_summaries, custom_prompt, api_key, system_message=system_prompt)
                        else:
                            analysis_text = "\n\n---\n\n".join(chunk_summaries) # Simple join
                else:
                     # Chunking selected but produced no chunks? Summarize original.
                     analysis_text = perform_summarization(api_name, text_to_analyze, custom_prompt, api_key, system_message=system_prompt)
            else:
                 # Single pass summarization
                 analysis_text = perform_summarization(api_name, text_to_analyze, custom_prompt, api_key, system_message=system_prompt)

            processing_result["analysis"] = analysis_text

        # 4. Final Success State
        processing_result["status"] = "Success"
        return processing_result

    except Exception as e:
        logging.error(f"Exception in DB-agnostic process_single_video({video_input}): {e}", exc_info=True)
        processing_result["status"] = "Error"
        processing_result["error"] = f"{type(e).__name__}: {str(e)}"
        return processing_result


#
# End of Video_DL_Ingestion_Lib.py
#######################################################################################################################
