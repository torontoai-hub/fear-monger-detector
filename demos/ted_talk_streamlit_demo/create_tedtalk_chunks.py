import pandas as pd

df = pd.read_csv("data/ted_talks_transcripts.csv")

def split_text_into_chunks(text, max_chunk_size=500):
    if not isinstance(text, str):
        return []
    text = text.strip()
    return [text[i:i+max_chunk_size] for i in range(0, len(text), max_chunk_size)]

records = []
for idx, row in df.iterrows():
    chunks = split_text_into_chunks(row['transcript'], max_chunk_size=500)
    for i, chunk_text in enumerate(chunks):
        records.append({
            "transcript_chunk": f"chunk{i+1}",  # simple chunk ID without URL
            "text_response": chunk_text,
        })

df_chunks = pd.DataFrame(records)

# Save to CSV without the url info in your chunk IDs
df_chunks.to_csv("ted_talks_transcript_chunks.csv", index=False)

print("CSV saved without url in chunk IDs.")
print(df_chunks.head())
