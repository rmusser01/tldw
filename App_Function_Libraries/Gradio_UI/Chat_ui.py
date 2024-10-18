# Chat_ui.py
# Description: Chat interface functions for Gradio
#
# Imports
import html
import json
import logging
import os
import sqlite3
from datetime import datetime
#
# External Imports
import gradio as gr
#
# Local Imports
from App_Function_Libraries.Chat import chat, save_chat_history, update_chat_content, save_chat_history_to_db_wrapper
from App_Function_Libraries.DB.DB_Manager import add_chat_message, search_chat_conversations, create_chat_conversation, \
    get_chat_messages, update_chat_message, delete_chat_message, load_preset_prompts, db
from App_Function_Libraries.Gradio_UI.Gradio_Shared import update_dropdown, update_user_prompt


#
#
########################################################################################################################
#
# Functions:


def show_edit_message(selected):
    if selected:
        return gr.update(value=selected[0], visible=True), gr.update(value=selected[1], visible=True), gr.update(
            visible=True)
    return gr.update(visible=False), gr.update(visible=False), gr.update(visible=False)


def show_delete_message(selected):
    if selected:
        return gr.update(value=selected[1], visible=True), gr.update(visible=True)
    return gr.update(visible=False), gr.update(visible=False)


def debug_output(media_content, selected_parts):
    print(f"Debug - Media Content: {media_content}")
    print(f"Debug - Selected Parts: {selected_parts}")
    return ""


def update_selected_parts(use_content, use_summary, use_prompt):
    selected_parts = []
    if use_content:
        selected_parts.append("content")
    if use_summary:
        selected_parts.append("summary")
    if use_prompt:
        selected_parts.append("prompt")
    print(f"Debug - Update Selected Parts: {selected_parts}")
    return selected_parts


# Old update_user_prompt shim for backwards compatibility
def get_system_prompt(preset_name):
    # For backwards compatibility
    prompts = update_user_prompt(preset_name)
    return prompts["system_prompt"]

def clear_chat():
    """
    Return empty list for chatbot and None for conversation_id
    @return:
    """
    return gr.update(value=[]), None


def clear_chat_single():
    """
    Clears the chatbot and chat history.

    Returns:
        list: Empty list for chatbot messages.
        list: Empty list for chat history.
    """
    return [], []

# FIXME - add additional features....
def chat_wrapper(message, history, media_content, selected_parts, api_endpoint, api_key, custom_prompt, conversation_id,
                 save_conversation, temperature, system_prompt, max_tokens=None, top_p=None, frequency_penalty=None,
                 presence_penalty=None, stop_sequence=None):
    try:
        if save_conversation:
            if conversation_id is None:
                # Create a new conversation
                media_id = media_content.get('id', None)
                conversation_name = f"Chat about {media_content.get('title', 'Unknown Media')} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                conversation_id = create_chat_conversation(media_id, conversation_name)

            # Add user message to the database
            user_message_id = add_chat_message(conversation_id, "user", message)

        # Include the selected parts and custom_prompt only for the first message
        if not history and selected_parts:
            message_body = "\n".join(selected_parts)
            full_message = f"{custom_prompt}\n\n{message}\n\n{message_body}"
        elif custom_prompt:
            full_message = f"{custom_prompt}\n\n{message}"
        else:
            full_message = message

        # Generate bot response
        bot_message = chat(full_message, history, media_content, selected_parts, api_endpoint, api_key, custom_prompt,
                           temperature, system_prompt)

        logging.debug(f"Bot message being returned: {bot_message}")

        if save_conversation:
            # Add assistant message to the database
            add_chat_message(conversation_id, "assistant", bot_message)

        # Update history
        new_history = history + [(message, bot_message)]

        return bot_message, new_history, conversation_id
    except Exception as e:
        logging.error(f"Error in chat wrapper: {str(e)}")
        return "An error occurred.", history, conversation_id

def search_conversations(query):
    try:
        conversations = search_chat_conversations(query)
        if not conversations:
            print(f"Debug - Search Conversations - No results found for query: {query}")
            return gr.update(choices=[])

        conversation_options = [
            (f"{c['conversation_name']} (Media: {c['media_title']}, ID: {c['id']})", c['id'])
            for c in conversations
        ]
        print(f"Debug - Search Conversations - Options: {conversation_options}")
        return gr.update(choices=conversation_options)
    except Exception as e:
        print(f"Debug - Search Conversations - Error: {str(e)}")
        return gr.update(choices=[])


def load_conversation(conversation_id):
    if not conversation_id:
        return [], None

    messages = get_chat_messages(conversation_id)
    history = [
        (msg['message'], None) if msg['sender'] == 'user' else (None, msg['message'])
        for msg in messages
    ]
    return history, conversation_id


def update_message_in_chat(message_id, new_text, history):
    update_chat_message(message_id, new_text)
    updated_history = [(msg1, msg2) if msg1[1] != message_id and msg2[1] != message_id
                       else ((new_text, msg1[1]) if msg1[1] == message_id else (new_text, msg2[1]))
                       for msg1, msg2 in history]
    return updated_history


def delete_message_from_chat(message_id, history):
    delete_chat_message(message_id)
    updated_history = [(msg1, msg2) for msg1, msg2 in history if msg1[1] != message_id and msg2[1] != message_id]
    return updated_history


def regenerate_last_message(history, media_content, selected_parts, api_endpoint, api_key, custom_prompt, temperature, system_prompt):
    if not history:
        return history, "No messages to regenerate."

    last_entry = history[-1]
    last_user_message, last_bot_message = last_entry

    if last_bot_message is None:
        return history, "The last message is not from the bot."

    new_history = history[:-1]

    if not last_user_message:
        return new_history, "No user message to regenerate the bot response."

    full_message = last_user_message

    bot_message = chat(
        full_message,
        new_history,
        media_content,
        selected_parts,
        api_endpoint,
        api_key,
        custom_prompt,
        temperature,
        system_prompt
    )

    new_history.append((last_user_message, bot_message))

    return new_history, "Last message regenerated successfully."

def create_chat_interface():
    custom_css = """
    .chatbot-container .message-wrap .message {
        font-size: 14px !important;
    }
    """
    with gr.TabItem("Remote LLM Chat (Horizontal)", visible=True):
        gr.Markdown("# Chat with a designated LLM Endpoint, using your selected item as starting context")
        chat_history = gr.State([])
        media_content = gr.State({})
        selected_parts = gr.State([])
        conversation_id = gr.State(None)

        with gr.Row():
            with gr.Column(scale=1):
                search_query_input = gr.Textbox(label="Search Query", placeholder="Enter your search query here...")
                search_type_input = gr.Radio(choices=["Title", "URL", "Keyword", "Content"], value="Title",
                                             label="Search By")
                search_button = gr.Button("Search")
                items_output = gr.Dropdown(label="Select Item", choices=[], interactive=True)
                item_mapping = gr.State({})
                with gr.Row():
                    use_content = gr.Checkbox(label="Use Content")
                    use_summary = gr.Checkbox(label="Use Summary")
                    use_prompt = gr.Checkbox(label="Use Prompt")
                    save_conversation = gr.Checkbox(label="Save Conversation", value=False, visible=True)
                with gr.Row():
                    temperature = gr.Slider(label="Temperature", minimum=0.00, maximum=1.0, step=0.05, value=0.7)
                with gr.Row():
                    conversation_search = gr.Textbox(label="Search Conversations")
                with gr.Row():
                    search_conversations_btn = gr.Button("Search Conversations")
                with gr.Row():
                    previous_conversations = gr.Dropdown(label="Select Conversation", choices=[], interactive=True)
                with gr.Row():
                    load_conversations_btn = gr.Button("Load Selected Conversation")

                api_endpoint = gr.Dropdown(label="Select API Endpoint",
                                           choices=["Local-LLM", "OpenAI", "Anthropic", "Cohere", "Groq", "DeepSeek",
                                                    "Mistral", "OpenRouter",
                                                    "Llama.cpp", "Kobold", "Ooba", "Tabbyapi", "VLLM", "ollama",
                                                    "HuggingFace"])
                api_key = gr.Textbox(label="API Key (if required)", type="password")
                custom_prompt_checkbox = gr.Checkbox(label="Use a Custom Prompt",
                                                     value=False,
                                                     visible=True)
                preset_prompt_checkbox = gr.Checkbox(label="Use a pre-set Prompt",
                                                     value=False,
                                                     visible=True)
                preset_prompt = gr.Dropdown(label="Select Preset Prompt",
                                            choices=load_preset_prompts(),
                                            visible=False)
                user_prompt = gr.Textbox(label="Custom Prompt",
                                         placeholder="Enter custom prompt here",
                                         lines=3,
                                         visible=False)
                system_prompt_input = gr.Textbox(label="System Prompt",
                                                 value="You are a helpful AI assitant",
                                                 lines=3,
                                                 visible=False)
            with gr.Column(scale=2):
                chatbot = gr.Chatbot(height=600, elem_classes="chatbot-container")
                msg = gr.Textbox(label="Enter your message")
                submit = gr.Button("Submit")
                regenerate_button = gr.Button("Regenerate Last Message")
                clear_chat_button = gr.Button("Clear Chat")

                edit_message_id = gr.Number(label="Message ID to Edit", visible=False)
                edit_message_text = gr.Textbox(label="Edit Message", visible=False)
                update_message_button = gr.Button("Update Message", visible=False)

                delete_message_id = gr.Number(label="Message ID to Delete", visible=False)
                delete_message_button = gr.Button("Delete Message", visible=False)

                chat_media_name = gr.Textbox(label="Custom Chat Name(optional)")
                save_chat_history_to_db = gr.Button("Save Chat History to DataBase")
                save_chat_history_as_file = gr.Button("Save Chat History as File")
                download_file = gr.File(label="Download Chat History")
                save_status = gr.Textbox(label="Save Status", interactive=False)

        # Restore original functionality
        search_button.click(
            fn=update_dropdown,
            inputs=[search_query_input, search_type_input],
            outputs=[items_output, item_mapping]
        )

        def save_chat_wrapper(history, conversation_id, media_content):
            file_path = save_chat_history(history, conversation_id, media_content)
            if file_path:
                return file_path, f"Chat history saved successfully as {os.path.basename(file_path)}!"
            else:
                return None, "Error saving chat history. Please check the logs and try again."

        save_chat_history_as_file.click(
            save_chat_wrapper,
            inputs=[chatbot, conversation_id, media_content],
            outputs=[download_file, save_status]
        )

        def update_prompts(preset_name):
            prompts = update_user_prompt(preset_name)
            return (
                gr.update(value=prompts["user_prompt"], visible=True),
                gr.update(value=prompts["system_prompt"], visible=True)
            )

        def clear_chat():
            return [], None  # Return empty list for chatbot and None for conversation_id

        clear_chat_button.click(
            clear_chat,
            outputs=[chatbot, conversation_id]
        )
        preset_prompt.change(
            update_prompts,
            inputs=preset_prompt,
            outputs=[user_prompt, system_prompt_input]
        )
        custom_prompt_checkbox.change(
            fn=lambda x: (gr.update(visible=x), gr.update(visible=x)),
            inputs=[custom_prompt_checkbox],
            outputs=[user_prompt, system_prompt_input]
        )
        preset_prompt_checkbox.change(
            fn=lambda x: gr.update(visible=x),
            inputs=[preset_prompt_checkbox],
            outputs=[preset_prompt]
        )
        submit.click(
            chat_wrapper,
            inputs=[msg, chatbot, media_content, selected_parts, api_endpoint, api_key, user_prompt, conversation_id,
                    save_conversation, temperature, system_prompt_input],
            outputs=[msg, chatbot, conversation_id]
        ).then(  # Clear the message box after submission
            lambda x: gr.update(value=""),
            inputs=[chatbot],
            outputs=[msg]
        ).then(  # Clear the user prompt after the first message
            lambda: (gr.update(value=""), gr.update(value="")),
            outputs=[user_prompt, system_prompt_input]
        )

        items_output.change(
            update_chat_content,
            inputs=[items_output, use_content, use_summary, use_prompt, item_mapping],
            outputs=[media_content, selected_parts]
        )
        use_content.change(update_selected_parts, inputs=[use_content, use_summary, use_prompt],
                           outputs=[selected_parts])
        use_summary.change(update_selected_parts, inputs=[use_content, use_summary, use_prompt],
                           outputs=[selected_parts])
        use_prompt.change(update_selected_parts, inputs=[use_content, use_summary, use_prompt],
                          outputs=[selected_parts])
        items_output.change(debug_output, inputs=[media_content, selected_parts], outputs=[])

        search_conversations_btn.click(
            search_conversations,
            inputs=[conversation_search],
            outputs=[previous_conversations]
        )

        load_conversations_btn.click(
            clear_chat,
            outputs=[chatbot, chat_history]
        ).then(
            load_conversation,
            inputs=[previous_conversations],
            outputs=[chatbot, conversation_id]
        )

        previous_conversations.change(
            load_conversation,
            inputs=[previous_conversations],
            outputs=[chat_history]
        )

        update_message_button.click(
            update_message_in_chat,
            inputs=[edit_message_id, edit_message_text, chat_history],
            outputs=[chatbot]
        )

        delete_message_button.click(
            delete_message_from_chat,
            inputs=[delete_message_id, chat_history],
            outputs=[chatbot]
        )

        save_chat_history_as_file.click(
            save_chat_history,
            inputs=[chatbot, conversation_id],
            outputs=[download_file]
        )

        save_chat_history_to_db.click(
            save_chat_history_to_db_wrapper,
            inputs=[chatbot, conversation_id, media_content, chat_media_name],
            outputs=[conversation_id, gr.Textbox(label="Save Status")]
        )

        regenerate_button.click(
            regenerate_last_message,
            inputs=[chatbot, media_content, selected_parts, api_endpoint, api_key, user_prompt, temperature, system_prompt_input],
            outputs=[chatbot, save_status]
        )

        chatbot.select(show_edit_message, None, [edit_message_text, edit_message_id, update_message_button])
        chatbot.select(show_delete_message, None, [delete_message_id, delete_message_button])


def create_chat_interface_stacked():
    custom_css = """
    .chatbot-container .message-wrap .message {
        font-size: 14px !important;
    }
    """
    with gr.TabItem("Remote LLM Chat - Stacked", visible=True):
        gr.Markdown("# Stacked Chat")
        chat_history = gr.State([])
        media_content = gr.State({})
        selected_parts = gr.State([])
        conversation_id = gr.State(None)

        with gr.Row():
            with gr.Column():
                search_query_input = gr.Textbox(label="Search Query", placeholder="Enter your search query here...")
                search_type_input = gr.Radio(choices=["Title", "URL", "Keyword", "Content"], value="Title",
                                             label="Search By")
                search_button = gr.Button("Search")
                items_output = gr.Dropdown(label="Select Item", choices=[], interactive=True)
                item_mapping = gr.State({})
                with gr.Row():
                    use_content = gr.Checkbox(label="Use Content")
                    use_summary = gr.Checkbox(label="Use Summary")
                    use_prompt = gr.Checkbox(label="Use Prompt")
                    save_conversation = gr.Checkbox(label="Save Conversation", value=False, visible=True)
                    temp = gr.Slider(label="Temperature", minimum=0.00, maximum=1.0, step=0.05, value=0.7)
                with gr.Row():
                    conversation_search = gr.Textbox(label="Search Conversations")
                with gr.Row():
                    previous_conversations = gr.Dropdown(label="Select Conversation", choices=[], interactive=True)
                with gr.Row():
                    search_conversations_btn = gr.Button("Search Conversations")
                    load_conversations_btn = gr.Button("Load Selected Conversation")
            with gr.Column():
                api_endpoint = gr.Dropdown(label="Select API Endpoint",
                                           choices=["Local-LLM", "OpenAI", "Anthropic", "Cohere", "Groq", "DeepSeek",
                                                    "OpenRouter", "Mistral", "Llama.cpp", "Kobold", "Ooba", "Tabbyapi",
                                                    "VLLM", "ollama", "HuggingFace"])
                api_key = gr.Textbox(label="API Key (if required)", type="password")
                preset_prompt = gr.Dropdown(label="Select Preset Prompt",
                                            choices=load_preset_prompts(),
                                            visible=True)
                system_prompt = gr.Textbox(label="System Prompt",
                                           value="You are a helpful AI assistant.",
                                           lines=3,
                                           visible=True)
                user_prompt = gr.Textbox(label="Custom User Prompt",
                                         placeholder="Enter custom prompt here",
                                         lines=3,
                                         visible=True)
                gr.Markdown("Scroll down for the chat window...")
        with gr.Row():
            with gr.Column(scale=1):
                chatbot = gr.Chatbot(height=600, elem_classes="chatbot-container")
                msg = gr.Textbox(label="Enter your message")
        with gr.Row():
            with gr.Column():
                submit = gr.Button("Submit")
                regenerate_button = gr.Button("Regenerate Last Message")
                clear_chat_button = gr.Button("Clear Chat")
                chat_media_name = gr.Textbox(label="Custom Chat Name(optional)", visible=True)
                save_chat_history_to_db = gr.Button("Save Chat History to DataBase")
                save_chat_history_as_file = gr.Button("Save Chat History as File")
            with gr.Column():
                download_file = gr.File(label="Download Chat History")

        # Restore original functionality
        search_button.click(
            fn=update_dropdown,
            inputs=[search_query_input, search_type_input],
            outputs=[items_output, item_mapping]
        )

        def update_prompts(preset_name):
            prompts = update_user_prompt(preset_name)
            return (
                gr.update(value=prompts["user_prompt"], visible=True),
                gr.update(value=prompts["system_prompt"], visible=True)
            )

        clear_chat_button.click(
            clear_chat,
            outputs=[chatbot, conversation_id]
        )
        preset_prompt.change(
            update_prompts,
            inputs=preset_prompt,
            outputs=[user_prompt, system_prompt]
        )

        submit.click(
            chat_wrapper,
            inputs=[msg, chatbot, media_content, selected_parts, api_endpoint, api_key, user_prompt,
                    conversation_id, save_conversation, temp, system_prompt],
            outputs=[msg, chatbot, conversation_id]
        ).then(  # Clear the message box after submission
            lambda x: gr.update(value=""),
            inputs=[chatbot],
            outputs=[msg]
        ).then(  # Clear the user prompt after the first message
            lambda: gr.update(value=""),
            outputs=[user_prompt, system_prompt]
        )

        items_output.change(
            update_chat_content,
            inputs=[items_output, use_content, use_summary, use_prompt, item_mapping],
            outputs=[media_content, selected_parts]
        )
        use_content.change(update_selected_parts, inputs=[use_content, use_summary, use_prompt],
                           outputs=[selected_parts])
        use_summary.change(update_selected_parts, inputs=[use_content, use_summary, use_prompt],
                           outputs=[selected_parts])
        use_prompt.change(update_selected_parts, inputs=[use_content, use_summary, use_prompt],
                          outputs=[selected_parts])
        items_output.change(debug_output, inputs=[media_content, selected_parts], outputs=[])

        search_conversations_btn.click(
            search_conversations,
            inputs=[conversation_search],
            outputs=[previous_conversations]
        )

        load_conversations_btn.click(
            clear_chat,
            outputs=[chatbot, chat_history]
        ).then(
            load_conversation,
            inputs=[previous_conversations],
            outputs=[chatbot, conversation_id]
        )

        previous_conversations.change(
            load_conversation,
            inputs=[previous_conversations],
            outputs=[chat_history]
        )

        save_chat_history_as_file.click(
            save_chat_history,
            inputs=[chatbot, conversation_id],
            outputs=[download_file]
        )

        save_chat_history_to_db.click(
            save_chat_history_to_db_wrapper,
            inputs=[chatbot, conversation_id, media_content, chat_media_name],
            outputs=[conversation_id, gr.Textbox(label="Save Status")]
        )

        regenerate_button.click(
            regenerate_last_message,
            inputs=[chatbot, media_content, selected_parts, api_endpoint, api_key, user_prompt, temp, system_prompt],
            outputs=[chatbot, gr.Textbox(label="Regenerate Status")]
        )


# FIXME - System prompts
def create_chat_interface_multi_api():
    custom_css = """
    .chatbot-container .message-wrap .message {
        font-size: 14px !important;
    }
    .chat-window {
        height: 400px;
        overflow-y: auto;
    }
    """
    with gr.TabItem("One Prompt - Multiple APIs", visible=True):
        gr.Markdown("# One Prompt but Multiple APIs Chat Interface")

        with gr.Row():
            with gr.Column(scale=1):
                search_query_input = gr.Textbox(label="Search Query", placeholder="Enter your search query here...")
                search_type_input = gr.Radio(choices=["Title", "URL", "Keyword", "Content"], value="Title",
                                             label="Search By")
                search_button = gr.Button("Search")
                items_output = gr.Dropdown(label="Select Item", choices=[], interactive=True)
                item_mapping = gr.State({})
                with gr.Row():
                    use_content = gr.Checkbox(label="Use Content")
                    use_summary = gr.Checkbox(label="Use Summary")
                    use_prompt = gr.Checkbox(label="Use Prompt")
            with gr.Column():
                preset_prompt = gr.Dropdown(label="Select Preset Prompt", choices=load_preset_prompts(), visible=True)
                system_prompt = gr.Textbox(label="System Prompt", value="You are a helpful AI assistant.", lines=5)
                user_prompt = gr.Textbox(label="Modify Prompt (Prefixed to your message every time)", lines=5, value="", visible=True)

        with gr.Row():
            chatbots = []
            api_endpoints = []
            api_keys = []
            temperatures = []
            regenerate_buttons = []
            for i in range(3):
                with gr.Column():
                    gr.Markdown(f"### Chat Window {i + 1}")
                    api_endpoint = gr.Dropdown(label=f"API Endpoint {i + 1}",
                                               choices=["Local-LLM", "OpenAI", "Anthropic", "Cohere", "Groq",
                                                        "DeepSeek", "Mistral", "OpenRouter", "Llama.cpp", "Kobold",
                                                        "Ooba", "Tabbyapi", "VLLM", "ollama", "HuggingFace"])
                    api_key = gr.Textbox(label=f"API Key {i + 1} (if required)", type="password")
                    temperature = gr.Slider(label=f"Temperature {i + 1}", minimum=0.0, maximum=1.0, step=0.05,
                                            value=0.7)
                    chatbot = gr.Chatbot(height=800, elem_classes="chat-window")
                    regenerate_button = gr.Button(f"Regenerate Last Message {i + 1}")
                    chatbots.append(chatbot)
                    api_endpoints.append(api_endpoint)
                    api_keys.append(api_key)
                    temperatures.append(temperature)
                    regenerate_buttons.append(regenerate_button)

        with gr.Row():
            msg = gr.Textbox(label="Enter your message", scale=4)
            submit = gr.Button("Submit", scale=1)
            clear_chat_button = gr.Button("Clear All Chats")

        # State variables
        chat_history = [gr.State([]) for _ in range(3)]
        media_content = gr.State({})
        selected_parts = gr.State([])
        conversation_id = gr.State(None)

        # Event handlers
        search_button.click(
            fn=update_dropdown,
            inputs=[search_query_input, search_type_input],
            outputs=[items_output, item_mapping]
        )

        preset_prompt.change(update_user_prompt, inputs=preset_prompt, outputs=user_prompt)


        def clear_all_chats():
            return [[]] * 3 + [[]] * 3

        clear_chat_button.click(
            clear_all_chats,
            outputs=chatbots + chat_history
        )
        def chat_wrapper_multi(message, custom_prompt, system_prompt, *args):
            chat_histories = args[:3]
            chatbots = args[3:6]
            api_endpoints = args[6:9]
            api_keys = args[9:12]
            temperatures = args[12:15]
            media_content = args[15]
            selected_parts = args[16]

            new_chat_histories = []
            new_chatbots = []

            for i in range(3):
                # Call chat_wrapper with dummy values for conversation_id and save_conversation
                bot_message, new_history, _ = chat_wrapper(
                    message, chat_histories[i], media_content, selected_parts,
                    api_endpoints[i], api_keys[i], custom_prompt, None,  # None for conversation_id
                    False,  # False for save_conversation
                    temperature=temperatures[i],
                    system_prompt=system_prompt
                )

                new_chatbot = chatbots[i] + [(message, bot_message)]

                new_chat_histories.append(new_history)
                new_chatbots.append(new_chatbot)

            return [gr.update(value="")] + new_chatbots + new_chat_histories


        def regenerate_last_message(chat_history, chatbot, media_content, selected_parts, api_endpoint, api_key, custom_prompt, temperature, system_prompt):
            if not chat_history:
                return chatbot, chat_history, "No messages to regenerate."

            last_entry = chat_history[-1]
            last_user_message, last_bot_message = last_entry

            if last_bot_message is None:
                return chatbot, chat_history, "The last message is not from the bot."

            new_history = chat_history[:-1]

            if not last_user_message:
                return chatbot[:-1], new_history, "No user message to regenerate the bot response."

            bot_message = chat(
                last_user_message,
                new_history,
                media_content,
                selected_parts,
                api_endpoint,
                api_key,
                custom_prompt,
                temperature,
                system_prompt
            )

            new_history.append((last_user_message, bot_message))
            new_chatbot = chatbot[:-1] + [(last_user_message, bot_message)]

            return new_chatbot, new_history, "Last message regenerated successfully."

        for i in range(3):
            regenerate_buttons[i].click(
                regenerate_last_message,
                inputs=[chat_history[i], chatbots[i], media_content, selected_parts, api_endpoints[i], api_keys[i], user_prompt, temperatures[i], system_prompt],
                outputs=[chatbots[i], chat_history[i], gr.Textbox(label=f"Regenerate Status {i + 1}")]
            )

        # In the create_chat_interface_multi_api function:
        submit.click(
            chat_wrapper_multi,
            inputs=[msg, user_prompt,
                    system_prompt] + chat_history + chatbots + api_endpoints + api_keys + temperatures +
                   [media_content, selected_parts],
            outputs=[msg] + chatbots + chat_history
        ).then(
            lambda: (gr.update(value=""), gr.update(value="")),
            outputs=[msg, user_prompt]
        )

        items_output.change(
            update_chat_content,
            inputs=[items_output, use_content, use_summary, use_prompt, item_mapping],
            outputs=[media_content, selected_parts]
        )

        for checkbox in [use_content, use_summary, use_prompt]:
            checkbox.change(
                update_selected_parts,
                inputs=[use_content, use_summary, use_prompt],
                outputs=[selected_parts]
            )



def create_chat_interface_four():
    custom_css = """
    .chatbot-container .message-wrap .message {
        font-size: 14px !important;
    }
    .chat-window {
        height: 400px;
        overflow-y: auto;
    }
    """

    with gr.TabItem("Four Independent API Chats", visible=True):
        gr.Markdown("# Four Independent API Chat Interfaces")

        with gr.Row():
            with gr.Column():
                preset_prompt = gr.Dropdown(
                    label="Select Preset Prompt",
                    choices=load_preset_prompts(),
                    visible=True
                )
                user_prompt = gr.Textbox(
                    label="Modify Prompt",
                    lines=3
                )
            with gr.Column():
                gr.Markdown("Scroll down for the chat windows...")

        chat_interfaces = []

        def create_single_chat_interface(index, user_prompt_component):
            with gr.Column():
                gr.Markdown(f"### Chat Window {index + 1}")
                api_endpoint = gr.Dropdown(
                    label=f"API Endpoint {index + 1}",
                    choices=[
                        "Local-LLM", "OpenAI", "Anthropic", "Cohere", "Groq",
                        "DeepSeek", "Mistral", "OpenRouter", "Llama.cpp", "Kobold",
                        "Ooba", "Tabbyapi", "VLLM", "ollama", "HuggingFace"
                    ]
                )
                api_key = gr.Textbox(
                    label=f"API Key {index + 1} (if required)",
                    type="password"
                )
                temperature = gr.Slider(
                    label=f"Temperature {index + 1}",
                    minimum=0.0,
                    maximum=1.0,
                    step=0.05,
                    value=0.7
                )
                chatbot = gr.Chatbot(height=400, elem_classes="chat-window")
                msg = gr.Textbox(label=f"Enter your message for Chat {index + 1}")
                submit = gr.Button(f"Submit to Chat {index + 1}")
                regenerate_button = gr.Button(f"Regenerate Last Message {index + 1}")
                clear_chat_button = gr.Button(f"Clear Chat {index + 1}")

                # State to maintain chat history
                chat_history = gr.State([])

                # Append to chat_interfaces list
                chat_interfaces.append({
                    'api_endpoint': api_endpoint,
                    'api_key': api_key,
                    'temperature': temperature,
                    'chatbot': chatbot,
                    'msg': msg,
                    'submit': submit,
                    'regenerate_button': regenerate_button,
                    'clear_chat_button': clear_chat_button,
                    'chat_history': chat_history
                })

        # Create four chat interfaces arranged in a 2x2 grid
        with gr.Row():
            for i in range(2):
                with gr.Column():
                    for j in range(2):
                        create_single_chat_interface(i * 2 + j, user_prompt)

        # Update user_prompt based on preset_prompt selection
        preset_prompt.change(
            fn=update_user_prompt,
            inputs=preset_prompt,
            outputs=user_prompt
        )

        def chat_wrapper_single(message, chat_history, api_endpoint, api_key, temperature, user_prompt):
            logging.debug(f"Chat Wrapper Single - Message: {message}, Chat History: {chat_history}")

            new_msg, new_history, _ = chat_wrapper(
                message,
                chat_history,
                {},  # Empty media_content
                [],  # Empty selected_parts
                api_endpoint,
                api_key,
                user_prompt,  # custom_prompt
                None,  # conversation_id
                False,  # save_conversation
                temperature,  # temperature
                system_prompt="",  # system_prompt
                max_tokens=None,
                top_p=None,
                frequency_penalty=None,
                presence_penalty=None,
                stop_sequence=None
            )
            if "API request failed" not in new_msg:
                chat_history.append((message, new_msg))
            else:
                logging.error(f"API request failed: {new_msg}")

            return "", chat_history, chat_history

        def regenerate_last_message(chat_history, api_endpoint, api_key, temperature, user_prompt):
            if not chat_history:
                return chat_history, chat_history, "No messages to regenerate."

            last_user_message, _ = chat_history[-1]

            new_msg, new_history, _ = chat_wrapper(
                last_user_message,
                chat_history[:-1],
                {},  # Empty media_content
                [],  # Empty selected_parts
                api_endpoint,
                api_key,
                user_prompt,  # custom_prompt
                None,  # conversation_id
                False,  # save_conversation
                temperature,  # temperature
                system_prompt="",  # system_prompt
                max_tokens=None,
                top_p=None,
                frequency_penalty=None,
                presence_penalty=None,
                stop_sequence=None
            )

            if "API request failed" not in new_msg:
                new_history.append((last_user_message, new_msg))
                return new_history, new_history, "Last message regenerated successfully."
            else:
                logging.error(f"API request failed during regeneration: {new_msg}")
                return chat_history, chat_history, f"Failed to regenerate: {new_msg}"

        # Attach click events for each chat interface
        for interface in chat_interfaces:
            interface['submit'].click(
                chat_wrapper_single,
                inputs=[
                    interface['msg'],
                    interface['chat_history'],
                    interface['api_endpoint'],
                    interface['api_key'],
                    interface['temperature'],
                    user_prompt
                ],
                outputs=[
                    interface['msg'],
                    interface['chatbot'],
                    interface['chat_history']
                ]
            )

            interface['regenerate_button'].click(
                regenerate_last_message,
                inputs=[
                    interface['chat_history'],
                    interface['api_endpoint'],
                    interface['api_key'],
                    interface['temperature'],
                    user_prompt
                ],
                outputs=[
                    interface['chatbot'],
                    interface['chat_history'],
                    gr.Textbox(label="Regenerate Status")
                ]
            )

            interface['clear_chat_button'].click(
                clear_chat_single,
                inputs=[],
                outputs=[interface['chatbot'], interface['chat_history']]
            )


def chat_wrapper_single(message, chat_history, chatbot, api_endpoint, api_key, temperature, media_content,
                        selected_parts, conversation_id, save_conversation, user_prompt):
    new_msg, new_history, new_conv_id = chat_wrapper(
        message, chat_history, media_content, selected_parts,
        api_endpoint, api_key, user_prompt, conversation_id,
        save_conversation, temperature, system_prompt=""
    )

    if new_msg:
        updated_chatbot = chatbot + [(message, new_msg)]
    else:
        updated_chatbot = chatbot

    return new_msg, updated_chatbot, new_history, new_conv_id


# FIXME - Finish implementing functions + testing/valdidation
def create_chat_management_tab():
    with gr.TabItem("Chat Management", visible=True):
        gr.Markdown("# Chat Management")

        with gr.Row():
            search_query = gr.Textbox(label="Search Conversations")
            search_button = gr.Button("Search")

        conversation_list = gr.Dropdown(label="Select Conversation", choices=[])
        conversation_mapping = gr.State({})

        with gr.Tabs():
            with gr.TabItem("Edit", visible=True):
                chat_content = gr.TextArea(label="Chat Content (JSON)", lines=20, max_lines=50)
                save_button = gr.Button("Save Changes")
                delete_button = gr.Button("Delete Conversation", variant="stop")

            with gr.TabItem("Preview", visible=True):
                chat_preview = gr.HTML(label="Chat Preview")
        result_message = gr.Markdown("")

        def search_conversations(query):
            conversations = search_chat_conversations(query)
            choices = [f"{conv['conversation_name']} (Media: {conv['media_title']}, ID: {conv['id']})" for conv in
                       conversations]
            mapping = {choice: conv['id'] for choice, conv in zip(choices, conversations)}
            return gr.update(choices=choices), mapping

        def load_conversations(selected, conversation_mapping):
            logging.info(f"Selected: {selected}")
            logging.info(f"Conversation mapping: {conversation_mapping}")

            try:
                if selected and selected in conversation_mapping:
                    conversation_id = conversation_mapping[selected]
                    messages = get_chat_messages(conversation_id)
                    conversation_data = {
                        "conversation_id": conversation_id,
                        "messages": messages
                    }
                    json_content = json.dumps(conversation_data, indent=2)

                    # Create HTML preview
                    html_preview = "<div style='max-height: 500px; overflow-y: auto;'>"
                    for msg in messages:
                        sender_style = "background-color: #e6f3ff;" if msg[
                                                                           'sender'] == 'user' else "background-color: #f0f0f0;"
                        html_preview += f"<div style='margin-bottom: 10px; padding: 10px; border-radius: 5px; {sender_style}'>"
                        html_preview += f"<strong>{msg['sender']}:</strong> {html.escape(msg['message'])}<br>"
                        html_preview += f"<small>Timestamp: {msg['timestamp']}</small>"
                        html_preview += "</div>"
                    html_preview += "</div>"

                    logging.info("Returning json_content and html_preview")
                    return json_content, html_preview
                else:
                    logging.warning("No conversation selected or not in mapping")
                    return "", "<p>No conversation selected</p>"
            except Exception as e:
                logging.error(f"Error in load_conversations: {str(e)}")
                return f"Error: {str(e)}", "<p>Error loading conversation</p>"

        def validate_conversation_json(content):
            try:
                data = json.loads(content)
                if not isinstance(data, dict):
                    return False, "Invalid JSON structure: root should be an object"
                if "conversation_id" not in data or not isinstance(data["conversation_id"], int):
                    return False, "Missing or invalid conversation_id"
                if "messages" not in data or not isinstance(data["messages"], list):
                    return False, "Missing or invalid messages array"
                for msg in data["messages"]:
                    if not all(key in msg for key in ["sender", "message"]):
                        return False, "Invalid message structure: missing required fields"
                return True, data
            except json.JSONDecodeError as e:
                return False, f"Invalid JSON: {str(e)}"

        def save_conversation(selected, conversation_mapping, content):
            if not selected or selected not in conversation_mapping:
                return "Please select a conversation before saving.", "<p>No changes made</p>"

            conversation_id = conversation_mapping[selected]
            is_valid, result = validate_conversation_json(content)

            if not is_valid:
                return f"Error: {result}", "<p>No changes made due to error</p>"

            conversation_data = result
            if conversation_data["conversation_id"] != conversation_id:
                return "Error: Conversation ID mismatch.", "<p>No changes made due to ID mismatch</p>"

            try:
                with db.get_connection() as conn:
                    conn.execute("BEGIN TRANSACTION")
                    cursor = conn.cursor()

                    # Backup original conversation
                    cursor.execute("SELECT * FROM ChatMessages WHERE conversation_id = ?", (conversation_id,))
                    original_messages = cursor.fetchall()
                    backup_data = json.dumps({"conversation_id": conversation_id, "messages": original_messages})

                    # You might want to save this backup_data somewhere

                    # Delete existing messages
                    cursor.execute("DELETE FROM ChatMessages WHERE conversation_id = ?", (conversation_id,))

                    # Insert updated messages
                    for message in conversation_data["messages"]:
                        cursor.execute('''
                            INSERT INTO ChatMessages (conversation_id, sender, message, timestamp)
                            VALUES (?, ?, ?, COALESCE(?, CURRENT_TIMESTAMP))
                        ''', (conversation_id, message["sender"], message["message"], message.get("timestamp")))

                    conn.commit()

                    # Create updated HTML preview
                    html_preview = "<div style='max-height: 500px; overflow-y: auto;'>"
                    for msg in conversation_data["messages"]:
                        sender_style = "background-color: #e6f3ff;" if msg[
                                                                           'sender'] == 'user' else "background-color: #f0f0f0;"
                        html_preview += f"<div style='margin-bottom: 10px; padding: 10px; border-radius: 5px; {sender_style}'>"
                        html_preview += f"<strong>{msg['sender']}:</strong> {html.escape(msg['message'])}<br>"
                        html_preview += f"<small>Timestamp: {msg.get('timestamp', 'N/A')}</small>"
                        html_preview += "</div>"
                    html_preview += "</div>"

                    return "Conversation updated successfully.", html_preview
            except sqlite3.Error as e:
                conn.rollback()
                logging.error(f"Database error in save_conversation: {e}")
                return f"Error updating conversation: {str(e)}", "<p>Error occurred while saving</p>"
            except Exception as e:
                conn.rollback()
                logging.error(f"Unexpected error in save_conversation: {e}")
                return f"Unexpected error: {str(e)}", "<p>Unexpected error occurred</p>"

        def delete_conversation(selected, conversation_mapping):
            if not selected or selected not in conversation_mapping:
                return "Please select a conversation before deleting.", "<p>No changes made</p>", gr.update(choices=[])

            conversation_id = conversation_mapping[selected]

            try:
                with db.get_connection() as conn:
                    cursor = conn.cursor()

                    # Delete messages associated with the conversation
                    cursor.execute("DELETE FROM ChatMessages WHERE conversation_id = ?", (conversation_id,))

                    # Delete the conversation itself
                    cursor.execute("DELETE FROM ChatConversations WHERE id = ?", (conversation_id,))

                    conn.commit()

                # Update the conversation list
                remaining_conversations = [choice for choice in conversation_mapping.keys() if choice != selected]
                updated_mapping = {choice: conversation_mapping[choice] for choice in remaining_conversations}

                return "Conversation deleted successfully.", "<p>Conversation deleted</p>", gr.update(choices=remaining_conversations)
            except sqlite3.Error as e:
                conn.rollback()
                logging.error(f"Database error in delete_conversation: {e}")
                return f"Error deleting conversation: {str(e)}", "<p>Error occurred while deleting</p>", gr.update()
            except Exception as e:
                conn.rollback()
                logging.error(f"Unexpected error in delete_conversation: {e}")
                return f"Unexpected error: {str(e)}", "<p>Unexpected error occurred</p>", gr.update()

        def parse_formatted_content(formatted_content):
            lines = formatted_content.split('\n')
            conversation_id = int(lines[0].split(': ')[1])
            timestamp = lines[1].split(': ')[1]
            history = []
            current_role = None
            current_content = None
            for line in lines[3:]:
                if line.startswith("Role: "):
                    if current_role is not None:
                        history.append({"role": current_role, "content": ["", current_content]})
                    current_role = line.split(': ')[1]
                elif line.startswith("Content: "):
                    current_content = line.split(': ', 1)[1]
            if current_role is not None:
                history.append({"role": current_role, "content": ["", current_content]})
            return json.dumps({
                "conversation_id": conversation_id,
                "timestamp": timestamp,
                "history": history
            }, indent=2)

        search_button.click(
            search_conversations,
            inputs=[search_query],
            outputs=[conversation_list, conversation_mapping]
        )

        conversation_list.change(
            load_conversations,
            inputs=[conversation_list, conversation_mapping],
            outputs=[chat_content, chat_preview]
        )

        save_button.click(
            save_conversation,
            inputs=[conversation_list, conversation_mapping, chat_content],
            outputs=[result_message, chat_preview]
        )

        delete_button.click(
            delete_conversation,
            inputs=[conversation_list, conversation_mapping],
            outputs=[result_message, chat_preview, conversation_list]
        )

    return search_query, search_button, conversation_list, conversation_mapping, chat_content, save_button, delete_button, result_message, chat_preview



# Mock function to simulate LLM processing
def process_with_llm(workflow, context, prompt, api_endpoint, api_key):
    api_key_snippet = api_key[:5] + "..." if api_key else "Not provided"
    return f"LLM output using {api_endpoint} (API Key: {api_key_snippet}) for {workflow} with context: {context[:30]}... and prompt: {prompt[:30]}..."


#
# End of Chat_ui.py
#######################################################################################################################