import sys
from backend.fitbit_app.fitbit_utils import get_fitbit_heart_data, plot_fitbit_heart
from datetime import datetime

if __name__ == "__main__":
    try:
        # Step 1: Determine which date to fetch heart rate data for
        # If a date is passed as a command-line argument (e.g., python main.py 2025-10-02),
        # use it. Otherwise, default to today's date.
        if len(sys.argv) > 1:
            date_str = sys.argv[1]
        else:
            date_str = datetime.today().strftime("%Y-%m-%d")

        # Step 2: Fetch Fitbit heart rate data for the given date
        # Returns a DataFrame (df), normalized date string, and an error message if any.
        df, date_str, error = get_fitbit_heart_data(date_str)

        # Step 3: If an error occurred (e.g., token failure, no data found), print and exit.
        if error:
            print(error)
            exit()

        # Step 4: Save the heart rate data as a CSV file for further analysis or backup
        df.to_csv(f"fitbit_heart_{date_str}.csv", index=False)
        print(f"Saved CSV: fitbit_heart_{date_str}.csv")

        # Step 5: Plot and save an interactive HTML chart of heart rate over time
        # This allows you to view the heart rate trends visually in a web browser.
        fig = plot_fitbit_heart(df, date_str)
        fig.write_html(f"fitbit_heart_{date_str}.html")
        print(f"Saved HTML chart: fitbit_heart_{date_str}.html")

    except Exception as e:
        # Step 6: Catch and display any unexpected errors (e.g., network, parsing)
        print("Error:", e)

#   Example usage:
#   python fitbit_client.py   → manually refresh or test client authentication
#   python fitbit_auth.py     → manually authenticate and create initial token file
#   python main.py 2025-10-02 → fetch and plot heart rate data for October 2, 2025
