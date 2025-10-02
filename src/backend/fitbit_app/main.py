from fitbit_client import fetch_fitbit_data  # Assuming this uses the auth token internally
import pandas as pd
import pytz
from datetime import datetime

if __name__ == "__main__":
    try:
        today = datetime.today().strftime("%Y-%m-%d")

        # Request intraday heart data at 1-minute resolution
        endpoint = f"/1/user/-/activities/heart/date/{today}/1d/1min.json"
        data = fetch_fitbit_data(endpoint)  # fetch_fitbit_data uses pre-authenticated session

        # Extract intraday dataset
        intraday = data.get("activities-heart-intraday", {}).get("dataset", [])
        if not intraday:
            print("No intraday heart data found.")
        else:
            df = pd.DataFrame(intraday)

            # Combine date + time into naive datetime (no timezone set yet)
            df["datetime"] = pd.to_datetime(today + " " + df["time"])

            # Localize naive datetime to Fitbit user's local timezone (e.g., 'US/Eastern')
            eastern = pytz.timezone("US/Eastern")
            df["datetime"] = df["datetime"].dt.tz_localize(
                eastern, ambiguous='NaT', nonexistent='shift_forward'
            )

            # Print last 5 rows
            print(df.head())

            print("\n --------------------- \n")

            # Print last 5 rows
            print(df.tail())

            # Print current local time
            now = datetime.now(eastern)
            print("Current time in US/Eastern:", now.strftime('%Y-%m-%d %I:%M:%S %p %Z'))

            # Save to CSV
            output_file = f"fitbit_heart_{today}.csv"
            df.to_csv(output_file, index=False)
            print(f"Saved intraday heart data to {output_file}")

    except Exception as e:
        print("Error:", e)
