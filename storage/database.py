"""storage/database.py — SQLite operations for Engineer Sandbox."""
import sqlite3
import json
import os

DB_PATH = "storage/sandbox.db"

def get_connection():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    return sqlite3.connect(DB_PATH)

def setup_db():
    """Initializes the SQLite database with required tables."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS player_performance (
            scenario_type TEXT PRIMARY KEY,
            avg_score REAL,
            last_5 TEXT,
            count INTEGER
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS player_profile (
            id INTEGER PRIMARY KEY,
            role TEXT,
            reputation_json TEXT,
            decision_patterns TEXT
        )
    """)
    # Insert default profile if none exists
    cursor.execute("SELECT count(*) FROM player_profile")
    if cursor.fetchone()[0] == 0:
        cursor.execute(
            "INSERT INTO player_profile (role, reputation_json, decision_patterns) VALUES (?, ?, ?)",
            ("Tech Lead", "{}", "[]")
        )

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS scenario_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT,
            title TEXT,
            overall_score REAL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

def get_performance_profile() -> dict:
    """Returns a dictionary of performance by scenario type."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT scenario_type, avg_score, last_5, count FROM player_performance")
    rows = cursor.fetchall()
    conn.close()
    
    perf = {}
    for row in rows:
        perf[row[0]] = {
            "avg_score": row[1],
            "last_5": json.loads(row[2]),
            "count": row[3]
        }
    return perf

def get_player_profile() -> dict:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT role, reputation_json, decision_patterns FROM player_profile ORDER BY id DESC LIMIT 1")
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return {
            "player_role": row[0],
            "reputation_json": json.loads(row[1]) if row[1] else {},
            "decision_patterns": json.loads(row[2]) if row[2] else []
        }
    return {"player_role": "Tech Lead", "reputation_json": {}, "decision_patterns": []}

def get_recent_scenario_types(limit: int) -> list:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT type FROM scenario_history ORDER BY timestamp DESC LIMIT ?", (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [row[0] for row in rows]
    
def get_scenario_count() -> int:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM scenario_history")
    count = cursor.fetchone()[0]
    conn.close()
    return count
