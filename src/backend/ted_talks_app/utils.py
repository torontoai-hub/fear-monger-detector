"""utils.py - Text processing and timestamps"""
import re
import datetime
import pandas as pd
from config import MAX_CHARS


def segment_text(text, max_chars=MAX_CHARS):
    """Split text into paragraphs by sentence boundaries"""
    sentences = re.split(r'(?<=[.!?])\s+', text)
    
    paragraphs = []
    current = []
    current_len = 0
    
    for sentence in sentences:
        space = 1 if current else 0
        if current_len + len(sentence) + space > max_chars:
            if current:
                paragraphs.append(" ".join(current).strip())
            current = [sentence]
            current_len = len(sentence)
        else:
            current.append(sentence)
            current_len += len(sentence) + space
    
    if current:
        paragraphs.append(" ".join(current).strip())
    
    return [p for p in paragraphs if p]


def assign_timestamps(paragraphs, total_duration_sec):
    """Assign timestamps to paragraphs"""
    num = len(paragraphs)
    duration_per = total_duration_sec / max(num, 1)
    
    seconds = []
    timestamps = []
    
    for i in range(num):
        sec = duration_per * i
        seconds.append(sec)
        
        td = datetime.timedelta(seconds=sec)
        total_sec = int(td.total_seconds())
        h = total_sec // 3600
        m = (total_sec % 3600) // 60
        s = total_sec % 60
        timestamps.append(f"{h:02d}:{m:02d}:{s:02d}")
    
    return pd.DataFrame({
        "seconds": seconds,
        "timestamp_str": timestamps
    })