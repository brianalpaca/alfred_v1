import re
from datetime import datetime
from pathlib import Path
from typing import Optional

import anthropic

from config.settings import ARCHIVES_PATH, MODEL
from .db import get_connection


_ARCHIVE_SYSTEM = """\
You are summarizing a conversation for long-term memory. Output structured QMD.

Format exactly:
---
title: Session Archive
date: {date}
topics: [topic1, topic2]
tasks_completed:
  - task description
decisions:
  - decision description
token_count: {token_count}
---

## Summary
2-3 sentence overview.

## Key Decisions
- bullet list

## Patterns / Preferences Learned
- bullet list

## Commands / Code Used
```
relevant code or commands only
```
"""


def archive_conversation(
    messages: list[dict],
    session_id: int,
    token_count: int,
    client: anthropic.Anthropic,
) -> Optional[str]:
    ARCHIVES_PATH.mkdir(parents=True, exist_ok=True)

    date_str = datetime.now().strftime("%Y-%m-%d_%H-%M")
    qmd_path = ARCHIVES_PATH / f"session_{date_str}.qmd"

    conversation_text = "\n\n".join(
        f"**{m['role'].upper()}:** {m['content']}" for m in messages
    )

    system = _ARCHIVE_SYSTEM.format(
        date=datetime.now().strftime("%Y-%m-%d"),
        token_count=token_count,
    )

    try:
        response = client.messages.create(
            model=MODEL,
            max_tokens=2048,
            system=system,
            messages=[{"role": "user", "content": f"Summarize:\n\n{conversation_text}"}],
        )
    except anthropic.APIError as e:
        raise RuntimeError(f"Archive summarization failed: {e}") from e

    qmd_content = response.content[0].text
    qmd_path.write_text(qmd_content, encoding="utf-8")

    _index_archive(session_id, str(qmd_path), qmd_content)
    return str(qmd_path)


def _index_archive(session_id: int, qmd_path: str, content: str) -> None:
    topics_match = re.search(r"topics:\s*\[([^\]]+)\]", content)
    topics = topics_match.group(1) if topics_match else ""

    summary_match = re.search(r"## Summary\n(.+?)(?=\n##|\Z)", content, re.DOTALL)
    summary = summary_match.group(1).strip() if summary_match else ""

    conn = get_connection()
    try:
        conn.execute(
            "INSERT INTO archives_fts (session_id, qmd_path, content, topics, summary) VALUES (?, ?, ?, ?, ?)",
            (session_id, qmd_path, content, topics, summary),
        )
        conn.execute(
            "UPDATE sessions SET qmd_path = ?, summary = ?, topics = ? WHERE id = ?",
            (qmd_path, summary, topics, session_id),
        )
        conn.commit()
    finally:
        conn.close()
