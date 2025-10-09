"""config.py - All settings in one place"""
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data" / "transcripts" / "ted_talks"

# Model
MODEL_NAME = "Falconsai/fear_mongering_detection"
DEFAULT_FEAR_THRESHOLD = 0.6

# Text processing
MAX_CHARS = 350

MAX_SENTENCES = 5


# UI
PREVIEW_CHARS = 500

DEFAULT_SMOOTHING_WINDOW = 7
DEFAULT_CHART_TYPE = "Area Chart"

FIXED_DURATION = 600  # 10 minutes
