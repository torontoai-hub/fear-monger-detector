from transformers import pipeline, AutoTokenizer
import streamlit as st
from backend.fear_monger_processor.config import MODEL_NAME

@st.cache_resource
def load_classifier():  # Cache the model as a persistent resource (loaded once per session)

    # Load the tokenizer for the specified Hugging Face model
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)

    # Create a text classification pipeline
    # Handles tokenization, model inference, and output formatting automatically
    return pipeline(
        "text-classification", # Task type
        model=MODEL_NAME, # Model name 
        tokenizer=tokenizer,
        truncation=True, # Ensure long text is truncated to fit model input size
        max_length=512, # Maximum token length per input
        top_k=1 # Return only the top prediction
    )

        # NOTE:
        # The `top_k=1` parameter ensures that the classifier returns only the single
        # most confident label for each text input instead of a list of all possible
        # labels with probabilities. This keeps inference results simple, like:
        #     [{'label': 'fear_mongering', 'score': 0.92}]
        # instead of:
        #     [
        #       {'label': 'fear_mongering', 'score': 0.92},
        #       {'label': 'neutral', 'score': 0.06},
        #       {'label': 'informative', 'score': 0.02}
        #     ]
        # This makes downstream analysis (e.g., correlating with heart rate or time)
        # easier since each paragraph yields exactly one numeric score.
