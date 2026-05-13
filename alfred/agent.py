import sqlite3
from datetime import datetime, timezone
from typing import Optional

import anthropic
import tiktoken

from config.settings import (
    ANTHROPIC_API_KEY,
    CHUNK_TOKEN_THRESHOLD,
    MODEL,
)
from .archiver import archive_conversation
from .db import get_connection
from .retriever import build_retrieval_context


_SYSTEM_PROMPT = """\
You are Alfred, a personal productivity and execution assistant.
You help the user capture ideas, plan tasks, execute actions, and track progress.
You remember past sessions and learn from them to be more efficient over time.
Be direct, concise, and action-oriented. When given a task, execute it.
"""

_ENCODER = tiktoken.get_encoding("cl100k_base")


def _count_tokens(text: str) -> int:
    return len(_ENCODER.encode(text))


def _count_messages_tokens(messages: list[dict]) -> int:
    return sum(_count_tokens(m["content"]) for m in messages)


class AlfredAgent:
    def __init__(self):
        self.client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        self.messages: list[dict] = []
        self.session_id: Optional[int] = self._create_session()
        self.total_tokens: int = 0

    def _create_session(self) -> int:
        conn = get_connection()
        try:
            cursor = conn.execute(
                "INSERT INTO sessions (started_at) VALUES (?)",
                (datetime.now(timezone.utc).isoformat(),),
            )
            conn.commit()
            return cursor.lastrowid
        finally:
            conn.close()

    def _close_session(self) -> None:
        conn = get_connection()
        try:
            conn.execute(
                "UPDATE sessions SET ended_at = ?, token_count = ? WHERE id = ?",
                (datetime.now(timezone.utc).isoformat(), self.total_tokens, self.session_id),
            )
            conn.commit()
        finally:
            conn.close()

    def _maybe_archive(self) -> None:
        if _count_messages_tokens(self.messages) >= CHUNK_TOKEN_THRESHOLD:
            print("\n[Alfred] Archiving conversation chunk...\n")
            archive_conversation(
                messages=self.messages,
                session_id=self.session_id,
                token_count=self.total_tokens,
                client=self.client,
            )
            self.messages = []

    def _build_system(self, user_input: str) -> str:
        retrieval = build_retrieval_context(user_input)
        if retrieval:
            return f"{_SYSTEM_PROMPT}\n\n{retrieval}"
        return _SYSTEM_PROMPT

    def chat(self, user_input: str) -> str:
        self.messages.append({"role": "user", "content": user_input})

        system = self._build_system(user_input)

        try:
            response = self.client.messages.create(
                model=MODEL,
                max_tokens=4096,
                system=[
                    {
                        "type": "text",
                        "text": system,
                        "cache_control": {"type": "ephemeral"},
                    }
                ],
                messages=self.messages,
            )
        except anthropic.APIError as e:
            self.messages.pop()
            raise RuntimeError(f"API error: {e}") from e

        assistant_text = response.content[0].text
        self.messages.append({"role": "assistant", "content": assistant_text})

        self.total_tokens += response.usage.input_tokens + response.usage.output_tokens

        self._maybe_archive()

        return assistant_text

    def end_session(self) -> None:
        if self.messages:
            archive_conversation(
                messages=self.messages,
                session_id=self.session_id,
                token_count=self.total_tokens,
                client=self.client,
            )
        self._close_session()
