import pandas as pd
from datetime import datetime
import pytz

# -------------------------------
# Utility functions
# -------------------------------
def normalize_datetime(df, column, tz="US/Eastern"):
    """Ensure datetime column is timezone-aware and consistent."""
    df[column] = pd.to_datetime(df[column], errors="coerce")

    if df[column].dt.tz is None:
        df[column] = df[column].dt.tz_localize(tz, ambiguous="NaT", nonexistent="shift_forward")
    else:
        df[column] = df[column].dt.tz_convert(tz)

    return df


def attach_date_to_fear(fear_df, fitbit_df, fear_col="Timestamp", fitbit_col="datetime"):
    """Attach Fitbit date to fear timestamps so they align."""
    # Ensure Fitbit datetime is timezone-aware
    fitbit_df = normalize_datetime(fitbit_df, fitbit_col)

    # Extract date from first Fitbit entry
    fitbit_date = fitbit_df[fitbit_col].dt.date.iloc[0]

    # Convert fear timestamps to time, then combine with Fitbit date
    fear_df[fear_col] = pd.to_datetime(fear_df[fear_col], errors="coerce").dt.time
    fear_df[fear_col] = fear_df[fear_col].apply(
        lambda t: pd.Timestamp.combine(fitbit_date, t)
    )

    # Localize to Fitbit timezone
    fear_df[fear_col] = fear_df[fear_col].dt.tz_localize(fitbit_df[fitbit_col].dt.tz)

    return fear_df



def merge_fear_fitbit(fear_df, fitbit_df, fear_col="Timestamp", fitbit_col="datetime", tolerance="2min"):
    """Merge fear and fitbit DataFrames with nearest timestamp alignment,
    and add time difference column for diagnostics."""

    # Ensure datetime columns are timezone-aware
    fear_df[fear_col] = pd.to_datetime(fear_df[fear_col], errors="coerce")
    fitbit_df[fitbit_col] = pd.to_datetime(fitbit_df[fitbit_col], errors="coerce")

    # Ensure both have same timezone (UTC or specific)
    if fear_df[fear_col].dt.tz is None:
        fear_df[fear_col] = fear_df[fear_col].dt.tz_localize("US/Eastern")
    else:
        fear_df[fear_col] = fear_df[fear_col].dt.tz_convert("US/Eastern")

    if fitbit_df[fitbit_col].dt.tz is None:
        fitbit_df[fitbit_col] = fitbit_df[fitbit_col].dt.tz_localize("US/Eastern")
    else:
        fitbit_df[fitbit_col] = fitbit_df[fitbit_col].dt.tz_convert("US/Eastern")

    fear_df = fear_df.sort_values(fear_col)
    fitbit_df = fitbit_df.sort_values(fitbit_col)

    merged_df = pd.merge_asof(
        fear_df,
        fitbit_df,
        left_on=fear_col,
        right_on=fitbit_col,
        direction="nearest",
        tolerance=pd.Timedelta(tolerance),
        suffixes=("_fear", "_fitbit")
    )

    # Add time difference column
    merged_df["time_diff"] = (merged_df[fear_col] - merged_df[fitbit_col]).abs()

    print(merged_df[["Timestamp", "datetime", "time_diff"]].head(10))

    return merged_df