"""analysis.py - Run inference and create results"""
import time
import streamlit as st
import pandas as pd
from .config import DEFAULT_FEAR_THRESHOLD
from .utils import smooth_scores

@st.cache_data
def run_inference(_classifier, paragraphs):
    """Run classifier on paragraphs with progress bar"""
    results = []
    progress = st.progress(0)

    for i, para in enumerate(paragraphs):
        prediction = _classifier(para)
        results.append(prediction)  # Keep nesting intact for flattening
        progress.progress((i + 1) / len(paragraphs))
        time.sleep(0.05)

    progress.empty()
    return results


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


def create_analysis_df(paragraphs, timestamps, predictions):
    """Create analysis dataframe with smoothing"""
    fear_scores = [extract_fear_score(pred) for pred in predictions]
    fear_scores_smoothed = smooth_scores(fear_scores, window=3)  # window size controls smoothing

    return pd.DataFrame({
        "Timestamp": timestamps["timestamp_str"],
        "Paragraph": paragraphs,
        "Fear Mongering Score": fear_scores_smoothed,
        "Prediction": [
            "Fear Mongering" if score > DEFAULT_FEAR_THRESHOLD else "Not Fear Mongering"
            for score in fear_scores_smoothed
        ]
    })
