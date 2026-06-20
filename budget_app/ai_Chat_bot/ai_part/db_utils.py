import sqlite3
import json
import random
from pydantic import TypeAdapter
from pydantic_ai.messages import ModelMessage

DB_PATH = "chat_history.db"
messages_adapter = TypeAdapter(list[ModelMessage])

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # Table for sessions with username mapping
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sessions (
            session_id TEXT PRIMARY KEY,
            username TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    # Table for histories (storing full message list as JSON blob)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS chat_history (
            session_id TEXT PRIMARY KEY,
            history_json TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (session_id) REFERENCES sessions (session_id)
        )
    ''')
    conn.commit()
    conn.close()

def save_history(session_id, messages):
    """Serializes the list of ModelMessage objects to JSON and saves to SQLite."""
    json_data = messages_adapter.dump_json(messages).decode("utf-8")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO chat_history (session_id, history_json, updated_at)
        VALUES (?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(session_id) DO UPDATE SET
            history_json = excluded.history_json,
            updated_at = CURRENT_TIMESTAMP
    ''', (session_id, json_data))
    conn.commit()
    conn.close()

def load_history(session_id):
    """Loads and deserializes the list of ModelMessage objects from SQLite."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT history_json FROM chat_history WHERE session_id = ?", (session_id,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return messages_adapter.validate_json(row[0])
    return []

def create_session(session_id, username="default_user"):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT OR IGNORE INTO sessions (session_id, username) VALUES (?, ?)",
        (session_id, username)
    )
    conn.commit()
    conn.close()

def list_user_sessions(username):
    """Retrieves all session IDs for a specific user."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT session_id FROM sessions WHERE username = ?", (username,))
    rows = cursor.fetchall()
    conn.close()
    return [row[0] for row in rows]


def get_or_create_session(username, first_message):
    existing_sessions = list_user_sessions(username)
    if existing_sessions:
        return existing_sessions[0]

    session_id = first_message.strip()[:120] or f"session_{username}"
    create_session(session_id, username)
    return session_id


def generate_session_id(first_message, username):
    prefix = first_message.strip().replace(" ", "_")[:40] or "session"
    suffix = random.randint(1000, 9999)
    return f"{prefix}_{suffix}_{username}"


def get_chat_history_by_user(username):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT s.session_id, s.created_at, h.history_json, h.updated_at
        FROM sessions s
        LEFT JOIN chat_history h ON s.session_id = h.session_id
        WHERE s.username = ?
        ORDER BY s.created_at ASC
        """,
        (username,),
    )
    rows = cursor.fetchall()
    conn.close()

    history = []
    for session_id, created_at, history_json, updated_at in rows:
        history.append(
            {
                "session_id": session_id,
                "created_at": created_at,
                "updated_at": updated_at,
                "messages": messages_adapter.validate_json(history_json) if history_json else [],
            }
        )
    return history
