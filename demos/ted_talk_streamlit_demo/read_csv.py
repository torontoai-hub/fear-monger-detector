import pandas as pd

import pandas as pd

# Load both datasets
df_transcripts = pd.read_csv("data/ted_talks_transcripts.csv")  # your first dataset
df_metadata = pd.read_csv("data/ted_main.csv")  # your second dataset

# Merge on 'url'
df = pd.merge(df_transcripts, df_metadata, on="url", how="left")

print(df.columns)
