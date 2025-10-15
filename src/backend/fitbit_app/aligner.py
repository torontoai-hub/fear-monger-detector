import pandas as pd
import numpy as np
import plotly.graph_objects as go
import pytz
from datetime import timedelta

def time_to_seconds(time_str):
    """Convert a time string to total seconds.
    
    Supports formats:
        - HH:MM:SS
        - H:MM:SS
        - MM:SS
        - numeric seconds as string or float
    
    Returns:
        float: total seconds, or None if conversion fails
    """
    try:
        time_str = str(time_str).strip()
        parts = time_str.split(':')

        if len(parts) == 3: # HH:MM:SS or H:MM:SS
            h, m, s = parts
            return int(h) * 3600 + int(m) * 60 + float(s)
        
        elif len(parts) == 2:  # MM:SS+++
            m, s = parts
            return int(m) * 60 + float(s)
        else:
            return float(time_str) # numeric value in seconds
    except:
        return None

def align_fear_and_heart(fear_df, heart_df, start_time, end_time):
    """
    Aligns fear model outputs with Fitbit heart rate data within a playback window.
    
    This function converts model-generated fear timestamps to real-world datetime
    values scaled to the playback window. Heart rate readings are trimmed to the
    same window. Both series are normalized to a 0 → 1 relative timeline, and then
    merged for comparison.
    
    The resulting Plotly chart has dual axes: fear score on the left, heart rate on the right.
    
    Args:
        fear_df (pd.DataFrame): Contains fear model outputs. Must have either:
            - 'Timestamp' column (HH:MM:SS style) or
            - 'datetime' column.
            Must contain a fear score column (detected automatically among
            ['fear_score', 'Fear Mongering Score', 'score', 'Score']).
        heart_df (pd.DataFrame): Contains heart rate readings with a 'datetime' column
            and a 'value' column (heart rate in bpm).
        start_time (pd.Timestamp): Playback window start.
        end_time (pd.Timestamp): Playback window end.
    
    Returns:
        fig (go.Figure): Interactive Plotly chart comparing fear and heart rate.
        merged (pd.DataFrame): Merged DataFrame of normalized fear scores and heart rates
            with 'relative' timeline between 0 and 1.
    
    Raises:
        ValueError: If required columns are missing or no data in the playback window.
    """
    
    print("=" * 50)
    print("Starting alignment...")
    
    # Make copies to avoid modifying original DataFrames
    fear_df = fear_df.copy()
    heart_df = heart_df.copy()
    
    # -----------------------
    # Handle fear DataFrame datetime conversion
    # -----------------------
    if "Timestamp" in fear_df.columns:

        # Convert Timestamp column (format like "0:00:00") to seconds
        fear_df['seconds_numeric'] = fear_df["Timestamp"].apply(time_to_seconds)
        
        # Scale model seconds to fit playback window
        total_seconds = (end_time - start_time).total_seconds()
        max_fear_seconds = fear_df['seconds_numeric'].max()
        scale = total_seconds / max_fear_seconds if max_fear_seconds > 0 else 1
        
        print(f"Fear data: {len(fear_df)} points, scaling {max_fear_seconds:.1f}s → {total_seconds:.1f}s")
        
        # Create timezone-aware datetime aligned to playback window
        fear_df["datetime"] = fear_df['seconds_numeric'].apply(
            lambda s: start_time + timedelta(seconds=float(s) * scale)
        )
    elif "datetime" not in fear_df.columns:
        raise ValueError("Expected 'Timestamp' or 'datetime' column in fear_df")
    
    # -----------------------
    # Ensure heart_df datetime is timezone-aware
    # -----------------------
    if heart_df["datetime"].dt.tz is None:
        heart_df["datetime"] = heart_df["datetime"].dt.tz_localize(pytz.timezone("US/Eastern"))
    
    # Ensure fear_df datetime is also timezone-aware (should match heart_df)
    if fear_df["datetime"].dt.tz is None:
        # If start_time has timezone, use that
        if hasattr(start_time, 'tz') and start_time.tz is not None:
            tz = start_time.tz
        else:
            tz = pytz.timezone("US/Eastern")
        fear_df["datetime"] = fear_df["datetime"].dt.tz_localize(tz)
    
    print(f"Time window: {start_time} to {end_time}")
    
    # -----------------------
    # Trim heart rate to playback window
    # -----------------------
    mask = (heart_df["datetime"] >= start_time) & (heart_df["datetime"] <= end_time)
    sliced_heart = heart_df.loc[mask].copy()
    
    if sliced_heart.empty:
        raise ValueError("No heart rate data available in that window.")
    
    print(f"Heart data: {len(sliced_heart)} readings in window")
    
    # -----------------------
    # Normalize both series for alignment
    # -----------------------
    sliced_heart = sliced_heart.sort_values("datetime").reset_index(drop=True)
    fear_df = fear_df.sort_values("datetime").reset_index(drop=True)
    
    # Assign relative position 0 → 1 for merging
    sliced_heart["relative"] = np.linspace(0, 1, len(sliced_heart))
    fear_df["relative"] = np.linspace(0, 1, len(fear_df))
    
    # Detect fear score column
    fear_score_col = None
    for col in ['fear_score', 'Fear Mongering Score', 'score', 'Score']:
        if col in fear_df.columns:
            fear_score_col = col
            break
    
    if fear_score_col is None:
        raise ValueError(f"Could not find fear score column. Available: {list(fear_df.columns)}")
    
    print(f"Using fear score column: '{fear_score_col}'")
    
    # -----------------------
    # Merge datasets on relative position
    # -----------------------
    merged = pd.merge_asof(
        fear_df.sort_values("relative"),
        sliced_heart[['relative', 'value']].sort_values("relative"),
        on="relative",
        direction="nearest"
    )
    
    print(f"✓ Merged {len(merged)} data points")
    print("=" * 50)
    
    # -----------------------
    # Create Plotly dual-axis chart
    # -----------------------
    fig = go.Figure()
    
    # Fear rating (left y-axis)
    fig.add_trace(go.Scatter(
        x=merged["relative"],
        y=merged[fear_score_col],
        name="Fear Rating",
        line=dict(color="blue", width=2),
        mode='lines',
        # marker=dict(size=6)
    ))
    
    # Heart rate (right y-axis)
    fig.add_trace(go.Scatter(
        x=merged["relative"],
        y=merged["value"],
        name="Heart Rate (bpm)",
        line=dict(color="red", width=2),
        mode='lines',
        # marker=dict(size=6),
        yaxis="y2"
    ))
    
    fig.update_layout(
        title="Fear Intensity vs Heart Rate (Normalized Timeline)",
        xaxis=dict(title="Normalized Progress (0 → 1)", showgrid=True),
        yaxis=dict(title="Fear Score", color="blue", showgrid=True),
        yaxis2=dict(title="Heart Rate (bpm)", overlaying="y", side="right", color="red"),
        template="plotly_white",
        height=500,
        hovermode='x unified'
    )
    
    return fig, merged