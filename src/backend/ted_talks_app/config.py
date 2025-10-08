"""config.py - All settings in one place"""
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data" / "transcripts" / "ted_talks"

# Model
MODEL_NAME = "Falconsai/fear_mongering_detection"
DEFAULT_FEAR_THRESHOLD = 0.6

# Text processing
MAX_CHARS = 400

MAX_SENTENCES = 5


# UI
PREVIEW_CHARS = 500