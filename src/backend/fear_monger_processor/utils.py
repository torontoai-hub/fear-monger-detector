"""quick_check_app.py - Fear Mongering Quick Check Tool"""
import re
import time
import datetime
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
from transformers import pipeline, AutoTokenizer
from backend.fear_monger_processor.config import DEFAULT_FEAR_THRESHOLD, MODEL_NAME, MAX_CHARS, FIXED_DURATION
from youtube_transcript_api import YouTubeTranscriptApi
from urllib.parse import urlparse, parse_qs
from nltk.tokenize import sent_tokenize


# ======================================================
# CORE FUNCTIONS
# ======================================================
def segment_text(text, max_chars=MAX_CHARS, max_sentences=5):
    """Split text into paragraphs based on sentence boundaries and limits."""

    # sentences = re.split(r'(?<=[.!?])\s+', text)
    sentences = sent_tokenize(text)
    paragraphs, current = [], []
    current_len, sentence_count = 0, 0

    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue

        space = 1 if current else 0
        if (current_len + len(sentence) + space > max_chars) or (sentence_count >= max_sentences):
            if current:
                paragraphs.append(" ".join(current).strip())
            current = [sentence]
            current_len = len(sentence)
            sentence_count = 1
        else:
            current.append(sentence)
            current_len += len(sentence) + space
            sentence_count += 1

    if current:
        paragraphs.append(" ".join(current).strip())

    return paragraphs


# def assign_timestamps(paragraphs, total_duration_sec):
#     """Assign evenly spaced timestamps based on fake total duration."""
#     num = len(paragraphs)
#     duration_per = total_duration_sec / max(num, 1)

#     seconds, timestamps = [], []
#     for i in range(num):
#         sec = duration_per * i
#         seconds.append(sec)
#         # td = datetime.timedelta(seconds=sec)
#         td = datetime.timedelta(seconds=int(sec))
#         timestamps.append(str(td))

#     return pd.DataFrame({"seconds": seconds, "timestamp_str": timestamps})

def assign_timestamps(paragraphs):
    """Assign evenly spaced timestamps for a fixed 10-minute test duration."""
    num = len(paragraphs)
    if num == 0:
        return pd.DataFrame(columns=["seconds", "timestamp_str"])

    duration_per = FIXED_DURATION / num

    seconds, timestamps = [], []
    for i in range(num):
        sec = duration_per * i
        seconds.append(sec)
        td = datetime.timedelta(seconds=int(sec))
        timestamps.append(str(td))

    return pd.DataFrame({"seconds": seconds, "timestamp_str": timestamps})


def smooth_scores(scores, window=3):
    """
    Apply rolling average smoothing to fear mongering scores.
    Larger window smooths more aggressively.
    """
    return pd.Series(scores).rolling(window=window, min_periods=1, center=True).mean().tolist()


def extract_fear_score(prediction):
    """Extract Fear_Mongering score from nested prediction list."""
    # Flatten if nested
    if isinstance(prediction, list) and len(prediction) == 1 and isinstance(prediction[0], list):
        prediction = prediction[0]

    if isinstance(prediction, list):
        for label_score in prediction:
            if label_score.get("label") == "Fear_Mongering":
                return round(label_score.get("score", 0.0), 4)
    elif isinstance(prediction, dict):
        if prediction.get("label") == "Fear_Mongering":
            return round(prediction.get("score", 0.0), 4)
    return 0.0


import pandas as pd
import streamlit as st

DEFAULT_FEAR_THRESHOLD = 0.5  # keep same as before

def create_analysis_df(paragraphs, timestamps, predictions, smoothing_window=3, video_duration_seconds=None):
    """Create analysis dataframe with smoothing and optional Streamlit state storage."""
    fear_scores = [extract_fear_score(pred) for pred in predictions]
    fear_scores_smoothed = smooth_scores(fear_scores, window=smoothing_window)

    df = pd.DataFrame({
        "Timestamp": timestamps["timestamp_str"],
        "Paragraph": paragraphs,
        "Fear Mongering Score": fear_scores_smoothed,
        "Prediction": [
            "Fear Mongering" if score > DEFAULT_FEAR_THRESHOLD else "Not Fear Mongering"
            for score in fear_scores_smoothed
        ]
    })

    # Store for downstream Fitbit correlation (if Streamlit session is active)
    try:
        st.session_state["fear_results_df"] = df
        if video_duration_seconds:
            st.session_state["video_duration_seconds"] = video_duration_seconds
    except Exception:
        # no Streamlit context (e.g., running in backend mode)
        pass

    return df



def create_plotly_chart(seconds, scores, paragraphs, chart_type="Line Chart", max_hover_length=100):
    """Create interactive Plotly chart with hover tooltips based on selected type."""
    start_time = datetime.datetime(2025, 1, 1, 0, 0, 0)
    time_axis = [start_time + datetime.timedelta(seconds=s) for s in seconds]

    hover_texts = [
        f"Paragraph: {p[:max_hover_length]}{'...' if len(p) > max_hover_length else ''}<br>"
        f"Score: {score:.2f}"
        for p, score in zip(paragraphs, scores)
    ]

    fig = go.Figure()
    
    if chart_type == "Line Chart":
        fig.add_trace(go.Scatter(
            x=time_axis,
            y=scores,
            mode='lines+markers',
            line=dict(color='blue', width=2),
            marker=dict(size=8),  # Larger markers for easier hovering
            text=hover_texts,
            hovertemplate='%{text}<extra></extra>',
            hoverlabel=dict(namelength=0)
        ))
    elif chart_type == "Bar Chart":
        fig.add_trace(go.Bar(
            x=time_axis,
            y=scores,
            marker=dict(color='blue'),
            text=hover_texts,
            hovertemplate='%{text}<extra></extra>',
            hoverlabel=dict(namelength=0)
        ))
    elif chart_type == "Area Chart":
        fig.add_trace(go.Scatter(
            x=time_axis,
            y=scores,
            mode='lines',
            line=dict(color='blue', width=2),
            fill='tozeroy',
            fillcolor='rgba(0, 0, 255, 0.3)',
            text=hover_texts,
            hovertemplate='%{text}<extra></extra>',
            hoverlabel=dict(namelength=0)
        ))

    fig.update_xaxes(
        tickformat="%H:%M:%S",
        title_text="Elapsed Time (HH:MM:SS)"
    )
    
    fig.update_yaxes(
        title_text="Score",
        range=[0, 1]
    )

    fig.update_layout(
        title=f"Fear Mongering Score vs Time for Talk Index",
        xaxis=dict(
            rangeselector=dict(
                buttons=[
                    dict(count=1, label='1m', step='minute', stepmode='backward'),
                    dict(count=5, label='5m', step='minute', stepmode='backward'),
                    dict(count=15, label='15m', step='minute', stepmode='backward'),
                    dict(step='all')
                ]
            ),
            rangeslider=dict(visible=False),
            type='date'
        ),
        # hovermode='closest',  # Use 'closest' for pointer on data points
        hovermode='x unified',
        hoverlabel=dict(
            bgcolor="white",
            font_size=12,
            font_family="Arial",
            align='left',  # Global alignment
            bordercolor='blue'
        ),
        dragmode='pan'  # This changes the default cursor behavior
    )

    return fig


def display_results_table(analysis_df, threshold):
    """Display styled results table with optional highlighting"""
    def highlight_scores(row):
        score = row["Fear Mongering Score"]
        if score >= threshold:
            return ['background-color: #ffcccc'] * len(row)  # Light red
        elif score >= 0.5:
            return ['background-color: #ffffcc'] * len(row)  # Yellow
        else:
            return ['background-color: #ccffcc'] * len(row)  # Green

    styled_df = analysis_df.style.apply(highlight_scores, axis=1)
    st.dataframe(styled_df, use_container_width=True)
