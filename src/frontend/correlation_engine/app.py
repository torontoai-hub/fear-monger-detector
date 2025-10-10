from datetime import datetime, timedelta
import pandas as pd
from pathlib import Path
import matplotlib.pyplot as plt
import streamlit as st
import pytz
import nltk
import plotly.express as px

# === MODEL LOADING ===
from backend.fear_monger_processor.model import load_classifier
from backend.fear_monger_processor.inference import run_inference
from backend.fear_monger_processor.transcript import get_video_id, fetch_transcript
from backend.fear_monger_processor.utils import segment_text, assign_timestamps, create_analysis_df, create_plotly_chart, display_results_table

# === CONFIG & UTILITIES ===
from frontend.correlation_engine.config import MAX_CHARS, DEFAULT_FEAR_THRESHOLD, DEFAULT_SMOOTHING_WINDOW, DEFAULT_CHART_TYPE
from backend.fitbit_app.fitbit_utils import get_fitbit_heart_data, plot_fitbit_heart
from backend.fitbit_app.fitbit_client import fetch_fitbit_data
from backend.fitbit_app.aligner import align_fear_and_heart
from backend.fitbit_app.playback_window import estimate_playback_window
from backend.fitbit_app.config import TOKEN_FILE
from backend.ted_talks_app.data_loader import load_transcripts

base_dir = Path(__file__).resolve().parents[2]

def load_css(file_path):
    with open(file_path) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
        

def main():

    # === Load Styles ===
    load_css("styles.css")

    # === Ensure NLP dependencies ===
    try:
        nltk.data.find("tokenizers/punkt")
    except LookupError:
        nltk.download("punkt")  # Needed for sentence segmentation

    # === Load Classifier Model ===
    if "classifier" not in st.session_state:

        # Only load once — stored in session_state for efficiency
        with st.spinner("Loading fear detection model..."):
            st.session_state.classifier = load_classifier()

    classifier = st.session_state.classifier

  
    # ======================================================
    # UI SETUP
    # ======================================================
    st.title("Fear Sensor")

    # ======================================================
    # Segmentation Settings
    # ======================================================
    with st.sidebar.expander("Select Fear Threshold ", expanded=False):
        segment_mode = st.radio(
            "Segment text by:",
            ["Characters", "Sentences", "Both"],
            index=2,  # Default to "Both"
            help="Choose how to split the text into paragraphs for analysis."
        )

        max_chars = MAX_CHARS
        max_sentences = 5

        if segment_mode in ("Characters", "Both"):
            max_chars = st.slider(
                "Maximum Characters per Segment",
                min_value=200,
                max_value=600,
                value=MAX_CHARS,
                step=5,
                help="Split the text once this many characters are reached."
            )

        if segment_mode in ("Sentences", "Both"):
            max_sentences = st.slider(
                "Maximum Sentences per Segment",
                min_value=1,
                max_value=10,
                value=5,
                step=1,
                help="Split the text once this many sentences are reached."
            )

        # ======================================================
        # Fear Threshold Settings
        # ======================================================
        threshold = st.slider(
            "Fear Mongering Threshold",
            min_value=0.0,
            max_value=1.0,
            value=DEFAULT_FEAR_THRESHOLD,
            step=0.05,
            help="Adjust the threshold for analysis."
        )

        smoothing_window = st.slider(
            "Smoothing Window Size",
            min_value=1,
            max_value=10,
            value=DEFAULT_SMOOTHING_WINDOW,
            step=1,
            help="Larger window smooths the fear mongering score more."
        )


    # ======================================================
    # Chart Options
    # ======================================================
    with st.sidebar.expander("Chart Options", expanded=False):
        chart_type = st.selectbox(
            "Chart Type",
            ["Line Chart", "Bar Chart", "Area Chart"],
            index=["Line Chart", "Bar Chart", "Area Chart"].index(DEFAULT_CHART_TYPE),
            help="Choose how to display fear mongering trends."
        )

        max_hover_length = st.slider(
            "Max Hover Text Length",
            min_value=20,
            max_value=500,
            value=30,
            step=10,
            help="Limit number of characters shown in chart hover text."
        )

    # ======================================================
    # TED Talks Loading
    # ======================================================
    with st.sidebar.expander("TED Talks", expanded=False):
        df = load_transcripts()

        if df.empty:
            st.error("Failed to load transcript data. Please check your data files.")
            return
        
        st.header("Talk Selection")

        # Sorting and Paging
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
        page = st.number_input(
            "Page number (1 = first 50 talks)",
            min_value=1,
            max_value=total_pages,
            value=1
        )
        start = (page - 1) * chunk_size
        end = min(start + chunk_size, len(df_sorted))

        talk_index = st.slider(
            f"Select talk (in page {page})",
            min_value=0,
            max_value=end - start - 1,
            value=0
        )
        
        selected_row = df_sorted.iloc[start + talk_index]

        # Display talk metadata
        st.markdown(f"**Title:** {selected_row['title']}")
        st.markdown(f"**Speaker:** {selected_row['main_speaker']}")
        st.markdown(f"**URL:** [{selected_row['url']}]({selected_row['url']})")
        st.markdown(f"**Description:** {selected_row.get('description', 'N/A')}")
        st.markdown(f"**Published Date:** {selected_row.get('published_date', 'N/A')}")
        st.markdown(f"**Views:** {selected_row.get('views', 'N/A')}")
        st.markdown(f"**Duration:** {selected_row.get('duration', 'N/A')} seconds")

        # Adjust talk_index to global dataset index
        talk_index = start + talk_index

        st.markdown("---")
        
        st.header("Analysis Settings")
        
        threshold = st.slider(
            "Fear Mongering Threshold",
            min_value=0.0,
            max_value=1.0,
            value=DEFAULT_FEAR_THRESHOLD,
            step=0.05,
            help="Scores above this threshold are considered fear mongering"
        )
        
        show_all_paragraphs = st.checkbox(
            "Show all paragraphs",
            value=True,
            help="Uncheck to show only high-scoring paragraphs"
        )
        
    

    # ===============================
    # YouTube URL Input
    # ===============================
    url_input = st.text_input(
        "Enter YouTube URL:",
        help="Paste a YouTube video URL to fetch its transcript."
    )

    # Create the expander immediately after URL input
    with st.expander("Transcript Preview"):
        expander_content = st.empty()

    transcript_text = None
    video_id = None

    if url_input.strip():
        video_id = get_video_id(url_input.strip())

        if video_id:
            transcript_text = fetch_transcript(video_id)  # progress bar handled inside function

            if transcript_text:
                expander_content.write(transcript_text[:4000])  # first 4000 chars preview
            else:
                expander_content.write("No transcript available for this video.")

        else:
            st.error("Invalid YouTube URL.")

    # ===============================
    # Manual Transcript Input
    # ===============================
    quick_text = st.text_area(
        "Or paste transcript text here:",
        height=100,
        help="Paste transcript text directly if you don’t want to use a URL."
    )

    if not transcript_text and quick_text.strip():
        transcript_text = quick_text
        expander_content.write(transcript_text[:4000])  # preview manual transcript

    # ===============================
    # YouTube Embed
    # ===============================
    if video_id:
        embed_code = f"""
        <div class="video-container">
            <div class="video-wrapper">
                <iframe
                    src="https://www.youtube.com/embed/{video_id}"
                    frameborder="0"
                    allowfullscreen>
                </iframe>
            </div>
        </div>
        """
        st.markdown(embed_code, unsafe_allow_html=True)

    if not transcript_text:
        st.info("Paste a YouTube URL above or enter transcript text to begin analysis.")


    # ========================
    # Text segmentation
    # ========================
    text_to_analyze = transcript_text or quick_text
    paragraphs = segment_text(
        text_to_analyze,
        max_chars=max_chars if segment_mode in ("Characters", "Both") else float('inf'),
        max_sentences=max_sentences if segment_mode in ("Sentences", "Both") else float('inf')
    )

    if not paragraphs:
        st.warning("No paragraphs detected.")
        return

    fake_duration = max(len(text_to_analyze) // 10, 10)
    timestamps = assign_timestamps(paragraphs)


    # ========================
    # RUN INFERENCE
    # ========================
    # This is the core model execution step.
    # It only runs when there is new transcript data.
    predictions = run_inference(classifier, paragraphs)

    st.markdown("---")


    # ======================================================
    # Segment Transcript
    # ======================================================
    st.subheader("View Transcript Segments")

    st.write(f"Text split into {len(paragraphs)} segments (max {max_chars} chars each)")

    with st.expander("View All Segments"):
        df_paragraphs = pd.DataFrame({
            "Segment #": list(range(1, len(paragraphs) + 1)),
            "Text": paragraphs
        })
        st.dataframe(df_paragraphs, use_container_width=True)

    st.markdown("---")


    # ======================================================
    # Create analysis DataFrame
    # ======================================================
    analysis_df = create_analysis_df(
        paragraphs=paragraphs,
        timestamps=timestamps,
        predictions=predictions,
        smoothing_window=smoothing_window,
        video_duration_seconds=fake_duration,
    )

    # Save results for downstream correlation
    st.session_state["fear_results_df"] = analysis_df
    st.session_state["video_duration_seconds"] = fake_duration


    # ======================================================
    # Get Timestamps and Fear Scores
    # ======================================================
    seconds = timestamps["seconds"]
    scores = analysis_df["Fear Mongering Score"]

    # ========================
    # Summary & Visualization
    # ========================
    st.subheader("Quick Analysis Summary")

    col1, col2 = st.columns([2, 1], gap="small")  # Main column + pie chart column

    with col1:
        avg_score = scores.mean()
        max_score = scores.max()
        min_score = scores.min()
        high_risk_count = len(analysis_df[analysis_df["Fear Mongering Score"] >= threshold])
        percentage = (high_risk_count / len(paragraphs)) * 100

        # Quick stats
        stats_col1, stats_col2, stats_col3, stats_col4 = st.columns(4)

        with stats_col1:
            st.metric("Paragraphs", len(paragraphs))

        with stats_col2:
            st.metric(
                "Average Score",
                f"{avg_score:.3f}",
                delta=f"{((avg_score - threshold) * 100):.0f}% vs threshold",
                delta_color="inverse"
            )

        with stats_col3:
            st.metric(
                "Peak Score",
                f"{max_score:.3f}",
                delta=f"Low: {min_score:.3f}"
            )

        with stats_col4:
            st.metric(
                "High Risk",
                f"{high_risk_count}",
                delta=f"{percentage:.1f}% of talk"
            )

        st.markdown("---")

        # Overall Assessment
        st.subheader("Overall Assessment")

        if avg_score >= threshold:
            st.markdown(f'<div class="theme-status-box error">'
                        f"### High Fear Mongering Detected<br>"
                        f"- Average score: **{avg_score:.3f}** (threshold: {threshold:.2f})<br>"
                        f"- **{high_risk_count}** of {len(paragraphs)} paragraphs exceed threshold<br>"
                        f"- Peak fear score: **{max_score:.3f}**"
                        f"</div>", unsafe_allow_html=True)

        elif avg_score >= 0.5:
            st.markdown(f'<div class="theme-status-box warning">'
                        f"### Moderate Concern<br>"
                        f"- Average score: **{avg_score:.3f}** (threshold: {threshold:.2f})<br>"
                        f"- **{high_risk_count}** segments above threshold<br>"
                        f"- Approaching concerning levels"
                        f"</div>", unsafe_allow_html=True)

        else:
            st.markdown(f'<div class="theme-status-box success">'
                        f"### Low Risk Content<br>"
                        f"- Average score: **{avg_score:.3f}** (well below {threshold:.2f})<br>"
                        f"- Only **{high_risk_count}** high-risk segments<br>"
                        f"- Generally balanced messaging"
                        f"</div>", unsafe_allow_html=True)

    with col2:
        st.markdown('<div style="margin-top:-5px; padding-top:0;"><h5 style="margin-bottom:5px;">Distribution</h5></div>', unsafe_allow_html=True)
        # Pie chart
        low = len(analysis_df[analysis_df["Fear Mongering Score"] < 0.5])
        medium = len(analysis_df[(analysis_df["Fear Mongering Score"] >= 0.5) &
                                (analysis_df["Fear Mongering Score"] < threshold)])
        high = len(analysis_df[analysis_df["Fear Mongering Score"] >= threshold])

        dist_df = pd.DataFrame({
            "Category": ["Low", "Medium", "High"],
            "Count": [low, medium, high]
        })

        fig = px.pie(
            dist_df,
            names="Category",
            values="Count",
            color="Category",
            color_discrete_map={
                "Low": "#4FC3F7",
                "Medium": "#FFD54F",
                "High": "#EF5350"
            }
        )

        fig.update_traces(
            textinfo="percent+label",
            hoverinfo="label+percent+value",
            marker=dict(line=dict(color="#0D1526", width=0))
        )

        fig.update_layout(
            height=320,  # make pie chart height match nicely
            margin=dict(l=10, r=10, t=0, b=0),
            showlegend=False,
            plot_bgcolor="#0D1526",
            paper_bgcolor="#0D1526"
        )

        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    # =======================
    # Chart
    # =======================
    st.subheader("Fear Mongering Trend")
    fig = create_plotly_chart(seconds, scores, paragraphs, chart_type=chart_type, max_hover_length=max_hover_length)
    st.plotly_chart(fig, use_container_width=True)


    # =======================
    # Table analysis
    # =======================
    st.subheader("Paragraph-Level Analysis")
    display_results_table(analysis_df, threshold)


    # ========================
    # DOWNLOAD RESULTS
    # ========================
    csv = analysis_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        "Download Results as CSV",
        data=csv,
        file_name="quick_fear_analysis.csv",
        mime="text/csv",
        key="download_fear_csv"
    )

 
    # ======================================================
    # FITBIT HEART RATE DATA LOADING
    # ======================================================
    st.write("---") 
    # with st.expander("Fitbit Heart Rate Data", expanded=False):
    st.subheader("Fitbit Heart Rate Data")

    # Two columns for compact layout
    col1, col2 = st.columns([3, 1])  # wider date input, narrower button

    with col1:
        fitbit_date = st.date_input(
            "Select date for Fitbit data",
            key="fitbit_date_input",
            help="Pick the date for which you want to load Fitbit heart rate data."
        )
    
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)  # adds vertical padding
        load_data = st.button("Load Data", key="load_fitbit_btn")

        # Button logic
    if load_data:
        with st.spinner("Fetching Fitbit data..."):
            df, date_str, error = get_fitbit_heart_data(fitbit_date.strftime("%Y-%m-%d"))
            if error:
                st.error(error)
            else:
                st.session_state["fitbit_data"] = df
                st.session_state["fitbit_date"] = date_str
                st.session_state["fitbit_fig"] = plot_fitbit_heart(df, date_str)
                st.rerun()

    # Display the figure if it exists
    if "fitbit_fig" in st.session_state:
        st.success(f"Fitbit heart rate data loaded for {st.session_state['fitbit_date']}")
        st.plotly_chart(st.session_state["fitbit_fig"], use_container_width=True)

        # Clear button below the plot
        if st.button("Clear Data", key="clear_fitbit_btn"):
            for key in ["fitbit_fig", "fitbit_data", "fitbit_date"]:
                st.session_state.pop(key, None)
            st.rerun()

    st.write("---") 

    
    # ======================================================
    # COMPARE FEAR RATING WITH HEART RATE
    # ======================================================
    st.header("Fear vs. Heart Rate Analysis")

    # User-selectable start time
    col1, col2 = st.columns(2)

    # Ensure fitbit_date is a date object
    fitbit_date_value = st.session_state.get("fitbit_date")
    if isinstance(fitbit_date_value, str):
        fitbit_date = datetime.strptime(fitbit_date_value, "%Y-%m-%d").date()
    elif fitbit_date_value is None:
        fitbit_date = datetime.now().date()
    else:
        fitbit_date = fitbit_date_value

    start_time_input = col1.time_input(
        "Start Time (HH:MM)",
        value=datetime.strptime("14:12", "%H:%M").time(),
        key="alignment_start_time"
    )
    duration_minutes = col2.number_input(
        "Duration (minutes)",
        min_value=1,
        max_value=30,
        value=10,
        key="alignment_duration"
    )

    if st.button("Auto-Align with Fitbit Heart Data", key="align_btn"):
        try:
            fear_df = st.session_state.get("fear_results_df")

            if fear_df is None:
                st.warning("Please run a fear analysis first (YouTube transcript).")
                st.stop()

            # Debug: Show what columns are available
            with st.expander("Debug: Fear DataFrame Info"):
                st.write("Available columns:", list(fear_df.columns))
                st.write("DataFrame shape:", fear_df.shape)
                st.write("Data types:", fear_df.dtypes.to_dict())
                
                # Check for time column
                for col in ['seconds', 'Seconds', 'timestamp', 'Timestamp', 'Start (s)']:
                    if col in fear_df.columns:
                        st.write(f"Found time column: '{col}'")
                        st.write(f"Sample values: {fear_df[col].head().tolist()}")
                        st.write(f"Data type: {fear_df[col].dtype}")
                        break
                
                st.dataframe(fear_df.head())

            # ---------------------------------------
            # Setup playback window
            # ---------------------------------------
            eastern = pytz.timezone("US/Eastern")

            # Combine date and time properly
            start_dt = eastern.localize(datetime.combine(fitbit_date, start_time_input))
            end_dt = start_dt + timedelta(minutes=duration_minutes)

            st.info(f"Playback window: {start_dt.strftime('%I:%M %p')} → {end_dt.strftime('%I:%M %p')}")

            # ---------------------------------------
            # Fetch Fitbit data for that time window
            # ---------------------------------------
            start_str = start_dt.strftime("%H:%M")
            end_str = end_dt.strftime("%H:%M")
            date_str = fitbit_date.strftime("%Y-%m-%d")

            endpoint = f"/1/user/-/activities/heart/date/{date_str}/1d/1min/time/{start_str}/{end_str}.json"
            data = fetch_fitbit_data(endpoint)

            intraday = data.get("activities-heart-intraday", {}).get("dataset", [])
            if not intraday:
                st.error("No intraday heart rate data found for that window.")
                st.stop()

            heart_df = pd.DataFrame(intraday)
            heart_df["datetime"] = pd.to_datetime(date_str + " " + heart_df["time"])
            heart_df["datetime"] = heart_df["datetime"].dt.tz_localize(eastern)

            st.success(f"✓ Fetched {len(heart_df)} heart rate readings")

            # ---------------------------------------
            # Rename fear score column if necessary
            # ---------------------------------------
            if "Fear Mongering Score" in fear_df.columns:
                fear_df = fear_df.rename(columns={"Fear Mongering Score": "fear_score"})

            # ---------------------------------------
            # Align & visualize
            # ---------------------------------------
            fig, merged_df = align_fear_and_heart(fear_df, heart_df, start_dt, end_dt)

            st.subheader("Aligned Fear vs Heart Rate")
            st.plotly_chart(fig, use_container_width=True)

            # Show summary statistics
            summary_col1, summary_col2, summary_col3 = st.columns(3)
            
            # Find the fear score column name
            fear_score_col = None
            for col in ['fear_score', 'Fear Mongering Score', 'score', 'Score']:
                if col in merged_df.columns:
                    fear_score_col = col
                    break
            
            if fear_score_col:
                summary_col1.metric("Avg Fear Score", f"{merged_df[fear_score_col].mean():.3f}")
            summary_col2.metric("Avg Heart Rate", f"{merged_df['value'].mean():.0f} bpm")
            summary_col3.metric("Data Points", len(merged_df))

            with st.expander("Show Aligned Data"):
                st.dataframe(merged_df.head(20))
                
                # Download button for merged data
                csv_merged = merged_df.to_csv(index=False).encode("utf-8")
                st.download_button(
                    "Download Aligned Data as CSV",
                    data=csv_merged,
                    file_name=f"fear_heart_aligned_{date_str}.csv",
                    mime="text/csv",
                    key="download_aligned_csv"
                )

        except Exception as e:
            st.error(f"Error aligning Fitbit and fear data: {e}")
            import traceback
            st.error(traceback.format_exc())


if __name__ == "__main__":
    main()
