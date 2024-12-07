# Text-To-Speech / Speech-To-Text Documentation

## Overview
Use of functions for individual services.
Function for each service, streaming & non-streaming.
Non-streaming will return a file, streaming will return a stream.
Use of temporary files for storage.
Use of pydub for audio manipulation.
Use of pydub for audio merging.


https://github.com/jiaaro/pydub

Flow:
1. Clean/format input text
2. Split text into segments
3. Generate audio for each segment using designated provider function
4. Merge audio segments into single output file
5. Clean up temporary files




### Link Dump:

https://github.com/cpumaxx/sovits-ff-plugin



Train using: https://github.com/Mangio621/Mangio-RVC-Fork/releases,
import the .pth into https://huggingface.co/wok000/vcclient000/tree/main to convert your voice in near real time with about a .25s delay

https://www.hackster.io/lhl/voicechat2-local-ai-voice-chat-4c48f2

https://github.com/abus-aikorea/voice-pro

https://github.com/myshell-ai/MeloTTS
https://github.com/idiap/coqui-ai-TTS
https://docs.inferless.com/cookbook/serverless-customer-service-bot


https://huggingface.co/spaces/lamm-mit/PDF2Audio

https://huggingface.co/spaces/bencser/episodegen

https://github.com/Picovoice/speech-to-text-benchmark

https://huggingface.co/papers/2410.02678

https://github.com/livekit/agents
https://github.com/pipecat-ai/pipecat/tree/a367a038f1a3967292b5de5b43b8600a82a73fb6?tab=readme-ov-file

https://github.com/lamm-mit/PDF2Audio
https://github.com/Purfview/whisper-standalone-win
https://github.com/ictnlp/LLaMA-Omni

https://github.com/SWivid/F5-TTS


https://github.com/matatonic/openedai-speech

https://github.com/RVC-Boss/GPT-SoVITS
https://github.com/RVC-Boss/GPT-SoVITS/wiki/GPT%E2%80%90SoVITS%E2%80%90v2%E2%80%90features-(%E6%96%B0%E7%89%B9%E6%80%A7)
https://rentry.org/GPT-SoVITS-guide
https://rentry.org/GPT-SoVITS-guide
It's just the 3 buttons (speech-to-text, ssl, semantics) and then training. 

The default training settings on the gradio UI are fine but I save epoch 12-16-24 on SoVITS for testing as that's the sweet spot range.

Next thing that matters a lot is the ref audio you pick, and you can also drop your entire dataset into the "multiple references to average tone" box, which can improve the voice

Only thing I changed was remove the space at the beginning of each lines in your list file

(Look at batch size/ list file)

And make sure you get the latest version https://github.com/RVC-Boss/GPT-SoVITS/releases

https://github.com/souzatharsis/podcastfy

https://github.com/THUDM/GLM-4-Voice/tree/main

https://huggingface.co/cydxg/glm-4-voice-9b-int4/blob/main/README_en.md

https://github.com/meta-llama/llama-recipes/tree/main/recipes%2Fquickstart%2FNotebookLlama


https://sakshi113.github.io/mmau_homepage/

https://github.com/fishaudio/fish-speech/tree/main
https://github.com/fishaudio/fish-speech/blob/main/Start_Agent.md
https://huggingface.co/fishaudio/fish-agent-v0.1-3b/tree/main

https://github.com/pixelpump/Ai-Interview-Assistant-Python

https://github.com/Standard-Intelligence/hertz-dev

https://github.com/edwko/OuteTTS
https://huggingface.co/OuteAI/OuteTTS-0.2-500M-GGUF
https://huggingface.co/NexaAIDev/Qwen2-Audio-7B-GGUF

https://www.twilio.com/en-us/blog/twilio-openai-realtime-api-launch-integration