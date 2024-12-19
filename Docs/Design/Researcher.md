# Automated Researcher

## Introduction

This page is to document efforts towards creating a 'research' agent workflow for use within the project. The goal is to create a system that can automatically generate research reports, summaries, and other research-related tasks.

### Link Dump:
https://github.com/assafelovic/gpt-researcher
https://arxiv.org/abs/2411.15114
https://journaliststudio.google.com/pinpoint/about/
https://blog.google/products/gemini/google-gemini-deep-research/
https://github.com/neuml/annotateai
https://pub.towardsai.net/learn-anything-with-ai-and-the-feynman-technique-00a33f6a02bc
https://help.openalex.org/hc/en-us/articles/24396686889751-About-us
https://www.ginkgonotes.com/
https://www.reddit.com/r/Anki/comments/17u01ge/spaced_repetition_algorithm_a_threeday_journey/
https://github.com/open-spaced-repetition/fsrs4anki/wiki/Spaced-Repetition-Algorithm:-A-Three%E2%80%90Day-Journey-from-Novice-to-Expert#day-3-the-latest-progress


### Ideas
Gated, checkpoints with 'retry, skip, continue' options
s
Follow gptresearchers method at first, planner LLM -> query LLM -> analyzer LLM -> summarizer LLM



Researcher config section
```
[researcher]
# Researcher settings
default_search_engine = google
# Options are: google, bing, yandex, baidu, searx, kagi, serper, tavily
default_search_type = web
# Options are: web, local, both
default_search_language = en
# Options are: FIXME
default_search_report_language = en
# Options are: FIXME
default_search_sort = relevance
# Options are: relevance, date
default_search_safe_search = moderate
# Options are: off, moderate, strict
default_search_planner = openai-o1-full
# Options are: FIXME
default_search_planner_max_tokens = 8192
default_search_analyzer = openai-o1-full
# Options are: FIXME
default_search_analyzer_max_tokens = 8192
default_search_summarization = openai-o1-full
# Options are: FIXME
default_search_summarization_max_tokens = 8192
search_max_results = 100
search_report_format = markdown
# Options are: markdown, html, pdf
search_max_iterations = 5
search_max_subtopics = 4
search_custom_user_agent = "CUSTOM_USER_AGENT_HERE"
search_blacklist_URLs = "URL1,URL2,URL3"
```


https://github.com/TheBlewish/Automated-AI-Web-Researcher-Ollama/blob/main/Self_Improving_Search.py




### Researcher Workflow



### Researcher Prompts







one2manny
 — 
Today at 12:43 AM
A great way to make studying more efficient and convenient is to take a digital PDF textbook, split it into separate files for each chapter, and organize them individually. I then create a dedicated notebook for each chapter, treating it as a focused single source. From there, I convert each chapter into an audio format, like a podcast. This approach makes it easy to study while commuting, relaxing in bed with your eyes closed, or at any time when reading isn’t practical.

I also recommend creating a study guide for each chapter, fully breaking down key concepts and definitions. For more complex topics, the “explain like I’m 5” method works wonders—it simplifies challenging ideas into digestible explanations.

To take this further, incorporate a Personal Knowledge Management (PKM) system into your routine. Apps like Obsidian are perfect for this, with their flexible folder structures and Markdown formatting. I optimize my AI outputs for Markdown so I can copy, paste, and organize them into clean, structured notes. This ensures your materials are not only well-organized but also easy to access and build on later. A solid PKM system is invaluable for managing knowledge and staying on top of your studies!

