import sys
import pandas as pd
import pytz
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta
from fitbit_client import fetch_fitbit_data 
import plotly.express as px

if __name__ == "__main__":
    try:
        # today = datetime.today().strftime("%Y-%m-%d")

        # # Request intraday heart data at 1-minute resolution
        # endpoint = f"/1/user/-/activities/heart/date/{today}/1d/1min.json"

        if len(sys.argv) > 1:
            date_str = sys.argv[1]   # e.g. "2025-10-01"
        else:
            date_str = datetime.today().strftime("%Y-%m-%d")

        endpoint = f"/1/user/-/activities/heart/date/{date_str}/1d/1min.json"

        data = fetch_fitbit_data(endpoint)  # fetch_fitbit_data uses pre-authenticated session

        # Extract intraday dataset
        intraday = data.get("activities-heart-intraday", {}).get("dataset", [])
        if not intraday:
            print("No intraday heart data found.")
        else:
            df = pd.DataFrame(intraday)

            # Combine date + time into naive datetime (no timezone set yet)
            df["datetime"] = pd.to_datetime(date_str + " " + df["time"])

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
            output_file = f"fitbit_heart_{date_str}.csv"
            df.to_csv(output_file, index=False)
            print(f"Saved intraday heart data to {output_file}")


            # Matplotlib static plot
            plt.figure(figsize=(12, 6))
            plt.plot(df["datetime"], df["value"], label="Heart Rate (bpm)", color="red")

            # Format x-axis
            plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
            plt.gca().xaxis.set_major_locator(mdates.HourLocator(interval=1))

            # Labels and title
            plt.xlabel("Time (HH:MM)")
            plt.ylabel("Heart Rate (bpm)")
            plt.title(f"Intraday Heart Rate - {date_str}")
            plt.legend()
            plt.grid(True)
            plt.xticks(rotation=45)
            plt.tight_layout()

            # Save as PNG
            output_img = f"fitbit_heart_{date_str}.png"
            plt.savefig(output_img, dpi=300)  # high resolution
            print(f"Saved chart as {output_img}")

            # plt.show()

            

            fig = px.line(
                df,
                x="datetime",
                y="value",
                title=f"Intraday Heart Rate - {date_str}",
                labels={"datetime": "Time", "value": "Heart Rate (bpm)"},
            )

            fig.update_traces(line=dict(color="red"))

            # Save interactive HTML file
            output_html = f"fitbit_heart_{date_str}.html"
            fig.write_html(output_html)
            print(f"Saved interactive chart as {output_html}")

            # Show in browser
            # fig.show()


    except Exception as e:
        print("Error:", e)
