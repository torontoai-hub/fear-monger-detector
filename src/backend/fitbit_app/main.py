import sys
from backend.fitbit_app.fitbit_utils import get_fitbit_heart_data, plot_fitbit_heart
from datetime import datetime

if __name__ == "__main__":
    try:
        if len(sys.argv) > 1:
            date_str = sys.argv[1]
        else:
            date_str = datetime.today().strftime("%Y-%m-%d")

        df, date_str, error = get_fitbit_heart_data(date_str)
        if error:
            print(error)
            exit()

        # print(df.head())

        # print("\n --------------------- \n")

        # Save CSV
        df.to_csv(f"fitbit_heart_{date_str}.csv", index=False)
        print(f"Saved CSV: fitbit_heart_{date_str}.csv")

        # Plot and save HTML chart
        fig = plot_fitbit_heart(df, date_str)
        fig.write_html(f"fitbit_heart_{date_str}.html")
        print(f"Saved HTML chart: fitbit_heart_{date_str}.html")

    except Exception as e:
        print("Error:", e)

        # Example usage
    # python fitbit_client.py 
    # python fitbit_auth.py 
    # python main.py 2025-10-02
