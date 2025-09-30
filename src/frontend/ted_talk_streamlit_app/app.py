import streamlit as st
import pandas as pd
import re
from pathlib import Path

# --- 1. Load Fear Mongering Detection Model ---
@st.cache_resource
def load_model():
    try:
        from transformers import pipeline
        classifier = pipeline(
            "text-classification",
            model="Falconsai/fear_mongering_detection",
            truncation=True
        )
        return classifier
    except ImportError:
        st.warning("Transformers library not found.")
        return None

classifier = load_model()

# --- 2. Load datasets and merge ---
@st.cache_data
def load_data(transcripts_path=None, metadata_path=None):
    base_dir = Path(__file__).resolve().parent / "data"
    transcripts_path = base_dir / "ted_talks_transcripts.csv"
    metadata_path = base_dir / "ted_main.csv"

    transcripts_df = pd.read_csv(transcripts_path)
    metadata_df = pd.read_csv(metadata_path)

    merged_df = pd.merge(transcripts_df, metadata_df, on="url", how="left")
    return merged_df

df = load_data() # Call it once, cached by Streamlit

# --- 3. Basic Keyword-based Fear Analysis ---
def basic_fear_analysis(text):
    fear_keywords = [
        'crisis', 'disaster', 'catastrophe', 'collapse', 'destroy', 'dangerous',
        'threat', 'risk', 'warning', 'urgent', 'emergency', 'panic', 'fear',
        'terrible', 'horrible', 'devastating', 'shocking', 'alarming'
    ]
    text_lower = text.lower()
    fear_count = sum(1 for keyword in fear_keywords if keyword in text_lower)
    total_words = len(text.split())
    if total_words == 0:
        return 0.0
    fear_ratio = fear_count / total_words
    return min(fear_ratio * 10, 1.0)

# --- 4. Text Segmentation Utility ---
def segment_text_into_paragraphs(text, max_chars=250):
    sentences = re.split(r'(?<=[.!?])\s+', text)
    paragraphs = []
    current_paragraph = []
    current_length = 0
    for sentence in sentences:
        if current_length + len(sentence) + (1 if current_paragraph else 0) > max_chars:
            if current_paragraph:
                paragraphs.append(" ".join(current_paragraph).strip())
            current_paragraph = [sentence]
            current_length = len(sentence)
        else:
            current_paragraph.append(sentence)
            current_length += len(sentence) + (1 if current_paragraph else 0)
    if current_paragraph:
        paragraphs.append(" ".join(current_paragraph).strip())
    return [p for p in paragraphs if p]

# --- 5. Streamlit App ---
st.set_page_config(layout="wide")
st.title("Fear Mongering Detection — TED Talks")

if "transcript" not in df.columns:
    st.error("Transcript column missing in CSV.")
else:
    # --- Sidebar Controls ---
    with st.sidebar:
        st.header("Talk Selection")

        # Sorting
        sort_option = st.selectbox(
            "Sort talks by:",
            ["title", "views", "published_date", "duration"],
            format_func=lambda x: x.replace("_", " ").title()
        )
        ascending_order = st.checkbox("Ascending order", value=True)

        df_sorted = df.sort_values(by=sort_option, ascending=ascending_order).reset_index(drop=True)

        # Paging
        chunk_size = 50
        total_pages = (len(df_sorted) - 1) // chunk_size + 1
        page = st.number_input("Page number", min_value=1, max_value=total_pages, value=1)
        start = (page - 1) * chunk_size
        end = min(start + chunk_size, len(df_sorted))

        # Slider for talk selection
        talk_index_in_page = st.slider(
            "Select talk in current page",
            min_value=0,
            max_value=end - start - 1,
            value=0
        )

        selected_row = df_sorted.iloc[start + talk_index_in_page]

        # Metadata summary
        st.markdown(f"**Title:** {selected_row['title']}")
        st.markdown(f"**Speaker:** {selected_row['main_speaker']}")
        st.markdown(f"**URL:** [{selected_row['url']}]({selected_row['url']})")

        with st.expander("More details"):
            st.markdown(f"**Description:** {selected_row.get('description', 'N/A')}")
            st.markdown(f"**Published Date:** {selected_row.get('published_date', 'N/A')}")
            st.markdown(f"**Views:** {selected_row.get('views', 'N/A')}")
            st.markdown(f"**Duration:** {selected_row.get('duration', 'N/A')} seconds")

    # --- Main Content: Analysis ---
    st.subheader("Transcript Preview")
    transcript_text = selected_row["transcript"]
    st.write(transcript_text[:1000] + "..." if len(transcript_text) > 1000 else transcript_text)

    st.subheader("Fear Mongering Analysis")
    paragraphs_for_analysis = segment_text_into_paragraphs(transcript_text, max_chars=250)

    if paragraphs_for_analysis:
        method = st.radio(
            "Choose analysis method:",
            ["Transformer Model", "Keyword Fallback"],
            index=1 if not classifier else 0,
            horizontal=True,
            disabled=False if classifier else True
        )

        if method == "Transformer Model" and classifier:
            results = classifier(paragraphs_for_analysis)
            analysis_df = pd.DataFrame({
                "Paragraph": paragraphs_for_analysis,
                "Fear Mongering Score": [res['score'] for res in results],
                "Prediction": [
                    "Fear Mongering" if res['score'] > 0.6 else "Not Fear Mongering"
                    for res in results
                ]
            })
        else:
            if method == "Transformer Model" and not classifier:
                st.warning("Transformer model unavailable. Falling back to keyword-based analysis.")
            fear_scores = [basic_fear_analysis(p) for p in paragraphs_for_analysis]
            analysis_df = pd.DataFrame({
                "Paragraph": paragraphs_for_analysis,
                "Fear Mongering Score": fear_scores,
                "Prediction": [
                    "Fear Mongering" if score > 0.3 else "Not Fear Mongering"
                    for score in fear_scores
                ]
            })

        analysis_df['Fear Mongering Score'] = analysis_df['Fear Mongering Score'].apply(lambda x: f"{x:.2f}")
        st.dataframe(analysis_df, height=600, use_container_width=True)
    else:
        st.warning("No paragraphs found in the transcript.")
