import pandas as pd

# Load both datasets
df_transcripts = pd.read_csv("ted_talks_transcripts.csv")  # your first dataset
df_metadata = pd.read_csv("ted_main.csv")  # your second dataset

# Merge on 'url'
df = pd.merge(df_transcripts, df_metadata, on="url", how="left")

df["duration"] = pd.to_numeric(df["duration"], errors="coerce")

# Find min and max
min_duration = df["duration"].min()
max_duration = df["duration"].max()

print(f"Minimum duration: {min_duration} seconds")
print(f"Maximum duration: {max_duration} seconds")

# Find row with min duration
min_row = df.loc[df["duration"] == df["duration"].min()]

print("URL of min duration talk:", min_row["url"].values[0])


print(df.columns)
print(df.head())
