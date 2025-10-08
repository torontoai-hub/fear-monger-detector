import streamlit as st
import time

def run_inference(classifier, paragraphs):
    """Run classifier on paragraphs with progress bar"""
    results = []
    progress = st.progress(0)

    for i, para in enumerate(paragraphs):
        prediction = classifier(para)
        results.append(prediction)
        progress.progress((i + 1) / len(paragraphs))
        time.sleep(0.05)

    progress.empty()
    return results
