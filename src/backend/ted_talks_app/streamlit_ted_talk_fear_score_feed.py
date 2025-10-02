import streamlit as st
import pandas as pd
import re
import time
from pathlib import Path

# --- 1. Load Fear Mongering Detection Model with caching ---
@st.cache_resource
def load_model():
    """
    Load and cache the Hugging Face transformer pipeline for text classification.
    This function will be executed once and cached to optimize app performance.
    Returns:
        classifier: A transformers pipeline object for fear mongering detection.
    """
    from transformers import pipeline
    # Load the pre-trained fear mongering detection model with truncation enabled
    return pipeline(
        "text-classification",
        model="Falconsai/fear_mongering_detection",
        truncation=True
    )

# Instantiate classifier once and cache
classifier = load_model()


# --- 2. Load transcripts CSV dataset with caching ---
@st.cache_data
@st.cache_data
def load_transcripts():
    """
    Load TED talks transcripts dataset from CSV files, cache the dataframe.
    Returns:
        DataFrame: The merged transcripts data.
    """
    try:
        # Go up two levels from backend/ to project root
        base_dir = Path(__file__).resolve().parent.parent.parent / "data" / "transcripts" / "ted_talks"

        transcripts_path = base_dir / "ted_talks_transcripts.csv"
        metadata_path = base_dir / "ted_main.csv"

        # st.write(f"Transcripts path: {transcripts_path.resolve()}")
        # st.write(f"Metadata path: {metadata_path.resolve()}")

        if not transcripts_path.exists():
            raise FileNotFoundError(f"Transcripts file not found: {transcripts_path}")
        if not metadata_path.exists():
            raise FileNotFoundError(f"Metadata file not found: {metadata_path}")

        transcripts_df = pd.read_csv(transcripts_path)
        metadata_df = pd.read_csv(metadata_path)

        merged_df = pd.merge(transcripts_df, metadata_df, on="url", how="left")
        return merged_df

    except FileNotFoundError as e:
        st.error(f"ile not found: {e}")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Unexpected error: {e}")
        return pd.DataFrame()


# Load transcripts once during app lifetime
df = load_transcripts()


# --- 3. Text Segmentation Utility ---
def segment_text_into_paragraphs(text, max_chars=250):
    """
    Split input text into paragraphs not exceeding max_chars.
    Paragraph segmentation respects sentence boundaries using regex.
    Args:
        text (str): Full transcript text.
        max_chars (int): Maximum characters allowed per paragraph chunk.
    Returns:
        list: List of paragraphs (strings) for analysis.
    """
    # Split text into sentences based on punctuation with lookbehind
    sentences = re.split(r'(?<=[.!?])\s+', text)
    paragraphs = []
    current_paragraph = []
    current_length = 0

    # Accumulate sentences without exceeding max_chars per paragraph
    for sentence in sentences:
        # Extra 1 char for spacing if needed
        if current_length + len(sentence) + (1 if current_paragraph else 0) > max_chars:
            if current_paragraph:
                # Join and append completed paragraph
                paragraphs.append(" ".join(current_paragraph).strip())
            current_paragraph = [sentence]
            current_length = len(sentence)
        else:
            current_paragraph.append(sentence)
            current_length += len(sentence) + (1 if current_paragraph else 0)

    # Append remaining sentences as last paragraph
    if current_paragraph:
        paragraphs.append(" ".join(current_paragraph).strip())

    # Filter out empty paragraphs for safety
    return [p for p in paragraphs if p]


# --- 4. Inference function with caching and progress reporting ---
@st.cache_data
def run_inference(paragraphs):
    """
    Run classifier on list of paragraphs.
    Results cached for repeated inputs to reduce latency.
    Includes simple progress bar for UX during batch inference.
    Args:
        paragraphs (list): List of paragraph strings.
    Returns:
        list: List of prediction dicts with 'label' and 'score'.
    """
    results = []
    progress_bar = st.progress(0)

    # Iterate paragraphs for individual inference
    for i, paragraph in enumerate(paragraphs):
        res = classifier(paragraph)[0]  # Run inference on paragraph
        results.append(res)
        progress_bar.progress((i + 1) / len(paragraphs))
        time.sleep(0.05)  # Optional delay for smoother UI progress update

    progress_bar.empty()  # Clear progress bar from UI
    return results


# --- 5. Streamlit Application UI ---
st.title("Fear Mongering Detection with Paragraph Segmentation")

# Sidebar for selecting talk index from the dataset
talk_index = st.sidebar.number_input(
    "Select talk index",
    min_value=0,
    max_value=len(df) - 1,
    value=0,
    help="Select index of TED talk transcript to analyze."
)

# Get selected transcript text
selected_transcript = df.iloc[talk_index]["transcript"]

# Display transcript snippet for quick overview
st.subheader("Transcript Preview")
st.write(selected_transcript[:1000] + "...")  # Limit output length

# Segment transcript into paragraphs for analysis
paragraphs = segment_text_into_paragraphs(selected_transcript, max_chars=250)

st.subheader("Fear Mongering Analysis")

# Run fear mongering inference if paragraphs available and model loaded
if paragraphs and classifier is not None:
    results = run_inference(paragraphs)
    # Build dataframe of text, scores, and predictions for display
    analysis_df = pd.DataFrame({
        "Paragraph": paragraphs,
        "Fear Mongering Score": [r["score"] for r in results],
        "Prediction": ["Fear Mongering" if r["score"] > 0.6 else "Not Fear Mongering" for r in results]
    })
    # Format score column nicely
    analysis_df["Fear Mongering Score"] = analysis_df["Fear Mongering Score"].apply(lambda x: f"{x:.2f}")
    # Show results in an interactive table
    st.dataframe(analysis_df)

# Warn user if model not loaded
elif classifier is None:
    st.warning("Transformer model unavailable. Please ensure the 'transformers' library is installed.")

# Warn if no paragraphs could be generated for analysis
else:
    st.warning("No paragraphs found in transcript.")
