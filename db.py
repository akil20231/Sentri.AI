import sqlite3
from pathlib import Path
from typing import Any, Optional

DB_PATH = Path("agentguard.sqlite")

def connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL;")
    return conn

def init_db() -> None:
    conn = connect()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ts INTEGER NOT NULL,
        guild_id INTEGER NOT NULL,
        channel_id INTEGER NOT NULL,
        user_id INTEGER NOT NULL,
        message_id INTEGER NOT NULL,
        content TEXT NOT NULL,
        has_link INTEGER NOT NULL,
        mentions_count INTEGER NOT NULL
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS decisions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ts INTEGER NOT NULL,
        guild_id INTEGER NOT NULL,
        channel_id INTEGER NOT NULL,
        user_id INTEGER NOT NULL,
        message_id INTEGER NOT NULL,
        agent_score REAL NOT NULL,
        harm_score REAL NOT NULL,
        final_risk REAL NOT NULL,
        action TEXT NOT NULL,
        reasons TEXT NOT NULL
    );
    """)

    conn.commit()
    conn.close()

def insert_event(
    ts: int, guild_id: int, channel_id: int, user_id: int, message_id: int,
    content: str, has_link: bool, mentions_count: int
) -> None:
    conn = connect()
    conn.execute(
        "INSERT INTO events (ts,guild_id,channel_id,user_id,message_id,content,has_link,mentions_count) VALUES (?,?,?,?,?,?,?,?)",
        (ts, guild_id, channel_id, user_id, message_id, content, int(has_link), mentions_count)
    )
    conn.commit()
    conn.close()

def insert_decision(
    ts: int, guild_id: int, channel_id: int, user_id: int, message_id: int,
    agent_score: float, harm_score: float, final_risk: float, action: str, reasons: str
) -> None:
    conn = connect()
    conn.execute(
        "INSERT INTO decisions (ts,guild_id,channel_id,user_id,message_id,agent_score,harm_score,final_risk,action,reasons) VALUES (?,?,?,?,?,?,?,?,?,?)",
        (ts, guild_id, channel_id, user_id, message_id, agent_score, harm_score, final_risk, action, reasons)
    )
    conn.commit()
    conn.close()
