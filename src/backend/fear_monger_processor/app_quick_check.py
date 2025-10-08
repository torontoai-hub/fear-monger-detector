"""quick_check_app.py - Fear Mongering Quick Check Tool"""
import re
import time
import datetime
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
from transformers import pipeline, AutoTokenizer
from backend.fear_monger_processor.config import DEFAULT_FEAR_THRESHOLD, MODEL_NAME, MAX_CHARS
from youtube_transcript_api import YouTubeTranscriptApi
from urllib.parse import urlparse, parse_qs

# ======================================================
# MODEL LOADING
# ======================================================
@st.cache_resource
def load_classifier():
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    return pipeline(
        "text-classification",
        model=MODEL_NAME,
        tokenizer=tokenizer,
        truncation=True,
        max_length=512,  # bigger context window
        top_k=1
    )

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


# ======================================================
# CORE FUNCTIONS
# ======================================================
def segment_text(text, max_chars=MAX_CHARS, max_sentences=5):
    """Split text into paragraphs based on sentence boundaries and limits."""

    sentences = re.split(r'(?<=[.!?])\s+', text)
    paragraphs, current = [], []
    current_len, sentence_count = 0, 0

    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue

        space = 1 if current else 0
        if (current_len + len(sentence) + space > max_chars) or (sentence_count >= max_sentences):
            if current:
                paragraphs.append(" ".join(current).strip())
            current = [sentence]
            current_len = len(sentence)
            sentence_count = 1
        else:
            current.append(sentence)
            current_len += len(sentence) + space
            sentence_count += 1

    if current:
        paragraphs.append(" ".join(current).strip())

    return paragraphs


def assign_timestamps(paragraphs, total_duration_sec):
    """Assign evenly spaced timestamps based on fake total duration."""
    num = len(paragraphs)
    duration_per = total_duration_sec / max(num, 1)

    seconds, timestamps = [], []
    for i in range(num):
        sec = duration_per * i
        seconds.append(sec)
        td = datetime.timedelta(seconds=sec)
        timestamps.append(str(td))

    return pd.DataFrame({"seconds": seconds, "timestamp_str": timestamps})


def smooth_scores(scores, window=3):
    """
    Apply rolling average smoothing to fear mongering scores.
    Larger window smooths more aggressively.
    """
    return pd.Series(scores).rolling(window=window, min_periods=1, center=True).mean().tolist()


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


def create_analysis_df(paragraphs, timestamps, predictions, smoothing_window=3):
    """Create analysis dataframe with smoothing"""
    fear_scores = [extract_fear_score(pred) for pred in predictions]
    fear_scores_smoothed = smooth_scores(fear_scores, window=smoothing_window)
    return pd.DataFrame({
        "Timestamp": timestamps["timestamp_str"],
        "Paragraph": paragraphs,
        "Fear Mongering Score": fear_scores_smoothed,
        "Prediction": [
            "Fear Mongering" if score > DEFAULT_FEAR_THRESHOLD else "Not Fear Mongering"
            for score in fear_scores_smoothed
        ]
    })


def create_plotly_chart(seconds, scores, paragraphs, chart_type="Line Chart", max_hover_length=100):
    """Create interactive Plotly chart with hover tooltips based on selected type."""
    start_time = datetime.datetime(2025, 1, 1, 0, 0, 0)
    time_axis = [start_time + datetime.timedelta(seconds=s) for s in seconds]

    hover_texts = [
        f"Paragraph: {p[:max_hover_length]}{'...' if len(p) > max_hover_length else ''}<br>"
        f"Score: {score:.2f}"
        for p, score in zip(paragraphs, scores)
    ]

    fig = go.Figure()
    
    if chart_type == "Line Chart":
        fig.add_trace(go.Scatter(
            x=time_axis,
            y=scores,
            mode='lines+markers',
            line=dict(color='blue', width=2),
            marker=dict(size=8),  # Larger markers for easier hovering
            text=hover_texts,
            hovertemplate='%{text}<extra></extra>',
            hoverlabel=dict(namelength=0)
        ))
    elif chart_type == "Bar Chart":
        fig.add_trace(go.Bar(
            x=time_axis,
            y=scores,
            marker=dict(color='blue'),
            text=hover_texts,
            hovertemplate='%{text}<extra></extra>',
            hoverlabel=dict(namelength=0)
        ))
    elif chart_type == "Area Chart":
        fig.add_trace(go.Scatter(
            x=time_axis,
            y=scores,
            mode='lines',
            line=dict(color='blue', width=2),
            fill='tozeroy',
            fillcolor='rgba(0, 0, 255, 0.3)',
            text=hover_texts,
            hovertemplate='%{text}<extra></extra>',
            hoverlabel=dict(namelength=0)
        ))

    fig.update_xaxes(
        tickformat="%H:%M:%S",
        title_text="Elapsed Time (HH:MM:SS)"
    )
    
    fig.update_yaxes(
        title_text="Score",
        range=[0, 1]
    )

    fig.update_layout(
        title=f"Fear Mongering Score vs Time for Talk Index",
        xaxis=dict(
            rangeselector=dict(
                buttons=[
                    dict(count=1, label='1m', step='minute', stepmode='backward'),
                    dict(count=5, label='5m', step='minute', stepmode='backward'),
                    dict(count=15, label='15m', step='minute', stepmode='backward'),
                    dict(step='all')
                ]
            ),
            rangeslider=dict(visible=False),
            type='date'
        ),
        # hovermode='closest',  # Use 'closest' for pointer on data points
        hovermode='x unified',
        hoverlabel=dict(
            bgcolor="white",
            font_size=12,
            font_family="Arial",
            align='left',  # Global alignment
            bordercolor='blue'
        ),
        dragmode='pan'  # This changes the default cursor behavior
    )

    return fig

def display_results_table(analysis_df, threshold):
    """Display styled results table with optional highlighting"""
    def highlight_scores(row):
        score = row["Fear Mongering Score"]
        if score >= threshold:
            return ['background-color: #ffcccc'] * len(row)  # Light red
        elif score >= 0.5:
            return ['background-color: #ffffcc'] * len(row)  # Yellow
        else:
            return ['background-color: #ccffcc'] * len(row)  # Green

    styled_df = analysis_df.style.apply(highlight_scores, axis=1)
    st.dataframe(styled_df, use_container_width=True)


# -----------------------------------------------------------
# Utilities
# -----------------------------------------------------------

def get_video_id(url_or_id):
    """Extracts YouTube video ID from URL or returns it directly if valid."""
    if len(url_or_id) == 11:
        return url_or_id
    try:
        parsed = urlparse(url_or_id)
        if parsed.hostname in ["www.youtube.com", "youtube.com"]:
            return parse_qs(parsed.query)["v"][0]
        elif parsed.hostname == "youtu.be":
            return parsed.path[1:]
    except Exception:
        pass
    return None


def fetch_transcript(video_id):
    """Fetch transcript text from YouTube given a video ID."""
    try:
        ytt_api = YouTubeTranscriptApi()
        transcript_list = ytt_api.list(video_id)

        # Prefer manually created transcript, fallback to generated
        try:
            transcript = transcript_list.find_manually_created_transcript(["en-US", "en"])
        except Exception:
            transcript = transcript_list.find_generated_transcript(["en"])

        full_text = " ".join([snippet.text for snippet in transcript.fetch()])
        return full_text
    except Exception as e:
        st.error(f"Error fetching transcript: {e}")
        return None

# ======================================================
# STREAMLIT UI
# ======================================================

def main():
    # st.set_page_config("Quick Fear Mongering Check", layout="wide")
    st.title("Quick Fear Mongering Check")

    # ======================================================
    # Segmentation Settings
    # ======================================================
    st.sidebar.header("Segmentation Settings")

    segment_mode = st.sidebar.radio(
        "Segment text by:",
        ["Characters", "Sentences", "Both"],
        index=2,  # Default to "Both"
        help="Choose how to split the text into paragraphs for analysis."
    )

    max_chars = MAX_CHARS
    max_sentences = 5  # default value

    if segment_mode in ("Characters", "Both"):
        max_chars = st.sidebar.slider(
            "Maximum Characters per Segment",
            min_value=200,
            max_value=600,
            value=MAX_CHARS,
            step=5,
            help="Split the text once this many characters are reached."
        )

    if segment_mode in ("Sentences", "Both"):
        max_sentences = st.sidebar.slider(
            "Maximum Sentences per Segment",
            min_value=1,
            max_value=10,
            value=5,
            step=1,
            help="Split the text once this many sentences are reached."
        )


    # ======================================================
    # Threshold Settings
    # ======================================================
    threshold = st.sidebar.slider(
        "Fear Mongering Threshold",
        min_value=0.0,
        max_value=1.0,
        value=DEFAULT_FEAR_THRESHOLD,
        step=0.05,
        help="Paragraphs scoring above this value are labeled as fear mongering."
    )

    st.sidebar.caption("Adjust the threshold and paste any text below.")

    # ======================================================
    # Advanced Options
    # ======================================================
    with st.sidebar.expander("Advanced Options", expanded=False):
        smoothing_window = st.slider(
            "Smoothing Window Size",
            min_value=1,
            max_value=10,
            value=3,
            step=1,
            help="Larger window smooths the fear mongering score more."
        )

        chart_type = st.selectbox(
            "Chart Type",
            ["Line Chart", "Bar Chart", "Area Chart"],
            index=0,
            help="Choose how to display fear mongering trends."
        )

        max_hover_length = st.slider(
            "Max Hover Text Length",
            min_value=20,
            max_value=500,
            value=100,
            step=10,
            help="Limit number of characters shown in chart hover text."
        )

    # ======================================================
    # Load Model
    # ======================================================
    classifier = load_classifier()

    # ======================================================
    # Text Input
    # ======================================================
    quick_text = st.text_area(
        "Paste text here for quick analysis:",
        height=400,
        placeholder="Paste a paragraph, article, or speech segment..."
    )

    # ==== YouTube Integration ====
    transcript_text = None
    if quick_text.strip():
        
        if "youtube.com" in quick_text or "youtu.be" in quick_text or len(quick_text.strip()) == 11:
            video_id = get_video_id(quick_text.strip())

            if video_id:
                st.info(f"Fetching transcript for YouTube video ID: `{video_id}` ...")

                transcript_text = fetch_transcript(video_id)
                if transcript_text:
                    st.success("Transcript successfully fetched.")
                    with st.expander("Transcript Preview", expanded=False):
                        st.text_area("Fetched Transcript (readonly)", transcript_text[:4000], height=250)

                else:
                    st.error("Could not fetch transcript. Try another video.")
                    return
            else:
                st.error("Invalid YouTube URL or video ID.")
                return
        else:
            transcript_text = quick_text
    else:
        st.info("Paste text or YouTube link above to begin analysis.")
        return
    
    # ======================================================
    # Run Analysis
    # ======================================================
    if quick_text.strip():
        st.info("Running quick fear mongering analysis...")

        # paragraphs = segment_text(quick_text, max_chars=max_chars, max_sentences=max_sentences)

        text_to_analyze = transcript_text or quick_text

        paragraphs = segment_text(
            # quick_text,
            text_to_analyze,
            max_chars=max_chars if segment_mode in ("Characters", "Both") else float('inf'),
            max_sentences=max_sentences if segment_mode in ("Sentences", "Both") else float('inf')
        )


        if not paragraphs:
            st.warning("No paragraphs detected in your text.")
            return

        # fake_duration = max(len(quick_text) // 10, 10)  # seconds estimate
        fake_duration = max(len(transcript_text) // 10, 10) 
        timestamps = assign_timestamps(paragraphs, fake_duration)

        predictions = run_inference(classifier, paragraphs)
        # analysis_df = create_analysis_df(paragraphs, timestamps, predictions)
        analysis_df = create_analysis_df(
            paragraphs, timestamps, predictions, smoothing_window=smoothing_window
        )

        st.write(f"Text split into {len(paragraphs)} paragraphs (max {max_chars} chars each)")

        seconds = timestamps["seconds"]
        scores = analysis_df["Fear Mongering Score"]

        # ======================================================
        # Summary Metrics
        # ======================================================
        st.subheader("Quick Analysis Summary")
        col1, col2, col3 = st.columns(3)
        col1.metric("Paragraphs", len(paragraphs))
        col2.metric("Average Score", f"{scores.mean():.3f}")
        col3.metric("Peak Score", f"{scores.max():.3f}")

        # ======================================================
        # Chart
        # ======================================================
        st.subheader("Fear Mongering Trend")
        # fig = create_plotly_chart(seconds, scores, paragraphs)
        fig = create_plotly_chart(seconds, scores, paragraphs, chart_type=chart_type, max_hover_length=max_hover_length)

        st.plotly_chart(fig, use_container_width=True)

        # ======================================================
        # Table & CSV Download
        # ======================================================
        st.subheader("Paragraph-Level Analysis")
        display_results_table(analysis_df, threshold)
        # CSV download
        csv = analysis_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            "Download Results as CSV",
            data=csv,
            file_name="quick_fear_analysis.csv",
            mime="text/csv"
        )
    else:
        st.info("Paste text above to begin analysis.")

if __name__ == "__main__":
    main()
