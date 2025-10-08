import pandas as pd
import pytz
from datetime import datetime
import plotly.express as px
from backend.fitbit_app.fitbit_client import fetch_fitbit_data
from .config import FITBIT_HEART_ENDPOINT, DATE_FORMAT

def get_fitbit_heart_data(date_str):
    """
    Fetch Fitbit heart rate data for a given date.
    Returns: (DataFrame, normalized_date_str, error_message)
    """
    try:
        # Normalize date format to YYYY-MM-DD
        date = pd.to_datetime(date_str)
        normalized_date = date.strftime(DATE_FORMAT)

        endpoint = FITBIT_HEART_ENDPOINT.format(date=normalized_date)
        data = fetch_fitbit_data(endpoint)

        intraday = data.get("activities-heart-intraday", {}).get("dataset", [])
        if not intraday:
            return None, normalized_date, "No intraday heart data found for that date."

        df = pd.DataFrame(intraday)
        if "time" not in df.columns:
            return None, normalized_date, "Fitbit data missing 'time' field."

        df["datetime"] = pd.to_datetime(normalized_date + " " + df["time"])
        df["datetime"] = df["datetime"].dt.tz_localize(pytz.timezone("US/Eastern"))

        return df, normalized_date, None

    except Exception as e:
        return None, date_str, f"Error fetching Fitbit data: {str(e)}"
    

def plot_fitbit_heart(df, date_str):
    fig = px.line(
        df, x="datetime", y="value",
        title=f"Intraday Heart Rate - {date_str}",
        labels={"datetime": "Time", "value": "Heart Rate (bpm)"}
    )
    fig.update_traces(line=dict(color="red"))
    return fig
