# Explain_summarize_tab.py
# Gradio UI for explaining and summarizing text
#
# Imports
import logging
#
# External Imports
import gradio as gr

from App_Function_Libraries.DB.DB_Manager import load_preset_prompts
from App_Function_Libraries.Gradio_UI.Gradio_Shared import update_user_prompt
#
# Local Imports
from App_Function_Libraries.Summarization.Local_Summarization_Lib import summarize_with_llama, summarize_with_kobold, \
    summarize_with_oobabooga, summarize_with_tabbyapi, summarize_with_vllm, summarize_with_local_llm, \
    summarize_with_ollama
from App_Function_Libraries.Summarization.Summarization_General_Lib import summarize_with_openai, summarize_with_anthropic, \
    summarize_with_cohere, summarize_with_groq, summarize_with_openrouter, summarize_with_deepseek, \
    summarize_with_huggingface
#
#
############################################################################################################
#
# Functions:

def create_summarize_explain_tab():
    with gr.TabItem("Analyze Text", visible=True):
        gr.Markdown("# Analyze / Explain / Summarize Text without ingesting it into the DB")
        with gr.Row():
            with gr.Column():
                with gr.Row():
                    text_to_work_input = gr.Textbox(label="Text to be Explained or Summarized",
                                                placeholder="Enter the text you want explained or summarized here",
                                                lines=20)
                with gr.Row():
                    explanation_checkbox = gr.Checkbox(label="Explain Text", value=True)
                    summarization_checkbox = gr.Checkbox(label="Summarize Text", value=True)
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
                    api_endpoint = gr.Dropdown(
                        choices=[None, "Local-LLM", "OpenAI", "Anthropic", "Cohere", "Groq", "DeepSeek", "Mistral",
                                 "OpenRouter",
                                 "Llama.cpp", "Kobold", "Ooba", "Tabbyapi", "VLLM", "ollama", "HuggingFace", "Custom-OpenAI-API"],
                        value=None,
                        label="API to be used for request (Mandatory)"
                    )
                with gr.Row():
                    api_key_input = gr.Textbox(label="API Key (if required)", placeholder="Enter your API key here",
                                               type="password")
                with gr.Row():
                    explain_summarize_button = gr.Button("Explain/Summarize")

            with gr.Column():
                summarization_output = gr.Textbox(label="Summary:", lines=20)
                explanation_output = gr.Textbox(label="Explanation:", lines=20)
                custom_prompt_output = gr.Textbox(label="Custom Prompt:", lines=20, visible=True)

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

        explain_summarize_button.click(
            fn=summarize_explain_text,
            inputs=[text_to_work_input, api_endpoint, api_key_input, summarization_checkbox, explanation_checkbox, custom_prompt_input, system_prompt_input],
            outputs=[summarization_output, explanation_output, custom_prompt_output]
        )


def summarize_explain_text(message, api_endpoint, api_key, summarization, explanation, custom_prompt, custom_system_prompt,):
    global custom_prompt_output
    summarization_response = None
    explanation_response = None
    temp = 0.7
    try:
        logging.info(f"Debug - summarize_explain_text Function - Message: {message}")
        logging.info(f"Debug - summarize_explain_text Function - API Endpoint: {api_endpoint}")

        # Prepare the input for the API
        input_data = f"User: {message}\n"
        # Print first 500 chars
        logging.info(f"Debug - Chat Function - Input Data: {input_data[:500]}...")
        logging.debug(f"Debug - Chat Function - API Key: {api_key[:10]}")
        user_prompt = " "
        if not api_endpoint:
            return "Please select an API endpoint", "Please select an API endpoint"
        try:
            if summarization:
                system_prompt = """<s>You are a bulleted notes specialist. [INST]```When creating comprehensive bulleted notes, you should follow these guidelines: Use multiple headings based on the referenced topics, not categories like quotes or terms. Headings should be surrounded by bold formatting and not be listed as bullet points themselves. Leave no space between headings and their corresponding list items underneath. Important terms within the content should be emphasized by setting them in bold font. Any text that ends with a colon should also be bolded. Before submitting your response, review the instructions, and make any corrections necessary to adhered to the specified format. Do not reference these instructions within the notes.``` \nBased on the content between backticks create comprehensive bulleted notes.[/INST]
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
                - Do not reference these instructions in your response.</s>[INST] {{ .Prompt }} [/INST]"""

                # Use the existing API request code based on the selected endpoint
                logging.info(f"Debug - Chat Function - API Endpoint: {api_endpoint}")
                if api_endpoint.lower() == 'openai':
                    summarization_response = summarize_with_openai(api_key, input_data, user_prompt, temp,
                                                                   system_prompt)
                elif api_endpoint.lower() == "anthropic":
                    summarization_response = summarize_with_anthropic(api_key, input_data, user_prompt, temp,
                                                                      system_prompt)
                elif api_endpoint.lower() == "cohere":
                    summarization_response = summarize_with_cohere(api_key, input_data, user_prompt, temp,
                                                                   system_prompt)
                elif api_endpoint.lower() == "groq":
                    summarization_response = summarize_with_groq(api_key, input_data, user_prompt, temp, system_prompt)
                elif api_endpoint.lower() == "openrouter":
                    summarization_response = summarize_with_openrouter(api_key, input_data, user_prompt, temp,
                                                                       system_prompt)
                elif api_endpoint.lower() == "deepseek":
                    summarization_response = summarize_with_deepseek(api_key, input_data, user_prompt, temp,
                                                                     system_prompt)
                elif api_endpoint.lower() == "llama.cpp":
                    summarization_response = summarize_with_llama(input_data, user_prompt, api_key, temp, system_prompt)
                elif api_endpoint.lower() == "kobold":
                    summarization_response = summarize_with_kobold(input_data, api_key, user_prompt, temp,
                                                                   system_prompt)
                elif api_endpoint.lower() == "ooba":
                    summarization_response = summarize_with_oobabooga(input_data, api_key, user_prompt, temp,
                                                                      system_prompt)
                elif api_endpoint.lower() == "tabbyapi":
                    summarization_response = summarize_with_tabbyapi(input_data, user_prompt, temp, system_prompt)
                elif api_endpoint.lower() == "vllm":
                    summarization_response = summarize_with_vllm(input_data, user_prompt, system_prompt)
                elif api_endpoint.lower() == "local-llm":
                    summarization_response = summarize_with_local_llm(input_data, user_prompt, temp, system_prompt)
                elif api_endpoint.lower() == "huggingface":
                    summarization_response = summarize_with_huggingface(api_key, input_data, user_prompt,
                                                                        temp)  # , system_prompt)
                elif api_endpoint.lower() == "ollama":
                    summarization_response = summarize_with_ollama(input_data, user_prompt, None, api_key, temp, system_prompt)
                else:
                    raise ValueError(f"Unsupported API endpoint: {api_endpoint}")
        except Exception as e:
            logging.error(f"Error in summarization: {str(e)}")
            response1 = f"An error occurred during summarization: {str(e)}"

        try:
            if explanation:
                system_prompt = """You are a professional teacher. Please explain the content presented in an easy to digest fashion so that a non-specialist may understand it."""
                # Use the existing API request code based on the selected endpoint
                logging.info(f"Debug - Chat Function - API Endpoint: {api_endpoint}")
                if api_endpoint.lower() == 'openai':
                    explanation_response = summarize_with_openai(api_key, input_data, user_prompt, temp, system_prompt)
                elif api_endpoint.lower() == "anthropic":
                    explanation_response = summarize_with_anthropic(api_key, input_data, user_prompt, temp,
                                                                    system_prompt)
                elif api_endpoint.lower() == "cohere":
                    explanation_response = summarize_with_cohere(api_key, input_data, user_prompt, temp, system_prompt)
                elif api_endpoint.lower() == "groq":
                    explanation_response = summarize_with_groq(api_key, input_data, user_prompt, temp, system_prompt)
                elif api_endpoint.lower() == "openrouter":
                    explanation_response = summarize_with_openrouter(api_key, input_data, user_prompt, temp,
                                                                     system_prompt)
                elif api_endpoint.lower() == "deepseek":
                    explanation_response = summarize_with_deepseek(api_key, input_data, user_prompt, temp,
                                                                   system_prompt)
                elif api_endpoint.lower() == "llama.cpp":
                    explanation_response = summarize_with_llama(input_data, user_prompt, temp, system_prompt)
                elif api_endpoint.lower() == "kobold":
                    explanation_response = summarize_with_kobold(input_data, api_key, user_prompt, temp, system_prompt)
                elif api_endpoint.lower() == "ooba":
                    explanation_response = summarize_with_oobabooga(input_data, api_key, user_prompt, temp,
                                                                    system_prompt)
                elif api_endpoint.lower() == "tabbyapi":
                    explanation_response = summarize_with_tabbyapi(input_data, user_prompt, temp, system_prompt)
                elif api_endpoint.lower() == "vllm":
                    explanation_response = summarize_with_vllm(input_data, user_prompt, system_prompt)
                elif api_endpoint.lower() == "local-llm":
                    explanation_response = summarize_with_local_llm(input_data, user_prompt, temp, system_prompt)
                elif api_endpoint.lower() == "huggingface":
                    explanation_response = summarize_with_huggingface(api_key, input_data, user_prompt,
                                                                      temp)  # , system_prompt)
                elif api_endpoint.lower() == "ollama":
                    explanation_response = summarize_with_ollama(input_data, user_prompt, temp, system_prompt)
                else:
                    raise ValueError(f"Unsupported API endpoint: {api_endpoint}")
        except Exception as e:
            logging.error(f"Error in summarization: {str(e)}")
            response2 = f"An error occurred during summarization: {str(e)}"

        try:
            if custom_prompt:
                system_prompt = custom_system_prompt
                user_prompt = custom_prompt + input_data
                # Use the existing API request code based on the selected endpoint
                logging.info(f"Debug - Chat Function - API Endpoint: {api_endpoint}")
                if api_endpoint.lower() == 'openai':
                    custom_prompt_output = summarize_with_openai(api_key, input_data, user_prompt, temp, system_prompt)
                elif api_endpoint.lower() == "anthropic":
                    custom_prompt_output = summarize_with_anthropic(api_key, input_data, user_prompt, temp,
                                                                    system_prompt)
                elif api_endpoint.lower() == "cohere":
                    custom_prompt_output = summarize_with_cohere(api_key, input_data, user_prompt, temp, system_prompt)
                elif api_endpoint.lower() == "groq":
                    custom_prompt_output = summarize_with_groq(api_key, input_data, user_prompt, temp, system_prompt)
                elif api_endpoint.lower() == "openrouter":
                    custom_prompt_output = summarize_with_openrouter(api_key, input_data, user_prompt, temp,
                                                                     system_prompt)
                elif api_endpoint.lower() == "deepseek":
                    custom_prompt_output = summarize_with_deepseek(api_key, input_data, user_prompt, temp,
                                                                   system_prompt)
                elif api_endpoint.lower() == "llama.cpp":
                    custom_prompt_output = summarize_with_llama(input_data, user_prompt, temp, system_prompt)
                elif api_endpoint.lower() == "kobold":
                    custom_prompt_output = summarize_with_kobold(input_data, api_key, user_prompt, temp, system_prompt)
                elif api_endpoint.lower() == "ooba":
                    custom_prompt_output = summarize_with_oobabooga(input_data, api_key, user_prompt, temp,
                                                                    system_prompt)
                elif api_endpoint.lower() == "tabbyapi":
                    custom_prompt_output = summarize_with_tabbyapi(input_data, user_prompt, temp, system_prompt)
                elif api_endpoint.lower() == "vllm":
                    custom_prompt_output = summarize_with_vllm(input_data, user_prompt, system_prompt)
                elif api_endpoint.lower() == "local-llm":
                    custom_prompt_output = summarize_with_local_llm(input_data, user_prompt, temp, system_prompt)
                elif api_endpoint.lower() == "huggingface":
                    custom_prompt_output = summarize_with_huggingface(api_key, input_data, user_prompt,
                                                                      temp)  # , system_prompt)
                elif api_endpoint.lower() == "ollama":
                    custom_prompt_output = summarize_with_ollama(input_data, user_prompt, temp, system_prompt)
                else:
                    raise ValueError(f"Unsupported API endpoint: {api_endpoint}")
        except Exception as e:
            logging.error(f"Error in summarization: {str(e)}")
            response2 = f"An error occurred during summarization: {str(e)}"


        if summarization_response:
            response1 = f"Summary: {summarization_response}"
        else:
            response1 = "Summary: No summary requested"

        if explanation_response:
            response2 = f"Explanation: {explanation_response}"
        else:
            response2 = "Explanation: No explanation requested"

        if custom_prompt_output:
            response3 = f"Custom Prompt: {custom_prompt_output}"
        else:
            response3 = "Custom Prompt: No custom prompt requested"

        return response1, response2, response3

    except Exception as e:
        logging.error(f"Error in chat function: {str(e)}")
        return f"An error occurred: {str(e)}"