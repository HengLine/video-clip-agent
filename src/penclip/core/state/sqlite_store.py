"""SQLiteStateStore — SQLite-backed state persistence (V0.2)."""

import json
import sqlite3
import threading
from typing import Any, Dict, List, Optional

from penclip.core.state.state_store import StateStore
from penclip.logger import debug, error


class SQLiteStateStore(StateStore):
    def __init__(self, db_path: str = "data/state.db"):
        self._db_path = db_path
        self._lock = threading.Lock()
        self._init_db()

    def _init_db(self):
        try:
            with sqlite3.connect(self._db_path) as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS state (
                        session_id TEXT PRIMARY KEY,
                        state_json TEXT NOT NULL,
                        updated_at TEXT DEFAULT (datetime('now'))
                    )
                """)
        except Exception as e:
            error(f"SQLiteStateStore init failed: {e}")

    def get(self, session_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            try:
                with sqlite3.connect(self._db_path) as conn:
                    row = conn.execute("SELECT state_json FROM state WHERE session_id = ?", (session_id,)).fetchone()
                    if row:
                        return json.loads(row[0])
            except Exception as e:
                error(f"SQLiteStateStore get error: {e}")
        return None

    def put(self, session_id: str, state: Dict[str, Any]) -> None:
        with self._lock:
            try:
                with sqlite3.connect(self._db_path) as conn:
                    conn.execute(
                        "INSERT OR REPLACE INTO state (session_id, state_json, updated_at) VALUES (?, ?, datetime('now'))",
                        (session_id, json.dumps(state)),
                    )
            except Exception as e:
                error(f"SQLiteStateStore put error: {e}")

    def delete(self, session_id: str) -> bool:
        with self._lock:
            try:
                with sqlite3.connect(self._db_path) as conn:
                    conn.execute("DELETE FROM state WHERE session_id = ?", (session_id,))
                    return conn.total_changes > 0
            except Exception as e:
                error(f"SQLiteStateStore delete error: {e}")
        return False

    def list_sessions(self) -> List[str]:
        with self._lock:
            try:
                with sqlite3.connect(self._db_path) as conn:
                    return [r[0] for r in conn.execute("SELECT session_id FROM state").fetchall()]
            except Exception:
                return []
