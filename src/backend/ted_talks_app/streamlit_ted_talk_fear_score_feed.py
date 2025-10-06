import datetime
import re
import time
from pathlib import Path
import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import plotly.express as px
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode


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
        if not transcripts_path.exists():
            raise FileNotFoundError(f"Transcripts file not found: {transcripts_path}")
        if not metadata_path.exists():
            raise FileNotFoundError(f"Metadata file not found: {metadata_path}")

        transcripts_df = pd.read_csv(transcripts_path)
        metadata_df = pd.read_csv(metadata_path)

        merged_df = pd.merge(transcripts_df, metadata_df, on="url", how="left")
        return merged_df

    except FileNotFoundError as e:
        st.error(f"file not found: {e}")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Unexpected error: {e}")
        return pd.DataFrame()

# Load transcripts once during app lifetime
df = load_transcripts()


# --- 3. Utilities ---
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
    paragraphs, current_paragraph, current_length = [], [], 0

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


def timedelta_to_hms(td):
    total_seconds = int(td.total_seconds())
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


def assign_timestamps(paragraphs, total_duration_sec, start_time=None):
    """
    Assign timestamps to paragraph segments.
    Returns both seconds and formatted HH:MM:SS strings.

    Args:
        paragraphs (list): List of paragraph strings.
        total_duration_sec (int): Total duration in seconds.
        start_time (datetime, optional): Start time if desired.

    Returns:
        DataFrame: Columns for seconds and formatted timestamps.
    """
    num_paragraphs = len(paragraphs)
    duration_per_paragraph = total_duration_sec / max(num_paragraphs, 1)

    seconds_list, formatted_timestamps = [], []

    for i in range(num_paragraphs):
        elapsed_seconds = duration_per_paragraph * i
        seconds_list.append(elapsed_seconds)

        td = datetime.timedelta(seconds=elapsed_seconds)
        formatted_timestamps.append(timedelta_to_hms(td))

    return pd.DataFrame({
        "seconds": seconds_list,
        "timestamp_str": formatted_timestamps
    })



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

# ----------------------------------------------------------------------------------------
# Segment transcript into paragraphs for analysis
# ----------------------------------------------------------------------------------------
paragraphs = segment_text_into_paragraphs(selected_transcript, max_chars=250)

# Get duration in seconds for the selected talk
selected_duration_sec = df.iloc[talk_index]["duration"]

# Assign timestamps to paragraph segments using duration (returns seconds and HH:MM:SS)
timestamped_df = assign_timestamps(paragraphs, selected_duration_sec)


# ----------------------------------------------------------------------------------------
# Sub heading
# ----------------------------------------------------------------------------------------
# --- Fear Mongering Analysis ---
st.subheader("Fear Mongering Analysis")

if paragraphs and classifier is not None:
    results = run_inference(paragraphs)

    # Assign timestamps
    timestamped_df = assign_timestamps(paragraphs, selected_duration_sec)

    # Build dataframe
    analysis_df = pd.DataFrame({
        "Timestamp": timestamped_df["timestamp_str"],
        "Paragraph": paragraphs,
        "Fear Mongering Score": [r["score"] for r in results],
        "Prediction": ["Fear Mongering" if r["score"] > 0.6 else "Not Fear Mongering" for r in results]
    })

    analysis_df["Fear Mongering Score"] = analysis_df["Fear Mongering Score"].astype(float).round(2)
    seconds = timestamped_df["seconds"]

    # --- Matplotlib Plot ---
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot(seconds, analysis_df['Fear Mongering Score'], label='Fear Mongering Score', color='blue')

    ax.set_xlabel('Elapsed Time (HH:MM:SS)')
    ax.set_ylabel('Fear Mongering Score')
    ax.set_title(f'Fear Mongering Score vs Time for Talk Index {talk_index}')
    ax.legend()
    ax.grid(True)

    plt.xticks(rotation=45)
    plt.tight_layout()

    # Save Matplotlib chart
    output_img = f"fear_mongering_score_plot_{talk_index}.png"
    fig.savefig(output_img, dpi=300)

    st.pyplot(fig)

    with open(output_img, "rb") as f:
        st.download_button(
            label="Download Matplotlib Chart (PNG)",
            data=f,
            file_name=output_img,
            mime="image/png"
        )
    st.success(f"Matplotlib chart saved as {output_img}")

    # --- Plotly Interactive Chart ---
    import datetime
    start_time = datetime.datetime(2025, 1, 1, 0, 0, 0)
    time_axis = [start_time + datetime.timedelta(seconds=s) for s in seconds]

    fig = px.line(
        analysis_df,
        x=time_axis,
        y='Fear Mongering Score',
        title=f"Fear Mongering Score vs Time for Talk Index {talk_index}",
        labels={'x': 'Elapsed Time', 'Fear Mongering Score': 'Score'},
    )

    fig.update_traces(line=dict(color='blue'))

    fig.update_xaxes(
        tickformat="%H:%M:%S",
        title_text="Elapsed Time (HH:MM:SS)"
    )

    fig.update_layout(
        xaxis=dict(
            rangeselector=dict(
                buttons=list([
                    dict(count=1, label='1m', step='minute', stepmode='backward'),
                    dict(count=5, label='5m', step='minute', stepmode='backward'),
                    dict(count=15, label='15m', step='minute', stepmode='backward'),
                    dict(step='all')
                ])
            ),
            rangeslider=dict(visible=True),
            type='date'
        ),
        hovermode='x unified',
    )

    st.plotly_chart(fig, use_container_width=True)

    # --- Kaleido Safe Export + Download ---
    import plotly.io as pio
    try:
        plotly_img = f"fear_mongering_score_plot_{talk_index}_plotly.png"
        fig.write_image(plotly_img, scale=2)

        with open(plotly_img, "rb") as f:
            st.download_button(
                label="Download Plotly Chart (PNG)",
                data=f,
                file_name=plotly_img,
                mime="image/png"
            )
        st.success(f"Plotly chart saved as {plotly_img}")

    except Exception as e:
        st.warning(f"Could not export Plotly chart as image: {e}")
        st.info("Install Kaleido + Chrome in WSL to enable this feature.")

    # --- Results Table ---
    st.dataframe(analysis_df[["Timestamp", "Paragraph", "Fear Mongering Score", "Prediction"]])

    # CSV download button
    csv_data = analysis_df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="Download Analysis as CSV",
        data=csv_data,
        file_name=f"fear_mongering_analysis_{talk_index}.csv",
        mime="text/csv"
    )

elif classifier is None:
    st.warning("Transformer model unavailable. Please ensure the 'transformers' library is installed.")

else:
    st.warning("No paragraphs found in transcript.")

