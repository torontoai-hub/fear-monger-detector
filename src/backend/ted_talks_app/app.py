"""app.py - Main Streamlit application"""
import streamlit as st
import datetime
from models import load_classifier
from data_loader import load_transcripts
from utils import segment_text, assign_timestamps
from analysis import run_inference, create_analysis_df
from charts import create_matplotlib_chart, create_plotly_chart
from config import PREVIEW_CHARS, DEFAULT_FEAR_THRESHOLD



def display_transcript_preview(transcript):
    """Display transcript preview section"""
    st.subheader("Transcript Preview")
    st.write(transcript[:PREVIEW_CHARS] + "...") if transcript else st.write("No transcript available.")


def save_and_download_chart(fig, talk_index, chart_type="matplotlib"):
    """Save chart to file and create download button"""
    filename = f"fear_mongering_plot_{talk_index}_{chart_type}.png"

    try:
        if chart_type == "matplotlib":
            fig.savefig(filename, dpi=300)
            st.success(f"Matplotlib chart saved as {filename}")
        else:  # Plotly
            fig.write_image(filename, scale=2)
            st.success(f"Plotly chart saved as {filename}")
    except Exception as e:
        st.warning(f"Could not export {chart_type.title()} chart: {e}")
        return

    with open(filename, "rb") as f:
        st.download_button(
            f"Download {chart_type.title()} Chart (PNG)",
            data=f,
            file_name=filename,
            mime="image/png"
        )


def display_charts(seconds, scores, paragraphs, talk_index):
    """Display both matplotlib and plotly charts"""
    # Matplotlib chart
    # fig_mpl = create_matplotlib_chart(seconds, scores, talk_index)
    # st.pyplot(fig_mpl)
    # save_and_download_chart(fig_mpl, talk_index, "matplotlib")

    # Plotly chart
    fig_plotly = create_plotly_chart(seconds, scores, paragraphs, talk_index)
    st.plotly_chart(fig_plotly, use_container_width=True)
    save_and_download_chart(fig_plotly, talk_index, "plotly")


def display_results_table(analysis_df, talk_index, threshold, show_all_paragraphs):
    """Display results table and CSV download with filtering"""
    # Filter based on settings
    display_df = analysis_df.copy()
    
    if not show_all_paragraphs:
        display_df = display_df[display_df["Fear Mongering Score"] >= threshold]
        
        if len(display_df) == 0:
            st.warning(f"No paragraphs found above threshold {threshold:.2f}")
            return
        
        st.info(f"Showing {len(display_df)} of {len(analysis_df)} paragraphs (above threshold {threshold:.2f})")
    else:
        # Highlight high-scoring paragraphs
        high_score_count = len(analysis_df[analysis_df["Fear Mongering Score"] >= threshold])
        st.info(f"Total paragraphs: {len(analysis_df)} | High fear mongering (≥{threshold:.2f}): {high_score_count}")
    
    # Apply color styling
    def highlight_scores(row):
        score = row["Fear Mongering Score"]
        if score >= threshold:
            return ['background-color: #ffcccc'] * len(row)  # Light red - above threshold
        elif score >= 0.5:
            return ['background-color: #ffffcc'] * len(row)  # Light yellow - moderate
        else:
            return ['background-color: #ccffcc'] * len(row)  # Light green - low risk
    
    styled_df = display_df.style.apply(highlight_scores, axis=1)
    st.dataframe(styled_df, use_container_width=True)
    
    # Download button
    csv_data = display_df.to_csv(index=False).encode('utf-8')
    st.download_button(
        "Download Analysis as CSV",
        data=csv_data,
        file_name=f"fear_mongering_analysis_{talk_index}_threshold_{threshold:.2f}.csv",
        mime="text/csv"
    )


def main():
    """Main application logic"""

    # Custom CSS for better cursor interactions
    st.markdown("""
        <style>
        /* Pointer for expanders */
        .streamlit-expanderHeader {
            cursor: pointer !important;
        }
        
        /* Pointer for buttons */
        .stButton button {
            cursor: pointer !important;
        }
        
        /* Pointer for checkboxes and radio buttons */
        .stCheckbox label, .stRadio label {
            cursor: pointer !important;
        }
        
        /* Pointer for selectbox */
        .stSelectbox div[data-baseweb="select"] {
            cursor: pointer !important;
        }
        
        /* Hover effect for expanders */
        .streamlit-expanderHeader:hover {
            background-color: rgba(151, 166, 195, 0.15);
            transition: background-color 0.2s ease;
        }
        </style>
    """, unsafe_allow_html=True)

    
    # Load resources
    classifier = load_classifier()
    df = load_transcripts()

    st.title("Fear Mongering Detection - TED Talks")

    if df.empty:
        st.error("Failed to load transcript data. Please check your data files.")
        return
    
    st.sidebar.header("Talk Selection")

    # ============================================
    # Sorting and Paging
    # ============================================
    # Sorting
    sort_option = st.sidebar.selectbox(
        "Sort talks by:",
        ["title", "views", "published_date", "duration"],
        format_func=lambda x: x.replace("_", " ").title()
    )
    ascending_order = st.sidebar.checkbox("Ascending order", value=True)

    df_sorted = df.sort_values(by=sort_option, ascending=ascending_order).reset_index(drop=True)

    # Paging
    chunk_size = 50
    total_pages = (len(df_sorted) - 1) // chunk_size + 1
    page = st.sidebar.number_input(
        "Page number (1 = first 50 talks)",
        min_value=1,
        max_value=total_pages,
        value=1
    )
    start = (page - 1) * chunk_size
    end = min(start + chunk_size, len(df_sorted))

    st.sidebar.caption(f"Showing talks {start}–{end - 1} of {len(df_sorted)} total")

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

    with st.expander("More details"):
        st.markdown(f"**Description:** {selected_row.get('description', 'N/A')}")
        st.markdown(f"**Published Date:** {selected_row.get('published_date', 'N/A')}")
        st.markdown(f"**Views:** {selected_row.get('views', 'N/A')}")
        st.markdown(f"**Duration:** {selected_row.get('duration', 'N/A')} seconds")

    # Adjust talk_index to global dataset index
    talk_index = start + talk_index

    st.sidebar.markdown("---")
    
    st.sidebar.header("Analysis Settings")
    
    threshold = st.sidebar.slider(
        "Fear Mongering Threshold",
        min_value=0.0,
        max_value=1.0,
        value=DEFAULT_FEAR_THRESHOLD,
        step=0.05,
        help="Scores above this threshold are considered fear mongering"
    )
    
    show_all_paragraphs = st.sidebar.checkbox(
        "Show all paragraphs",
        value=True,
        help="Uncheck to show only high-scoring paragraphs"
    )
    
    st.sidebar.markdown("---")
    
    st.sidebar.header("Display Options")
    
    # chart_type = st.sidebar.radio(
    #     "Chart Type",
    #     options=["Line Chart", "Bar Chart", "Area Chart"],
    #     index=0
    # )
    
    color_scheme = st.sidebar.selectbox(
        "Color Scheme",
        options=["Default", "High Contrast", "Monochrome"],
        index=0
    )
    
    st.sidebar.markdown("---")

    transcript = df.iloc[talk_index]["transcript"]
    duration = df.iloc[talk_index]["duration"]

    st.sidebar.header("Information")
    st.sidebar.info(f"Analyzing talk #{talk_index}\n\n Duration: {duration:.1f} seconds")

    display_transcript_preview(transcript)

    paragraphs = segment_text(transcript)
    timestamps = assign_timestamps(paragraphs, duration)

    if not paragraphs:
        st.warning("No paragraphs found in transcript.")
        return

    predictions = run_inference(classifier, paragraphs)
    analysis_df = create_analysis_df(paragraphs, timestamps, predictions)

    seconds = timestamps["seconds"]
    scores = analysis_df["Fear Mongering Score"]

    # ============================================
    # MAIN DISPLAY PANEL
    # ============================================

    st.markdown("---")
    st.header("Fear Mongering Analysis Results")

    # Quick Stats
    col1, col2, col3, col4 = st.columns(4)

    avg_score = scores.mean()
    max_score = scores.max()
    min_score = scores.min()
    high_risk_count = len(analysis_df[analysis_df["Fear Mongering Score"] >= threshold])
    percentage = (high_risk_count / len(paragraphs)) * 100

    with col1:
        st.metric("Paragraphs", len(paragraphs))

    with col2:
        st.metric("Average", f"{avg_score:.3f}",
                  delta=f"{((avg_score - threshold) * 100):.0f}% vs threshold",
                  delta_color="inverse")

    with col3:
        st.metric("Peak", f"{max_score:.3f}",
                  delta=f"Low: {min_score:.3f}")

    with col4:
        st.metric("High Risk", f"{high_risk_count}",
                  delta=f"{percentage:.1f}% of talk")
        
    st.markdown("---")

    # Overall Assessment with More Context
    assessment_col1, assessment_col2 = st.columns([2, 1])

    with assessment_col1:
        if avg_score >= threshold:
            st.error(f"""
            ### High Fear Mongering Detected
            - Average score: **{avg_score:.3f}** (threshold: {threshold:.2f})
            - **{high_risk_count}** of {len(paragraphs)} paragraphs exceed threshold
            - Peak fear score: **{max_score:.3f}**
            """)
        elif avg_score >= 0.5:
            st.warning(f"""
            ### Moderate Concern
            - Average score: **{avg_score:.3f}** (threshold: {threshold:.2f})
            - **{high_risk_count}** segments above threshold
            - Approaching concerning levels
            """)
        else:
            st.success(f"""
            ### Low Risk Content
            - Average score: **{avg_score:.3f}** (well below {threshold:.2f})
            - Only **{high_risk_count}** high-risk segments
            - Generally balanced messaging
            """)

    with assessment_col2:
        st.markdown("#### Distribution")
        low = len(analysis_df[analysis_df["Fear Mongering Score"] < 0.5])
        medium = len(analysis_df[(analysis_df["Fear Mongering Score"] >= 0.5) & 
                                (analysis_df["Fear Mongering Score"] < threshold)])
        high = len(analysis_df[analysis_df["Fear Mongering Score"] >= threshold])
        
        st.markdown(f"""
        🟢 **Low:** {low} ({low/len(analysis_df)*100:.0f}%)  
        🟡 **Medium:** {medium} ({medium/len(analysis_df)*100:.0f}%)  
        🔴 **High:** {high} ({high/len(analysis_df)*100:.0f}%)
        """)

    st.markdown("---")

    # Visualizations Section
    st.subheader("Time-Series Analysis")
    # st.caption(f"Displaying as: {chart_type} | Color scheme: {color_scheme}")
    display_charts(seconds, scores, paragraphs, talk_index)

    st.markdown("---")

    # Top Findings (before full table)
    # Top Findings (before full table)
    if high_risk_count > 0:
        st.subheader("Top 5 Highest Risk Segments")
        top_df = analysis_df.nlargest(min(5, len(analysis_df)), "Fear Mongering Score")
        
        for i, (idx, row) in enumerate(top_df.iterrows(), 1):
            score = row["Fear Mongering Score"]
            badge = "🔴" if score >= threshold else "🟡"
            
            # Handle different possible column names
            start_time = row.get('Start Time', row.get('Start', 'N/A'))
            end_time = row.get('End Time', row.get('End', 'N/A'))
            
            with st.expander(
                f"{badge} **Rank #{i}** | Score: {score:.3f} | Time: {start_time} → {end_time}",
                expanded=(i == 1)  # Only expand #1
            ):
                st.write(row['Paragraph'])
                st.progress(score, text=f"Fear Mongering Score: {score:.3f}")
        
        st.markdown("---")

    # Full Data Table
    st.subheader("Complete Analysis Data")
    if not show_all_paragraphs:
        st.info(f"Filtered: Showing only paragraphs ≥ {threshold:.2f} threshold")
    else:
        st.info(f"Showing all {len(analysis_df)} paragraphs | Threshold set at {threshold:.2f}")

    display_results_table(analysis_df, talk_index, threshold, show_all_paragraphs)

    st.markdown("---")
    st.caption(f"Analysis complete | Talk #{talk_index} | {len(paragraphs)} paragraphs | Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    main()