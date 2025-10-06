"""models.py - Model loading"""
import streamlit as st
from transformers import pipeline
from config import MODEL_NAME


@st.cache_resource
def load_classifier():
    """Load and cache the fear mongering classifier"""
    return pipeline(
        "text-classification",
        model=MODEL_NAME,
        truncation=True
    )