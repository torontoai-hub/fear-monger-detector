# """app.py - Fear Mongering Quick Check Tool"""
from datetime import datetime, timedelta
import pandas as pd
from pathlib import Path
import matplotlib.pyplot as plt

import streamlit as st
import pytz
from backend.fear_monger_processor.model import load_classifier
from backend.fear_monger_processor.inference import run_inference
from backend.fear_monger_processor.transcript import get_video_id, fetch_transcript
from backend.fear_monger_processor.utils import segment_text, assign_timestamps, create_analysis_df, create_plotly_chart, display_results_table
from frontend.correlation_engine.config import MAX_CHARS, DEFAULT_FEAR_THRESHOLD, DEFAULT_SMOOTHING_WINDOW, DEFAULT_CHART_TYPE
from backend.fitbit_app.fitbit_utils import get_fitbit_heart_data, plot_fitbit_heart
from backend.fitbit_app.fitbit_client import fetch_fitbit_data
from backend.fitbit_app.aligner import align_fear_and_heart
from backend.fitbit_app.playback_window import estimate_playback_window
from backend.fitbit_app.config import TOKEN_FILE
base_dir = Path(__file__).resolve().parents[2]

def main():
    # # ======================================================
    # # STREAMLIT UI
    # # ======================================================

    st.title("Fear Mongering Check")

    # ======================================================
    # Segmentation Settings
    # ======================================================
    st.sidebar.header("Segmentation Settings")
    

    # segment_mode = st.sidebar.radio("Segment text by:", ["Characters", "Sentences", "Both"], index=2)

    segment_mode = st.sidebar.radio(
        "Segment text by:",
        ["Characters", "Sentences", "Both"],
        index=2,  # Default to "Both"
        help="Choose how to split the text into paragraphs for analysis."
    )

    max_chars = MAX_CHARS
    max_sentences = 5

    if segment_mode in ("Characters", "Both"):
        max_chars = st.sidebar.slider(
            "Maximum Characters per Segment",
            min_value=200,
            max_value=600,
            value=MAX_CHARS,  # now defaults to 350
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
        help="Adjust the threshold for analysis."
        )
    
    # ======================================================
    # Advanced Options
    # ======================================================
    with st.sidebar.expander("Advanced Options", expanded=False):
        smoothing_window = st.slider(
            "Smoothing Window Size",
            min_value=1,
            max_value=10,
            value=DEFAULT_SMOOTHING_WINDOW,  # now defaults to 7
            step=1,
            help="Larger window smooths the fear mongering score more."
        )

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
    quick_text = st.text_area("Paste text or YouTube link here:", height=250)


    # ======================================================
    # Run Analysis
    # ======================================================
    transcript_text = None

    if quick_text.strip():
        if "youtube.com" in quick_text or "youtu.be" in quick_text or len(quick_text.strip()) == 11:
            video_id = get_video_id(quick_text.strip())
            if video_id:
                st.info(f"Fetching transcript for video ID: `{video_id}` ...")
                transcript_text = fetch_transcript(video_id)
                if transcript_text:
                    st.success("Transcript fetched successfully.")
                    with st.expander("Transcript Preview"):
                        st.text_area("Transcript", transcript_text[:4000], height=250)
                else:
                    st.error("Could not fetch transcript.")
                    return
            else:
                st.error("Invalid YouTube URL or video ID.")
                return
        else:
            transcript_text = quick_text
    else:
        st.info("Paste text or YouTube link above to begin analysis.")
        return

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
    timestamps = assign_timestamps(paragraphs, fake_duration)


    # ======================================================
    # Run model inference and create analysis DataFrame
    # ======================================================
    predictions = run_inference(classifier, paragraphs)

    # analysis_df = create_analysis_df(paragraphs, timestamps, predictions, smoothing_window=smoothing_window)

    analysis_df = create_analysis_df(
        paragraphs=paragraphs,
        timestamps=timestamps,
        predictions=predictions,
        smoothing_window=smoothing_window,
        video_duration_seconds=fake_duration,  # simulated or real video duration
    )

    # Save results for downstream correlation
    st.session_state["fear_results_df"] = analysis_df
    st.session_state["video_duration_seconds"] = fake_duration

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
    fig = create_plotly_chart(seconds, scores, paragraphs, chart_type=chart_type, max_hover_length=max_hover_length)
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Paragraph-Level Analysis")
    display_results_table(analysis_df, threshold)

    # ======================================================
    # Table & CSV Download
    # ======================================================
    csv = analysis_df.to_csv(index=False).encode("utf-8")
    st.download_button("Download Results as CSV", data=csv, file_name="quick_fear_analysis.csv", mime="text/csv")



    # ======================================================
    # FIT BIT DATA
    # ======================================================
    st.sidebar.header("Fitbit Heart Rate Data")

    fitbit_date = st.sidebar.date_input("Select date for Fitbit data")

    # Display the figure if it exists in session state
    if "fitbit_fig" in st.session_state:
        st.success(f"✓ Fitbit heart rate data loaded for {st.session_state['fitbit_date']}")
        st.plotly_chart(st.session_state["fitbit_fig"], use_container_width=True)
        
        # Optional: Add a clear button
        if st.button("Clear Fitbit Data"):
            del st.session_state["fitbit_fig"]
            del st.session_state["fitbit_data"]
            del st.session_state["fitbit_date"]
            st.rerun()

    # Sidebar controls
    if st.sidebar.button("Load Fitbit Heart Data"):
        with st.spinner("Fetching Fitbit data..."):
            df, date_str, error = get_fitbit_heart_data(fitbit_date.strftime("%Y-%m-%d"))
            if error:
                st.error(error)
            else:
                # Store in session state
                st.session_state["fitbit_data"] = df
                st.session_state["fitbit_date"] = date_str
                st.session_state["fitbit_fig"] = plot_fitbit_heart(df, date_str)
                st.rerun()  # Rerun to show the data

    st.header("Compare Fear Rating with Heart Rate")


    if st.button("Auto-Align with Fitbit Heart Data"):
        try:
            fear_df = st.session_state.get("fear_results_df")
            video_duration = st.session_state.get("video_duration_seconds", None)

            if fear_df is None or video_duration is None:
                st.warning("Please run a fear analysis first (YouTube transcript).")
            else:
                date_str = fitbit_date.strftime("%Y-%m-%d")
                st.info(f"Using Fitbit data for: {date_str}")

                # -----------------------------
                # Test playback window
                # -----------------------------
                from datetime import datetime, timedelta
                import pytz

                eastern = pytz.timezone("US/Eastern")
                start_dt = eastern.localize(datetime.strptime(f"{date_str} 14:12:00", "%Y-%m-%d %H:%M:%S"))
                end_dt = start_dt + timedelta(minutes=1)

                st.info(f"Playback window: {start_dt.strftime('%I:%M %p')} → {end_dt.strftime('%I:%M %p')}")

                # -----------------------------
                # Fetch Fitbit heart rate data for window
                # -----------------------------
                start_time_str = start_dt.strftime("%H:%M")
                end_time_str = end_dt.strftime("%H:%M")
                endpoint = f"/1/user/-/activities/heart/date/{date_str}/1d/1sec/time/{start_time_str}/{end_time_str}.json"

                data = fetch_fitbit_data(endpoint)
                intraday = data.get("activities-heart-intraday", {}).get("dataset", [])

                if not intraday:
                    st.error("No intraday heart rate data found for this window.")
                    st.stop()

                heart_df = pd.DataFrame(intraday)
                heart_df["datetime"] = pd.to_datetime(date_str + " " + heart_df["time"])
                heart_df["datetime"] = heart_df["datetime"].dt.tz_localize(eastern)

                # Filter to exact window
                heart_df = heart_df[
                    (heart_df["datetime"] >= start_dt) &
                    (heart_df["datetime"] <= end_dt)
                ]

                st.write("Heart rate data range:", heart_df["datetime"].min(), "→", heart_df["datetime"].max())

                # -----------------------------
                # Rename fear score column
                # -----------------------------
                if "Fear Mongering Score" in fear_df.columns:
                    fear_df = fear_df.rename(columns={"Fear Mongering Score": "fear_score"})

                # -----------------------------
                # Align and visualize
                # -----------------------------
                fig, merged = align_fear_and_heart(fear_df, heart_df, start_dt, end_dt)
                st.plotly_chart(fig, use_container_width=True)

                with st.expander("Show Aligned Data (Debug View)"):
                    st.dataframe(merged.head(10))

        except Exception as e:
            st.error(f"Error aligning Fitbit and fear data: {e}")

if __name__ == "__main__":
    main()

