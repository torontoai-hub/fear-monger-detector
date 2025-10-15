"""
fitbit_utils.py

Utility functions for interacting with the Fitbit API and preparing
heart rate data for analysis and visualization.
"""

import pandas as pd
import pytz
from datetime import datetime
import plotly.express as px
from backend.fitbit_app.fitbit_client import fetch_fitbit_data
from .config import FITBIT_HEART_ENDPOINT, DATE_FORMAT

def get_fitbit_heart_data(date_str):
    """
    Fetch Fitbit heart rate data for a given date.

    Parameters
    ----------
    date_str : str
        Date string in 'YYYY-MM-DD' format or any format recognizable by pandas.

    Returns
    -------
    tuple
        (df, normalized_date, error_message)
        - df: pandas.DataFrame containing heart rate data (time, value, datetime)
        - normalized_date: standardized date string in DATE_FORMAT
        - error_message: None if successful, otherwise a string describing the error

    Workflow
    --------
    1. Normalize the input date string.
    2. Build the Fitbit API endpoint for the heart rate intraday data.
    3. Fetch data using fetch_fitbit_data() which handles OAuth2 authentication.
    4. Extract and validate the intraday dataset.
    5. Construct a timezone-aware datetime column for plotting and analysis.
    """

    try:
        # Step 1: Normalize the date format (to YYYY-MM-DD)
        # Converts input string to pandas datetime, then formats it consistently.        
        date = pd.to_datetime(date_str)
        normalized_date = date.strftime(DATE_FORMAT)

        # Step 2: Build the full Fitbit API endpoint using the normalized date
        endpoint = FITBIT_HEART_ENDPOINT.format(date=normalized_date)

        # Step 3: Fetch data from Fitbit API
        # This call manages token retrieval and refresh automatically.
        data = fetch_fitbit_data(endpoint)

        # Step 4: Extract intraday heart rate data from the API response
        intraday = data.get("activities-heart-intraday", {}).get("dataset", [])

        # If the response does not contain data, return an appropriate error    
        if not intraday:
            return None, normalized_date, "No intraday heart data found for that date."
        
        # Step 5: Convert list of dicts to a DataFrame
        df = pd.DataFrame(intraday)
        if "time" not in df.columns:
            return None, normalized_date, "Fitbit data missing 'time' field."

        # Step 6: Combine date and time into a full datetime column
        df["datetime"] = pd.to_datetime(normalized_date + " " + df["time"])

        # Step 7: Assign timezone (example uses US/Eastern; adjust as needed)
        df["datetime"] = df["datetime"].dt.tz_localize(pytz.timezone("US/Eastern"))

        # Successful result
        return df, normalized_date, None

    except Exception as e:
        # If any step fails (e.g., network error, token error, bad response),
        # return a formatted error message instead of raising        
        return None, date_str, f"Error fetching Fitbit data: {str(e)}"
    

def plot_fitbit_heart(df, date_str):
    fig = px.line(
        df, x="datetime", y="value",
        title=f"Intraday Heart Rate - {date_str}",
        labels={"datetime": "Time", "value": "Heart Rate (bpm)"}
    )
    fig.update_traces(line=dict(color="orange"))
    return fig
