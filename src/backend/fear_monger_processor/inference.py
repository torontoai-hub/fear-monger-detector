import streamlit as st
import time

def run_inference(classifier, paragraphs): # Cache the data results (reuse predictions for same inputs)
    """Run classifier on paragraphs with progress bar"""

    results = [] # List to store all predictions
    progress = st.progress(0) # Initialize progress bar in Streamlit

    # Loop through each paragraph in the text lis
    for i, para in enumerate(paragraphs): 
        prediction = classifier(para)  # Run the model on one paragraph
        results.append(prediction) # Store model's output (list of label/score dicts)

        # Update progress bar to show % completed
        progress.progress((i + 1) / len(paragraphs))

        time.sleep(0.05) # Small delay so the bar visibly updates smoothly

    progress.empty() # Clear progress bar after completion
    return results # Return all paragraph predictions
