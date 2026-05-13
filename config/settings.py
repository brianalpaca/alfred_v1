import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()


def require_env(key: str) -> str:
    val = os.getenv(key)
    if not val:
        raise EnvironmentError(f"Required env var missing: {key}")
    return val


ANTHROPIC_API_KEY: str = require_env("ANTHROPIC_API_KEY")
MODEL: str = os.getenv("MODEL", "claude-sonnet-4-6")
OBSIDIAN_VAULT_PATH: Path = Path(os.getenv("OBSIDIAN_VAULT_PATH", "~/obsidian-brain")).expanduser()
ALFRED_DB_PATH: str = os.getenv("ALFRED_DB_PATH", "data/alfred.db")
ARCHIVES_PATH: Path = Path(os.getenv("ALFRED_ARCHIVES_PATH", "archives/"))
CHUNK_TOKEN_THRESHOLD: int = int(os.getenv("CHUNK_TOKEN_THRESHOLD", "8000"))
MAX_RETRIEVAL_RESULTS: int = 3
