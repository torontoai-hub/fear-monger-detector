from transformers import pipeline, AutoTokenizer
import streamlit as st
from backend.fear_monger_processor.config import MODEL_NAME

@st.cache_resource
def load_classifier():
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    return pipeline(
        "text-classification",
        model=MODEL_NAME,
        tokenizer=tokenizer,
        truncation=True,
        max_length=512,
        top_k=1
    )
