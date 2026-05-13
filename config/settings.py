import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

ALFRED_DB_PATH: str = os.getenv("ALFRED_DB_PATH", str(Path.home() / "alfred_v1/data/alfred.db"))
ARCHIVES_PATH: Path = Path(os.getenv("ALFRED_ARCHIVES_PATH", str(Path.home() / "alfred_v1/archives")))
CHUNK_TOKEN_THRESHOLD: int = int(os.getenv("CHUNK_TOKEN_THRESHOLD", "6000"))
MAX_RETRIEVAL_RESULTS: int = 3
MODEL: str = os.getenv("MODEL", "claude-sonnet-4-6")
