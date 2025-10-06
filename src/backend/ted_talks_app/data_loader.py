"""data_loader.py - Load transcript data"""
import streamlit as st
import pandas as pd
from config import DATA_DIR


@st.cache_data
def load_transcripts():
    """Load and merge transcript data"""
    try:
        transcripts_path = DATA_DIR / "ted_talks_transcripts.csv"
        metadata_path = DATA_DIR / "ted_main.csv"
        
        # Check if files exist
        if not transcripts_path.exists():
            st.error(f"Transcripts file not found: {transcripts_path}")
            return pd.DataFrame()
        
        if not metadata_path.exists():
            st.error(f"Metadata file not found: {metadata_path}")
            return pd.DataFrame()
        
        transcripts_df = pd.read_csv(transcripts_path)
        metadata_df = pd.read_csv(metadata_path)
        
        merged_df = pd.merge(transcripts_df, metadata_df, on="url", how="left")
        
        if merged_df.empty:
            st.warning("Data loaded but contains no records.")
        
        return merged_df
    
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return pd.DataFrame()