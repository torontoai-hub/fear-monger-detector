"""analysis.py - Run inference and create results"""
import time
import streamlit as st
import pandas as pd
from config import DEFAULT_FEAR_THRESHOLD


@st.cache_data
def run_inference(_classifier, paragraphs):
    """Run classifier on paragraphs with progress bar"""
    results = []
    progress = st.progress(0)
    
    for i, para in enumerate(paragraphs):
        results.append(_classifier(para)[0])
        progress.progress((i + 1) / len(paragraphs))
        time.sleep(0.05)
    
    progress.empty()
    return results


def create_analysis_df(paragraphs, timestamps, predictions):
    """Create analysis dataframe"""
    return pd.DataFrame({
        "Timestamp": timestamps["timestamp_str"],
        "Paragraph": paragraphs,
        "Fear Mongering Score": [round(r["score"], 2) for r in predictions],
        "Prediction": [
            "Fear Mongering" if r["score"] > DEFAULT_FEAR_THRESHOLD else "Not Fear Mongering"
            for r in predictions
        ]
    })