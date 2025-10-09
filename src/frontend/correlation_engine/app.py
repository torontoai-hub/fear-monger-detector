
from datetime import datetime, timedelta
import pandas as pd
from pathlib import Path
import matplotlib.pyplot as plt
import streamlit as st
import pytz
import nltk
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
from backend.ted_talks_app.data_loader import load_transcripts
base_dir = Path(__file__).resolve().parents[2]

def load_css(file_path):
    with open(file_path) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

def main():

    load_css("styles.css")

    try:
        nltk.data.find("tokenizers/punkt")
    except LookupError:
        nltk.download("punkt")


    if "classifier" not in st.session_state:
        with st.spinner("Loading fear detection model..."):
            st.session_state.classifier = load_classifier()

    classifier = st.session_state.classifier

  
    # ======================================================
    # STREAMLIT UI
    # ======================================================

    st.title("Fear Mongering Checker")

    # ======================================================
    # Segmentation Settings
    # ======================================================

    with st.sidebar.expander("Segmentation Options", expanded=False):

        # st.sidebar.header("Segmentation Settings")

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
        # Threshold Settings
        # ======================================================
        threshold = st.slider(
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
            value=DEFAULT_SMOOTHING_WINDOW,
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
            value=30,
            step=10,
            help="Limit number of characters shown in chart hover text."
        )

    # ======================================================
    # Load Model
    # ======================================================
    # classifier = load_classifier()

    # ======================================================
    # Text Input
    # ======================================================

    url_input = st.text_input("Enter YouTube URL", help="Paste a YouTube link to fetch transcript automatically.")

    # text_input = st.text_area(
    #     "Or paste transcript text here:",
    #     height=200,
    #     help="Paste the transcript text directly if you don’t want to use a URL."
    # )

    # embed_code = f"""
    # <iframe width="800" height="450"
    # src="https://www.youtube.com/embed/{video_id}?start={start_time}&autoplay=0"
    # frameborder="0" allowfullscreen>
    # </iframe>
    # """

    # ======================================================
    # Paste transcript
    # ====================================================== 
    quick_text = st.text_area(
        "Or paste transcript text here:", 
        height=200,
        help="Paste the transcript text directly if you don’t want to use a URL."
    )
    
    # ======================================================
    # Ted Talks
    # ======================================================
    with st.sidebar.expander("TED Talks", expanded=False):
        df = load_transcripts()

        # st.subheader("TED Talks")

        if df.empty:
            st.error("Failed to load transcript data. Please check your data files.")
            return
        
        st.header("Talk Selection")
    # ============================================
        # Sorting and Paging
        # ============================================
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
        page = st.number_input(
            "Page number (1 = first 50 talks)",
            min_value=1,
            max_value=total_pages,
            value=1
        )
        start = (page - 1) * chunk_size
        end = min(start + chunk_size, len(df_sorted))

        # st.sidebar.caption(f"Showing talks {start}–{end - 1} of {len(df_sorted)} total")

        # Talk selection within the current page


        talk_index = st.slider(
            f"Select talk (in page {page})",
            min_value=0,
            max_value=end - start - 1,
            value=0
        )
        
        selected_row = df_sorted.iloc[start + talk_index]

        # Metadata summary
        st.markdown(f"**Title:** {selected_row['title']}")
        st.markdown(f"**Speaker:** {selected_row['main_speaker']}")
        st.markdown(f"**URL:** [{selected_row['url']}]({selected_row['url']})")

        # with st.expander("More details"):
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
        
        # st.sidebar.markdown("---")
        
        # st.sidebar.header("Display Options")




    # ======================================================
    # Run Analysis
    # ======================================================
    transcript_text = None
    video_id = None

    if url_input.strip():
        video_id = get_video_id(url_input.strip())
        if video_id:
            st.info(f"Fetching transcript for video ID: `{video_id}` ...")
            transcript_text = fetch_transcript(video_id)
            if transcript_text:
                st.success("Transcript fetched successfully.")
                with st.expander("Transcript Preview"):
                    st.text_area("Transcript", transcript_text[:4000], height=250, key="transcript_preview")

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

                # # Embed YouTube video
                # embed_code = f"""
                # <iframe width="700" height="450"
                # src="https://www.youtube.com/embed/{video_id}"
                # frameborder="0" allowfullscreen>
                # </iframe>
                # """
                # st.markdown(embed_code, unsafe_allow_html=True)
            else:
                st.error("Could not fetch transcript.")
                return
        else:
            st.error("Invalid YouTube URL.")
            return

    # FALLBACK: use pasted transcript text
    elif quick_text.strip():
        transcript_text = quick_text

    else:
        st.info("Paste text or YouTube link above to begin analysis.")
        return


    # if quick_text.strip():
    #     if "youtube.com" in quick_text or "youtu.be" in quick_text or len(quick_text.strip()) == 11:
    #         video_id = get_video_id(quick_text.strip())
    #         if video_id:
    #             st.info(f"Fetching transcript for video ID: `{video_id}` ...")
    #             transcript_text = fetch_transcript(video_id)
    #             if transcript_text:
    #                 st.success("Transcript fetched successfully.")
    #                 with st.expander("Transcript Preview"):
    #                     st.text_area("Transcript", transcript_text[:4000], height=250, key="transcript_preview")
    #             else:
    #                 st.error("Could not fetch transcript.")
    #                 return
    #         else:
    #             st.error("Invalid YouTube URL or video ID.")
    #             return
    #     else:
    #         transcript_text = quick_text
    # else:
    #     st.info("Paste text or YouTube link above to begin analysis.")
    #     return

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

    # ======================================================
    # Run model inference and create analysis DataFrame
    # ======================================================
    predictions = run_inference(classifier, paragraphs)

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
    st.download_button(
        "Download Results as CSV",
        data=csv,
        file_name="quick_fear_analysis.csv",
        mime="text/csv",
        key="download_fear_csv"
    )

 


    # ======================================================
    # FITBIT HEART RATE DATA
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

    # fitbit_date = st.date_input("Select date for Fitbit data", key="fitbit_date_input")

    # Sidebar controls
    # if st.button("Load Fitbit Heart Data", key="load_fitbit_btn"):
    #     with st.spinner("Fetching Fitbit data..."):
    #         df, date_str, error = get_fitbit_heart_data(fitbit_date.strftime("%Y-%m-%d"))
    #         if error:
    #             st.error(error)
    #         else:
    #             # Store in session state
    #             st.session_state["fitbit_data"] = df
    #             st.session_state["fitbit_date"] = date_str
    #             st.session_state["fitbit_fig"] = plot_fitbit_heart(df, date_str)
    #             st.rerun()


    # # Display the figure if it exists in session state
    # if "fitbit_fig" in st.session_state:
    #     st.success(f"Fitbit heart rate data loaded for {st.session_state['fitbit_date']}")
    #     st.plotly_chart(st.session_state["fitbit_fig"], use_container_width=True)


    #     # Optional: Add a clear button
    #     if st.button("Clear Fitbit Data", key="clear_fitbit_btn"):
    #         del st.session_state["fitbit_fig"]
    #         del st.session_state["fitbit_data"]
    #         del st.session_state["fitbit_date"]
    #         st.rerun()

    


    st.write("---") 
    # ======================================================
    # COMPARE FEAR RATING WITH HEART RATE
    # ======================================================
    st.header("Compare Fear Rating with Heart Rate")

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