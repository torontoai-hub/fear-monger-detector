# import pandas as pd
# import numpy as np
# import plotly.graph_objects as go
# import pytz
# from datetime import timedelta


# def align_fear_and_heart(fear_df, heart_df, start_time, end_time):
#     """
#     Align fear model outputs (0–600s) with Fitbit heart rate readings
#     within a fixed 10-minute window.
#     """

#     # -----------------------------------
#     # Map 0–600s fear timestamps to window
#     # -----------------------------------
#     total_seconds = (end_time - start_time).total_seconds()
#     scale = total_seconds / 600  # scale factor if window ≠ 10 min (still flexible)

#     # Expect 'seconds' column from assign_timestamps()
#     if "seconds" not in fear_df.columns:
#         raise ValueError("Expected 'seconds' column in fear_df for alignment.")

#     fear_df["datetime"] = [
#         start_time + timedelta(seconds=s * scale) for s in fear_df["seconds"]
#     ]

#     # -----------------------------------
#     # Standardize timezone handling
#     # -----------------------------------
#     fear_df["datetime"] = pd.to_datetime(fear_df["datetime"]).dt.tz_localize(None)
#     heart_df["datetime"] = pd.to_datetime(heart_df["datetime"]).dt.tz_localize(None)

#     # -----------------------------------
#     # Align on nearest timestamp
#     # -----------------------------------
#     fear_df = fear_df.sort_values("datetime")
#     heart_df = heart_df.sort_values("datetime")

#     merged = pd.merge_asof(
#         fear_df,
#         heart_df,
#         on="datetime",
#         direction="nearest"
#     )

#     # """
#     # Aligns normalized fear ratings and heart rate within a specific window.

#     # Handles fractional seconds and timezone-aware comparisons.
#     # """

#     # # -----------------------
#     # # Ensure datetime columns
#     # # -----------------------

#     # if "Timestamp" in fear_df.columns:
#     #     fear_df["datetime"] = pd.to_datetime(
#     #         fear_df["Timestamp"].astype(str),
#     #         format="%H:%M:%S.%f",
#     #         errors="coerce"
#     #     )
#     #     # fallback if fractional seconds fail
#     #     if fear_df["datetime"].isna().any():
#     #         fear_df.loc[fear_df["datetime"].isna(), "datetime"] = pd.to_datetime(
#     #             fear_df.loc[fear_df["datetime"].isna(), "Timestamp"].astype(str),
#     #             format="%H:%M:%S",
#     #             errors="coerce"
#     #         )

#     # # Ensure heart_df["datetime"] is timezone-aware
#     # if heart_df["datetime"].dt.tz is None:
#     #     heart_df["datetime"] = heart_df["datetime"].dt.tz_localize(pytz.timezone("US/Eastern"))

#     # # -----------------------
#     # # Trim to playback window
#     # # -----------------------
#     # mask = (heart_df["datetime"] >= start_time) & (heart_df["datetime"] <= end_time)
#     # sliced_heart = heart_df.loc[mask].copy()

#     # if sliced_heart.empty:
#     #     raise ValueError("No heart rate data available in that window.")

#     # # -----------------------
#     # # Normalize both series
#     # # -----------------------
#     # sliced_heart["relative"] = np.linspace(0, 1, len(sliced_heart))
#     # fear_df = fear_df.sort_values("datetime")
#     # fear_df["relative"] = np.linspace(0, 1, len(fear_df))

#     # merged = pd.merge_asof(
#     #     fear_df.sort_values("relative"),
#     #     sliced_heart.sort_values("relative"),
#     #     on="relative",
#     #     direction="nearest"
#     # )

#     # -----------------------
#     # Create Plotly chart
#     # -----------------------
#     fig = go.Figure()
#     fig.add_trace(go.Scatter(
#         x=merged["relative"], y=merged["fear_score"],
#         name="Fear Rating", line=dict(color="blue")
#     ))
#     fig.add_trace(go.Scatter(
#         x=merged["relative"], y=merged["value"],
#         name="Heart Rate (bpm)", line=dict(color="red"), yaxis="y2"
#     ))
#     fig.update_layout(
#         title="Fear Intensity vs Heart Rate (Normalized Timeline)",
#         xaxis=dict(title="Normalized Progress (0 → 1)"),
#         yaxis=dict(title="Fear Score", color="blue"),
#         yaxis2=dict(title="Heart Rate (bpm)", overlaying="y", side="right", color="red"),
#         template="plotly_white", height=500
#     )

#     return fig, merged



# import pandas as pd
# import numpy as np
# import plotly.graph_objects as go
# import pytz
# from datetime import timedelta


# def align_fear_and_heart(fear_df, heart_df, start_time, end_time):
#     """
#     Align fear model outputs (0–600s) with Fitbit heart rate readings
#     within a fixed playback window.

#     Returns:
#         fig: Plotly chart
#         merged: Merged DataFrame of fear scores and heart rates
#     """

#     # -----------------------
#     # Ensure datetime consistency
#     # -----------------------
#     if "seconds" not in fear_df.columns:
#         raise ValueError("Expected 'seconds' column in fear_df for alignment.")

#     # Map fear timestamps to the fixed window
#     total_seconds = (end_time - start_time).total_seconds()
#     scale = total_seconds / 600  # fixed duration scaling

#     fear_df["datetime"] = [
#         start_time + timedelta(seconds=s * scale) for s in fear_df["seconds"]
#     ]

#     # Remove timezone to avoid errors during merging
#     fear_df["datetime"] = pd.to_datetime(fear_df["datetime"]).dt.tz_localize(None)

#     if "datetime" in heart_df.columns:
#         if heart_df["datetime"].dt.tz is not None:
#             heart_df["datetime"] = heart_df["datetime"].dt.tz_convert(None)
#     else:
#         raise ValueError("Expected 'datetime' column in heart_df.")

#     # -----------------------
#     # Trim heart rate data to playback window
#     # -----------------------
#     mask = (heart_df["datetime"] >= start_time) & (heart_df["datetime"] <= end_time)
#     sliced_heart = heart_df.loc[mask].copy()

#     if sliced_heart.empty:
#         raise ValueError("No heart rate data found in playback window.")

#     # -----------------------
#     # Normalize both series for alignment
#     # -----------------------
#     fear_df = fear_df.sort_values("datetime").reset_index(drop=True)
#     sliced_heart = sliced_heart.sort_values("datetime").reset_index(drop=True)

#     fear_df["relative"] = np.linspace(0, 1, len(fear_df))
#     sliced_heart["relative"] = np.linspace(0, 1, len(sliced_heart))

#     merged = pd.merge_asof(
#         fear_df,
#         sliced_heart,
#         on="relative",
#         direction="nearest"
#     )

#     # -----------------------
#     # Create Plotly chart
#     # -----------------------
#     fig = go.Figure()

#     fig.add_trace(go.Scatter(
#         x=merged["relative"],
#         y=merged.get("fear_score", [0] * len(merged)),
#         name="Fear Rating",
#         line=dict(color="blue")
#     ))

#     fig.add_trace(go.Scatter(
#         x=merged["relative"],
#         y=merged.get("value", [0] * len(merged)),
#         name="Heart Rate (bpm)",
#         line=dict(color="red"),
#         yaxis="y2"
#     ))

#     fig.update_layout(
#         title="Fear Intensity vs Heart Rate (Normalized Timeline)",
#         xaxis=dict(title="Normalized Progress (0 → 1)"),
#         yaxis=dict(title="Fear Score", color="blue"),
#         yaxis2=dict(title="Heart Rate (bpm)", overlaying="y", side="right", color="red"),
#         template="plotly_white",
#         height=500
#     )

#     return fig, merged


# import pandas as pd
# import numpy as np
# import plotly.graph_objects as go
# from datetime import timedelta

# def time_to_seconds(time_str):
#     """Convert time string (HH:MM:SS or MM:SS or H:MM:SS) to seconds."""
#     try:
#         time_str = str(time_str).strip()
#         parts = time_str.split(':')
#         if len(parts) == 3:  # HH:MM:SS or H:MM:SS
#             h, m, s = parts
#             return int(h) * 3600 + int(m) * 60 + float(s)
#         elif len(parts) == 2:  # MM:SS
#             m, s = parts
#             return int(m) * 60 + float(s)
#         else:
#             return float(time_str)
#     except:
#         return None

# def align_fear_and_heart(fear_df, heart_df, start_time, end_time):
#     """
#     Align fear model outputs with Fitbit heart rate readings
#     within a fixed playback window.

#     Returns:
#         fig: Plotly chart
#         merged: Merged DataFrame of fear scores and heart rates
#     """

#     print("=" * 50)
#     print("Starting alignment process...")
    
#     # -----------------------
#     # Identify and convert the seconds/timestamp column
#     # -----------------------
#     fear_df = fear_df.copy()
    
#     # Check for various possible column names
#     seconds_col = None
#     for col in ['seconds', 'Seconds', 'timestamp', 'Timestamp', 'Start (s)']:
#         if col in fear_df.columns:
#             seconds_col = col
#             print(f"Found time column: '{col}'")
#             break
    
#     if seconds_col is None:
#         # If no seconds column found, create one based on index
#         fear_df['seconds_numeric'] = np.linspace(0, 600, len(fear_df))
#         print("No time column found, created synthetic timestamps")
#     else:
#         # Check if it's a time string format (HH:MM:SS or MM:SS)
#         sample_value = str(fear_df[seconds_col].iloc[0])
        
#         if ':' in sample_value:
#             print(f"Converting time strings to seconds...")
#             fear_df['seconds_numeric'] = fear_df[seconds_col].apply(time_to_seconds)
#         else:
#             print(f"Converting numeric time values...")
#             fear_df['seconds_numeric'] = pd.to_numeric(fear_df[seconds_col], errors='coerce')
    
#     # Drop any rows where conversion failed
#     fear_df = fear_df.dropna(subset=['seconds_numeric'])
    
#     if len(fear_df) == 0:
#         raise ValueError("No valid numeric values found in time/seconds column")
    
#     print(f"Fear data: {len(fear_df)} points, range {fear_df['seconds_numeric'].min():.1f}s to {fear_df['seconds_numeric'].max():.1f}s")
    
#     # -----------------------
#     # Map fear timestamps to the fixed window
#     # -----------------------
#     total_seconds = (end_time - start_time).total_seconds()
#     max_fear_seconds = fear_df['seconds_numeric'].max()
#     scale = total_seconds / max_fear_seconds if max_fear_seconds > 0 else 1
    
#     print(f"Scaling: {max_fear_seconds:.1f}s → {total_seconds:.1f}s (factor: {scale:.3f})")

#     # Create datetime column by scaling fear timestamps
#     fear_df["datetime"] = fear_df['seconds_numeric'].apply(
#         lambda s: start_time + timedelta(seconds=float(s) * scale)
#     )

#     # -----------------------
#     # Standardize timezone handling - make everything tz-naive
#     # -----------------------
#     # Remove timezone from fear datetimes
#     fear_df["datetime"] = pd.to_datetime(fear_df["datetime"]).dt.tz_localize(None)
    
#     # Handle heart_df datetime - remove timezone
#     if "datetime" not in heart_df.columns:
#         raise ValueError("Expected 'datetime' column in heart_df.")
    
#     heart_df = heart_df.copy()
#     heart_df["datetime"] = pd.to_datetime(heart_df["datetime"]).dt.tz_localize(None)
    
#     # Convert start_time and end_time to tz-naive
#     start_time_naive = pd.to_datetime(start_time).tz_localize(None)
#     end_time_naive = pd.to_datetime(end_time).tz_localize(None)
    
#     print(f"Playback window: {start_time_naive} to {end_time_naive}")

#     # -----------------------
#     # Trim heart rate data to playback window
#     # -----------------------
#     mask = (heart_df["datetime"] >= start_time_naive) & (heart_df["datetime"] <= end_time_naive)
#     sliced_heart = heart_df.loc[mask].copy()

#     if sliced_heart.empty:
#         raise ValueError("No heart rate data found in playback window.")

#     print(f"Heart data: {len(sliced_heart)} readings in window")

#     # -----------------------
#     # Normalize both series for alignment
#     # -----------------------
#     fear_df = fear_df.sort_values("datetime").reset_index(drop=True)
#     sliced_heart = sliced_heart.sort_values("datetime").reset_index(drop=True)

#     fear_df["relative"] = np.linspace(0, 1, len(fear_df))
#     sliced_heart["relative"] = np.linspace(0, 1, len(sliced_heart))

#     # Identify fear score column
#     fear_score_col = None
#     for col in ['fear_score', 'Fear Mongering Score', 'score', 'Score']:
#         if col in fear_df.columns:
#             fear_score_col = col
#             break
    
#     if fear_score_col is None:
#         raise ValueError(f"Could not find fear score column. Available: {list(fear_df.columns)}")

#     print(f"Using fear score column: '{fear_score_col}'")

#     # -----------------------
#     # Merge on relative position
#     # -----------------------
#     merged = pd.merge_asof(
#         fear_df,
#         sliced_heart[['relative', 'value']],
#         on="relative",
#         direction="nearest"
#     )
    

#     print(f"✓ Successfully merged {len(merged)} data points")
#     print("=" * 50)

#     # -----------------------
#     # Create Plotly chart
#     # -----------------------
#     fig = go.Figure()

#     fig.add_trace(go.Scatter(
#         x=merged["relative"],
#         y=merged[fear_score_col],
#         name="Fear Rating",
#         line=dict(color="blue", width=2),
#         mode='lines+markers',
#         marker=dict(size=6)
#     ))

#     fig.add_trace(go.Scatter(
#         x=merged["relative"],
#         y=merged["value"],
#         name="Heart Rate (bpm)",
#         line=dict(color="red", width=2),
#         mode='lines+markers',
#         marker=dict(size=6),
#         yaxis="y2"
#     ))

#     fig.update_layout(
#         title="Fear Intensity vs Heart Rate (Normalized Timeline)",
#         xaxis=dict(title="Normalized Progress (0 → 1)", showgrid=True),
#         yaxis=dict(title="Fear Score", color="blue", showgrid=True),
#         yaxis2=dict(title="Heart Rate (bpm)", overlaying="y", side="right", color="red"),
#         template="plotly_white",
#         height=500,
#         hovermode='x unified'
#     )

#     return fig, merged

# import pandas as pd
# import numpy as np
# import plotly.graph_objects as go
# import pytz

# def align_fear_and_heart(fear_df, heart_df, start_time, end_time):
#     """
#     Aligns normalized fear ratings and heart rate within a specific window.
#     Handles fractional seconds and timezone-aware comparisons.
#     """
#     # -----------------------
#     # Ensure datetime columns
#     # -----------------------
#     if "Timestamp" in fear_df.columns:
#         fear_df["datetime"] = pd.to_datetime(
#             fear_df["Timestamp"].astype(str),
#             format="%H:%M:%S.%f",
#             errors="coerce"
#         )
#         # fallback if fractional seconds fail
#         if fear_df["datetime"].isna().any():
#             fear_df.loc[fear_df["datetime"].isna(), "datetime"] = pd.to_datetime(
#                 fear_df.loc[fear_df["datetime"].isna(), "Timestamp"].astype(str),
#                 format="%H:%M:%S",
#                 errors="coerce"
#             )
#     # Ensure heart_df["datetime"] is timezone-aware
#     if heart_df["datetime"].dt.tz is None:
#         heart_df["datetime"] = heart_df["datetime"].dt.tz_localize(pytz.timezone("US/Eastern"))
    
#     # DEBUG: Print timezone info
#     print("=" * 50)
#     print("TIMEZONE DEBUG INFO:")
#     print(f"fear_df datetime tz: {fear_df['datetime'].dt.tz}")
#     print(f"heart_df datetime tz: {heart_df['datetime'].dt.tz}")
#     print(f"start_time tzinfo: {start_time.tzinfo}")
#     print(f"end_time tzinfo: {end_time.tzinfo}")
#     print(f"Sample fear_df datetime: {fear_df['datetime'].iloc[0] if len(fear_df) > 0 else 'N/A'}")
#     print(f"Sample heart_df datetime: {heart_df['datetime'].iloc[0] if len(heart_df) > 0 else 'N/A'}")
#     print("=" * 50)
    
#     # -----------------------
#     # Trim to playback window
#     # -----------------------
#     mask = (heart_df["datetime"] >= start_time) & (heart_df["datetime"] <= end_time)
#     sliced_heart = heart_df.loc[mask].copy()
#     if sliced_heart.empty:
#         raise ValueError("No heart rate data available in that window.")
#     # -----------------------
#     # Normalize both series
#     # -----------------------
#     sliced_heart["relative"] = np.linspace(0, 1, len(sliced_heart))
#     fear_df = fear_df.sort_values("datetime")
#     fear_df["relative"] = np.linspace(0, 1, len(fear_df))
#     merged = pd.merge_asof(
#         fear_df.sort_values("relative"),
#         sliced_heart.sort_values("relative"),
#         on="relative",
#         direction="nearest"
#     )
#     # -----------------------
#     # Create Plotly chart
#     # -----------------------
#     fig = go.Figure()
#     fig.add_trace(go.Scatter(
#         x=merged["relative"], y=merged["fear_score"],
#         name="Fear Rating", line=dict(color="blue")
#     ))
#     fig.add_trace(go.Scatter(
#         x=merged["relative"], y=merged["value"],
#         name="Heart Rate (bpm)", line=dict(color="red"), yaxis="y2"
#     ))
#     fig.update_layout(
#         title="Fear Intensity vs Heart Rate (Normalized Timeline)",
#         xaxis=dict(title="Normalized Progress (0 → 1)"),
#         yaxis=dict(title="Fear Score", color="blue"),
#         yaxis2=dict(title="Heart Rate (bpm)", overlaying="y", side="right", color="red"),
#         template="plotly_white", height=500
#     )
#     return fig, merged

import pandas as pd
import numpy as np
import plotly.graph_objects as go
import pytz
from datetime import timedelta

def time_to_seconds(time_str):
    """Convert time string (HH:MM:SS or MM:SS or H:MM:SS) to seconds."""
    try:
        time_str = str(time_str).strip()
        parts = time_str.split(':')
        if len(parts) == 3:
            h, m, s = parts
            return int(h) * 3600 + int(m) * 60 + float(s)
        elif len(parts) == 2:
            m, s = parts
            return int(m) * 60 + float(s)
        else:
            return float(time_str)
    except:
        return None

def align_fear_and_heart(fear_df, heart_df, start_time, end_time):
    """
    Aligns normalized fear ratings and heart rate within a specific window.
    Handles fractional seconds and timezone-aware comparisons.
    """
    
    print("=" * 50)
    print("Starting alignment...")
    
    fear_df = fear_df.copy()
    heart_df = heart_df.copy()
    
    # -----------------------
    # Handle fear DataFrame datetime conversion
    # -----------------------
    if "Timestamp" in fear_df.columns:
        # Convert Timestamp column (format like "0:00:00") to seconds
        fear_df['seconds_numeric'] = fear_df["Timestamp"].apply(time_to_seconds)
        
        # Scale fear timestamps to match the playback window
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
    
    sliced_heart["relative"] = np.linspace(0, 1, len(sliced_heart))
    fear_df["relative"] = np.linspace(0, 1, len(fear_df))
    
    # Find fear score column
    fear_score_col = None
    for col in ['fear_score', 'Fear Mongering Score', 'score', 'Score']:
        if col in fear_df.columns:
            fear_score_col = col
            break
    
    if fear_score_col is None:
        raise ValueError(f"Could not find fear score column. Available: {list(fear_df.columns)}")
    
    print(f"Using fear score column: '{fear_score_col}'")
    
    # Merge on relative position
    merged = pd.merge_asof(
        fear_df.sort_values("relative"),
        sliced_heart[['relative', 'value']].sort_values("relative"),
        on="relative",
        direction="nearest"
    )
    
    print(f"✓ Merged {len(merged)} data points")
    print("=" * 50)
    
    # -----------------------
    # Create Plotly chart
    # -----------------------
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=merged["relative"],
        y=merged[fear_score_col],
        name="Fear Rating",
        line=dict(color="blue", width=2),
        mode='lines+markers',
        marker=dict(size=6)
    ))
    
    fig.add_trace(go.Scatter(
        x=merged["relative"],
        y=merged["value"],
        name="Heart Rate (bpm)",
        line=dict(color="red", width=2),
        mode='lines+markers',
        marker=dict(size=6),
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