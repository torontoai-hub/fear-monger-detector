"""models.py - Model loading"""
import streamlit as st
from transformers import pipeline, AutoTokenizer
from backend.ted_talks_app.config import MODEL_NAME


@st.cache_resource
def load_classifier():
    from transformers import pipeline, AutoTokenizer
    from config import MODEL_NAME

    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    return pipeline(
        "text-classification",
        model=MODEL_NAME,
        tokenizer=tokenizer,
        truncation=True,
        max_length=512,  # bigger context window
        top_k=1
    )

# if __name__ == "__main__":
#     _classifier = load_classifier()

#     example_texts = [
#     "This is a scary statement.",
#     "This is a normal statement.",
#     "A long paragraph from your dataset..."
#     ]



#     for text in example_texts + ["A long paragraph from your dataset..."]:
#         print(text)
#         print(_classifier(text))
#         print("-" * 50)

#     for text in example_texts:
#         print(_classifier(text))
