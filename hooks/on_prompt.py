#!/usr/bin/env python3
"""
UserPromptSubmit hook.
Receives JSON on stdin, outputs RAG context on stdout.
"""
import json
import sys
import os
from datetime import datetime, timezone
from pathlib import Path

# Allow imports from project root
sys.path.insert(0, str(Path(__file__).parent.parent))

from alfred.db import init_db, get_connection
from alfred.retriever import build_retrieval_context


def _get_or_create_session(session_id: str) -> int:
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT id FROM sessions WHERE claude_session_id = ?", (session_id,)
        ).fetchone()
        if row:
            return row["id"]
        cursor = conn.execute(
            "INSERT INTO sessions (claude_session_id, started_at) VALUES (?, ?)",
            (session_id, datetime.now(timezone.utc).isoformat()),
        )
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


def _log_prompt(session_db_id: int, prompt: str) -> None:
    conn = get_connection()
    try:
        conn.execute(
            "INSERT INTO ideas (content, session_id, created_at) VALUES (?, ?, ?)",
            (prompt, session_db_id, datetime.now(timezone.utc).isoformat()),
        )
        conn.commit()
    finally:
        conn.close()


def main():
    init_db()

    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(0)

    prompt = payload.get("prompt", "")
    session_id = payload.get("session_id", "unknown")

    session_db_id = _get_or_create_session(session_id)
    _log_prompt(session_db_id, prompt)

    context = build_retrieval_context(prompt)
    if context:
        print(context)


if __name__ == "__main__":
    main()
