import configparser
import logging
import os
from contextlib import contextmanager
from time import sleep
from typing import Tuple
import sqlite3
# 3rd-Party Libraries
from elasticsearch import Elasticsearch

############################################################################################################
#
# This file contains the DatabaseManager class, which is responsible for managing the database connection, i.e. either SQLite or Elasticsearch.

####
# The DatabaseManager class provides the following methods:
# - add_media: Add a new media item to the database
# - fetch_items_by_keyword: Fetch media items from the database based on a keyword
# - fetch_item_details: Fetch details of a specific media item from the database
# - update_media_content: Update the content of a specific media item in the database
# - search_and_display_items: Search for media items in the database and display the results
# - close_connection: Close the database connection
####

# Import your existing SQLite functions
from SQLite_DB import (
    update_media_content as sqlite_update_media_content,
    list_prompts as sqlite_list_prompts,
    search_and_display as sqlite_search_and_display,
    fetch_prompt_details as sqlite_fetch_prompt_details,
    keywords_browser_interface as sqlite_keywords_browser_interface,
    add_keyword as sqlite_add_keyword,
    delete_keyword as sqlite_delete_keyword,
    export_keywords_to_csv as sqlite_export_keywords_to_csv,
    ingest_article_to_db as sqlite_ingest_article_to_db,
    add_media_to_database as sqlite_add_media_to_database,
    import_obsidian_note_to_db as sqlite_import_obsidian_note_to_db,
    add_prompt as sqlite_add_prompt,
    delete_chat_message as sqlite_delete_chat_message,
    update_chat_message as sqlite_update_chat_message,
    add_chat_message as sqlite_add_chat_message,
    get_chat_messages as sqlite_get_chat_messages,
    search_chat_conversations as sqlite_search_chat_conversations,
    create_chat_conversation as sqlite_create_chat_conversation,
    save_chat_history_to_database as sqlite_save_chat_history_to_database,
    view_database as sqlite_view_database,
    get_transcripts as sqlite_get_transcripts,
    get_trashed_items as sqlite_get_trashed_items,
    user_delete_item as sqlite_user_delete_item,
    empty_trash as sqlite_empty_trash,
    create_automated_backup as sqlite_create_automated_backup,
    add_or_update_prompt as sqlite_add_or_update_prompt,
    load_prompt_details as sqlite_load_prompt_details,
    load_preset_prompts as sqlite_load_preset_prompts,
    insert_prompt_to_db as sqlite_insert_prompt_to_db,
    delete_prompt as sqlite_delete_prompt,
    search_and_display_items as sqlite_search_and_display_items,
    get_conversation_name as sqlite_get_conversation_name,
    add_media_with_keywords as sqlite_add_media_with_keywords,
    check_media_and_whisper_model as sqlite_check_media_and_whisper_model,
    DatabaseError
)

class Database:
    def __init__(self, db_path=None):
        self.db_path = db_path or os.getenv('DB_NAME', 'media_summary.db')
        self.pool = []
        self.pool_size = 10

    @contextmanager
    def get_connection(self):
        retry_count = 5
        retry_delay = 1
        conn = None
        while retry_count > 0:
            try:
                conn = self.pool.pop() if self.pool else sqlite3.connect(self.db_path, check_same_thread=False)
                yield conn
                self.pool.append(conn)
                return
            except sqlite3.OperationalError as e:
                if 'database is locked' in str(e):
                    logging.warning(f"Database is locked, retrying in {retry_delay} seconds...")
                    retry_count -= 1
                    sleep(retry_delay)
                else:
                    raise DatabaseError(f"Database error: {e}")
            except Exception as e:
                raise DatabaseError(f"Unexpected error: {e}")
            finally:
                # Ensure the connection is returned to the pool even on failure
                if conn and conn not in self.pool:
                    self.pool.append(conn)
        raise DatabaseError("Database is locked and retries have been exhausted")

    def execute_query(self, query: str, params: Tuple = ()) -> None:
        with self.get_connection() as conn:
            try:
                cursor = conn.cursor()
                cursor.execute(query, params)
                conn.commit()
            except sqlite3.Error as e:
                raise DatabaseError(f"Database error: {e}, Query: {query}")

    def close_all_connections(self):
        for conn in self.pool:
            conn.close()
        self.pool.clear()

def get_db_config():
    config = configparser.ConfigParser()
    config.read('config.txt')
    return {
        'type': config['Database']['type'],
        'sqlite_path': config.get('Database', 'sqlite_path', fallback='media_summary.db'),
        'elasticsearch_host': config.get('Database', 'elasticsearch_host', fallback='localhost'),
        'elasticsearch_port': config.getint('Database', 'elasticsearch_port', fallback=9200)
    }

db_config = get_db_config()
db_type = db_config['type']

if db_type == 'sqlite':
    # Use the config path if provided, otherwise fall back to default
    db = Database(db_config.get('sqlite_path'))
elif db_type == 'elasticsearch':
    es = Elasticsearch([{
        'host': db_config['elasticsearch_host'],
        'port': db_config['elasticsearch_port']
    }])
else:
    raise ValueError(f"Unsupported database type: {db_type}")

db_path = db_config['sqlite_path']

# Update this path to the directory where you want to store the database backups
backup_dir = os.environ.get('DB_BACKUP_DIR', 'path/to/backup/directory')




if db_type == 'sqlite':
    conn = sqlite3.connect(db_config['sqlite_path'])
    cursor = conn.cursor()
elif db_type == 'elasticsearch':
    es = Elasticsearch([{
        'host': db_config['elasticsearch_host'],
        'port': db_config['elasticsearch_port']
    }])
else:
    raise ValueError(f"Unsupported database type: {db_type}")

############################################################################################################
#
# DB-Searching functions

def view_database(*args, **kwargs):
    if db_type == 'sqlite':
        return sqlite_view_database(*args, **kwargs)
    elif db_type == 'elasticsearch':
        # Implement Elasticsearch version
        raise NotImplementedError("Elasticsearch version of add_media_with_keywords not yet implemented")

def search_and_display_items(*args, **kwargs):
    if db_type == 'sqlite':
        return sqlite_search_and_display_items(*args, **kwargs)
    elif db_type == 'elasticsearch':
        # Implement Elasticsearch version
        raise NotImplementedError("Elasticsearch version of add_media_with_keywords not yet implemented")

def search_and_display(*args, **kwargs):
    if db_type == 'sqlite':
        return sqlite_search_and_display(*args, **kwargs)
    elif db_type == 'elasticsearch':
        # Implement Elasticsearch version
        raise NotImplementedError("Elasticsearch version of add_media_with_keywords not yet implemented")

#
# End of DB-Searching functions
############################################################################################################

############################################################################################################
#
# Transcript-related Functions

def get_transcripts(*args, **kwargs):
    if db_type == 'sqlite':
        return sqlite_get_transcripts(*args, **kwargs)
    elif db_type == 'elasticsearch':
        # Implement Elasticsearch version
        raise NotImplementedError("Elasticsearch version of add_media_with_keywords not yet implemented")

#
# End of Transcript-related Functions
############################################################################################################

############################################################################################################
#
# DB-Ingestion functions

def add_media_to_database(*args, **kwargs):
    if db_type == 'sqlite':
        return sqlite_add_media_to_database(*args, **kwargs)
    elif db_type == 'elasticsearch':
        # Implement Elasticsearch version
        raise NotImplementedError("Elasticsearch version of add_media_with_keywords not yet implemented")


def import_obsidian_note_to_db(*args, **kwargs):
    if db_type == 'sqlite':
        return sqlite_import_obsidian_note_to_db(*args, **kwargs)
    elif db_type == 'elasticsearch':
        # Implement Elasticsearch version
        raise NotImplementedError("Elasticsearch version of add_media_with_keywords not yet implemented")

def update_media_content(*args, **kwargs):
    if db_type == 'sqlite':
        return sqlite_update_media_content(*args, **kwargs)
    elif db_type == 'elasticsearch':
        # Implement Elasticsearch version
        raise NotImplementedError("Elasticsearch version of add_media_with_keywords not yet implemented")

def add_media_with_keywords(*args, **kwargs):
    if db_type == 'sqlite':
        return sqlite_add_media_with_keywords(*args, **kwargs)
    elif db_type == 'elasticsearch':
        raise NotImplementedError("Elasticsearch version of add_media_with_keywords not yet implemented")

def check_media_and_whisper_model(*args, **kwargs):
    if db_type == 'sqlite':
        return sqlite_check_media_and_whisper_model(*args, **kwargs)
    elif db_type == 'elasticsearch':
        raise NotImplementedError("Elasticsearch version of check_media_and_whisper_model not yet implemented")

def ingest_article_to_db(url, title, author, content, keywords, summary, ingestion_date, custom_prompt):
    if db_type == 'sqlite':
        return sqlite_ingest_article_to_db(url, title, author, content, keywords, summary, ingestion_date, custom_prompt)
    elif db_type == 'elasticsearch':
        # Implement Elasticsearch version
        raise NotImplementedError("Elasticsearch version of ingest_article_to_db not yet implemented")
    else:
        raise ValueError(f"Unsupported database type: {db_type}")

#
# End of DB-Ingestion functions
############################################################################################################


############################################################################################################
#
# Prompt-related functions

def list_prompts(*args, **kwargs):
    if db_type == 'sqlite':
        return sqlite_list_prompts(*args, **kwargs)
    elif db_type == 'elasticsearch':
        # Implement Elasticsearch version
        raise NotImplementedError("Elasticsearch version of add_media_with_keywords not yet implemented")


def fetch_prompt_details(*args, **kwargs):
    if db_type == 'sqlite':
        return sqlite_fetch_prompt_details(*args, **kwargs)
    elif db_type == 'elasticsearch':
        # Implement Elasticsearch version
        raise NotImplementedError("Elasticsearch version of add_media_with_keywords not yet implemented")

def add_prompt(*args, **kwargs):
    if db_type == 'sqlite':
        return sqlite_add_prompt(*args, **kwargs)
    elif db_type == 'elasticsearch':
        # Implement Elasticsearch version
        raise NotImplementedError("Elasticsearch version of add_media_with_keywords not yet implemented")


def add_or_update_prompt(*args, **kwargs):
    if db_type == 'sqlite':
        return sqlite_add_or_update_prompt(*args, **kwargs)
    elif db_type == 'elasticsearch':
        # Implement Elasticsearch version
        raise NotImplementedError("Elasticsearch version of add_media_with_keywords not yet implemented")

def load_prompt_details(*args, **kwargs):
    if db_type == 'sqlite':
        return sqlite_load_prompt_details(*args, **kwargs)
    elif db_type == 'elasticsearch':
        # Implement Elasticsearch version
        raise NotImplementedError("Elasticsearch version of add_media_with_keywords not yet implemented")

def load_preset_prompts(*args, **kwargs):
    if db_type == 'sqlite':
        return sqlite_load_preset_prompts(*args, **kwargs)
    elif db_type == 'elasticsearch':
        # Implement Elasticsearch version
        raise NotImplementedError("Elasticsearch version of add_media_with_keywords not yet implemented")

def insert_prompt_to_db(*args, **kwargs):
    if db_type == 'sqlite':
        return sqlite_insert_prompt_to_db(*args, **kwargs)
    elif db_type == 'elasticsearch':
        # Implement Elasticsearch version
        raise NotImplementedError("Elasticsearch version of add_media_with_keywords not yet implemented")

def delete_prompt(*args, **kwargs):
    if db_type == 'sqlite':
        return sqlite_delete_prompt(*args, **kwargs)
    elif db_type == 'elasticsearch':
        # Implement Elasticsearch version
        raise NotImplementedError("Elasticsearch version of add_media_with_keywords not yet implemented")

#
# End of Prompt-related functions
############################################################################################################

############################################################################################################
#
# Keywords-related Functions

def keywords_browser_interface(*args, **kwargs):
    if db_type == 'sqlite':
        return sqlite_keywords_browser_interface(*args, **kwargs)
    elif db_type == 'elasticsearch':
        # Implement Elasticsearch version
        raise NotImplementedError("Elasticsearch version of add_media_with_keywords not yet implemented")

def add_keyword(*args, **kwargs):
    if db_type == 'sqlite':
        with db.get_connection() as conn:
            cursor = conn.cursor()
        return sqlite_add_keyword(*args, **kwargs)
    elif db_type == 'elasticsearch':
        # Implement Elasticsearch version
        raise NotImplementedError("Elasticsearch version of add_media_with_keywords not yet implemented")

def delete_keyword(*args, **kwargs):
    if db_type == 'sqlite':
        return sqlite_delete_keyword(*args, **kwargs)
    elif db_type == 'elasticsearch':
        # Implement Elasticsearch version
        raise NotImplementedError("Elasticsearch version of add_media_with_keywords not yet implemented")

def export_keywords_to_csv(*args, **kwargs):
    if db_type == 'sqlite':
        return sqlite_export_keywords_to_csv(*args, **kwargs)
    elif db_type == 'elasticsearch':
        # Implement Elasticsearch version
        raise NotImplementedError("Elasticsearch version of add_media_with_keywords not yet implemented")

#
# End of Keywords-related Functions
############################################################################################################

############################################################################################################
#
# Chat-related Functions

def delete_chat_message(*args, **kwargs):
    if db_type == 'sqlite':
        return sqlite_delete_chat_message(*args, **kwargs)
    elif db_type == 'elasticsearch':
        # Implement Elasticsearch version
        raise NotImplementedError("Elasticsearch version of add_media_with_keywords not yet implemented")

def update_chat_message(*args, **kwargs):
    if db_type == 'sqlite':
        return sqlite_update_chat_message(*args, **kwargs)
    elif db_type == 'elasticsearch':
        # Implement Elasticsearch version
        raise NotImplementedError("Elasticsearch version of add_media_with_keywords not yet implemented")

def add_chat_message(*args, **kwargs):
    if db_type == 'sqlite':
        return sqlite_add_chat_message(*args, **kwargs)
    elif db_type == 'elasticsearch':
        # Implement Elasticsearch version
        raise NotImplementedError("Elasticsearch version of add_media_with_keywords not yet implemented")

def get_chat_messages(*args, **kwargs):
    if db_type == 'sqlite':
        return sqlite_get_chat_messages(*args, **kwargs)
    elif db_type == 'elasticsearch':
        # Implement Elasticsearch version
        raise NotImplementedError("Elasticsearch version of add_media_with_keywords not yet implemented")

def search_chat_conversations(*args, **kwargs):
    if db_type == 'sqlite':
        return sqlite_search_chat_conversations(*args, **kwargs)
    elif db_type == 'elasticsearch':
        # Implement Elasticsearch version
        raise NotImplementedError("Elasticsearch version of add_media_with_keywords not yet implemented")

def create_chat_conversation(*args, **kwargs):
    if db_type == 'sqlite':
        return sqlite_create_chat_conversation(*args, **kwargs)
    elif db_type == 'elasticsearch':
        # Implement Elasticsearch version
        raise NotImplementedError("Elasticsearch version of add_media_with_keywords not yet implemented")

def save_chat_history_to_database(*args, **kwargs):
    if db_type == 'sqlite':
        return sqlite_save_chat_history_to_database(*args, **kwargs)
    elif db_type == 'elasticsearch':
        # Implement Elasticsearch version
        raise NotImplementedError("Elasticsearch version of add_media_with_keywords not yet implemented")

def get_conversation_name(*args, **kwargs):
    if db_type == 'sqlite':
        return sqlite_get_conversation_name(*args, **kwargs)
    elif db_type == 'elasticsearch':
        # Implement Elasticsearch version
        raise NotImplementedError("Elasticsearch version of add_media_with_keywords not yet implemented")

#
# End of Chat-related Functions
############################################################################################################

############################################################################################################
#
# Trash-related Functions

def get_trashed_items(*args, **kwargs):
    if db_type == 'sqlite':
        return sqlite_get_trashed_items(*args, **kwargs)
    elif db_type == 'elasticsearch':
        # Implement Elasticsearch version
        raise NotImplementedError("Elasticsearch version of add_media_with_keywords not yet implemented")

def user_delete_item(*args, **kwargs):
    if db_type == 'sqlite':
        return sqlite_user_delete_item(*args, **kwargs)
    elif db_type == 'elasticsearch':
        # Implement Elasticsearch version
        raise NotImplementedError("Elasticsearch version of add_media_with_keywords not yet implemented")

def empty_trash(*args, **kwargs):
    if db_type == 'sqlite':
        return sqlite_empty_trash(*args, **kwargs)
    elif db_type == 'elasticsearch':
        # Implement Elasticsearch version
        raise NotImplementedError("Elasticsearch version of add_media_with_keywords not yet implemented")

#
# End of Trash-related Functions
############################################################################################################

############################################################################################################
#
# DB-Backup Functions

def create_automated_backup(*args, **kwargs):
    if db_type == 'sqlite':
        return sqlite_create_automated_backup(*args, **kwargs)
    elif db_type == 'elasticsearch':
        # Implement Elasticsearch version
        raise NotImplementedError("Elasticsearch version of add_media_with_keywords not yet implemented")

#
# End of DB-Backup Functions
############################################################################################################

############################################################################################################
#
# Function to close the database connection for SQLite

def close_connection():
    if db_type == 'sqlite':
        db.close_all_connections()
    # Elasticsearch doesn't need explicit closing

#
# End of file
############################################################################################################