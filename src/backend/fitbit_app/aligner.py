import pandas as pd
import numpy as np
import plotly.graph_objects as go
import pytz


def align_fear_and_heart(fear_df, heart_df, start_time, end_time):
    """
    Aligns normalized fear ratings and heart rate within a specific window.

    Handles fractional seconds and timezone-aware comparisons.
    """

    # -----------------------
    # Ensure datetime columns
    # -----------------------

    if "Timestamp" in fear_df.columns:
        fear_df["datetime"] = pd.to_datetime(
            fear_df["Timestamp"].astype(str),
            format="%H:%M:%S.%f",
            errors="coerce"
        )
        # fallback if fractional seconds fail
        if fear_df["datetime"].isna().any():
            fear_df.loc[fear_df["datetime"].isna(), "datetime"] = pd.to_datetime(
                fear_df.loc[fear_df["datetime"].isna(), "Timestamp"].astype(str),
                format="%H:%M:%S",
                errors="coerce"
            )

    # Ensure heart_df["datetime"] is timezone-aware
    if heart_df["datetime"].dt.tz is None:
        heart_df["datetime"] = heart_df["datetime"].dt.tz_localize(pytz.timezone("US/Eastern"))

    # -----------------------
    # Trim to playback window
    # -----------------------
    mask = (heart_df["datetime"] >= start_time) & (heart_df["datetime"] <= end_time)
    sliced_heart = heart_df.loc[mask].copy()

    if sliced_heart.empty:
        raise ValueError("No heart rate data available in that window.")

    # -----------------------
    # Normalize both series
    # -----------------------
    sliced_heart["relative"] = np.linspace(0, 1, len(sliced_heart))
    fear_df = fear_df.sort_values("datetime")
    fear_df["relative"] = np.linspace(0, 1, len(fear_df))

    merged = pd.merge_asof(
        fear_df.sort_values("relative"),
        sliced_heart.sort_values("relative"),
        on="relative",
        direction="nearest"
    )

    # -----------------------
    # Create Plotly chart
    # -----------------------
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=merged["relative"], y=merged["fear_score"],
        name="Fear Rating", line=dict(color="blue")
    ))
    fig.add_trace(go.Scatter(
        x=merged["relative"], y=merged["value"],
        name="Heart Rate (bpm)", line=dict(color="red"), yaxis="y2"
    ))
    fig.update_layout(
        title="Fear Intensity vs Heart Rate (Normalized Timeline)",
        xaxis=dict(title="Normalized Progress (0 → 1)"),
        yaxis=dict(title="Fear Score", color="blue"),
        yaxis2=dict(title="Heart Rate (bpm)", overlaying="y", side="right", color="red"),
        template="plotly_white", height=500
    )

    return fig, merged
