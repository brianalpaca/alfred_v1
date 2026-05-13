from .db import get_connection
from config.settings import MAX_RETRIEVAL_RESULTS


def search_archives(query: str, limit: int = MAX_RETRIEVAL_RESULTS) -> list[dict]:
    conn = get_connection()
    try:
        rows = conn.execute(
            """
            SELECT session_id, qmd_path, summary, topics,
                   snippet(archives_fts, 2, '[', ']', '...', 20) AS snippet
            FROM archives_fts
            WHERE archives_fts MATCH ?
            ORDER BY rank
            LIMIT ?
            """,
            (query, limit),
        ).fetchall()
    finally:
        conn.close()
    return [dict(r) for r in rows]


def build_retrieval_context(query: str) -> str:
    results = search_archives(query)
    if not results:
        return ""

    parts = ["## Relevant Past Context\n"]
    for r in results:
        parts.append(f"**Session {r['session_id']}** | Topics: {r['topics']}")
        parts.append(f"Summary: {r['summary']}")
        parts.append(f"Relevant excerpt: {r['snippet']}\n")

    return "\n".join(parts)
