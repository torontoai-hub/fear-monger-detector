# import sys, os
# sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../backend")))

# from backend.ted_talks_app import segment_text
from transcribe_youtube import get_transcript

video_id = "fkIvmfqX-t0"
try:
    transcript_text = get_transcript(video_id)
    print(transcript_text[:500])  # first 500 characters
except Exception as e:
    print(f"Error fetching transcript: {e}")
