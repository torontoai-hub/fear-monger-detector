from youtube_transcript_api import YouTubeTranscriptApi
from urllib.parse import urlparse, parse_qs
import streamlit as st
import time

def get_video_id(url_or_id):
    if len(url_or_id) == 11:
        return url_or_id
    try:
        parsed = urlparse(url_or_id)
        if parsed.hostname in ["www.youtube.com", "youtube.com"]:
            return parse_qs(parsed.query)["v"][0]
        elif parsed.hostname == "youtu.be":
            return parsed.path[1:]
    except Exception:
        pass
    return None

# def fetch_transcript(video_id):
#     try:
#         ytt_api = YouTubeTranscriptApi()
#         transcript_list = ytt_api.list(video_id)
#         try:
#             transcript = transcript_list.find_manually_created_transcript(["en-US", "en"])
#         except Exception:
#             transcript = transcript_list.find_generated_transcript(["en"])
#         return " ".join([snippet.text for snippet in transcript.fetch()])
#     except Exception as e:
#         st.error(f"Error fetching transcript: {e}")
#         return None



@st.cache_data
def fetch_transcript(video_id):
    """
    Fetch transcript text from a YouTube video ID with progress updates
    in the same style as run_inference().
    """
    progress = st.progress(0)

    try:
        progress.progress(10)  # Step 1: Starting
        time.sleep(0.1)

        ytt_api = YouTubeTranscriptApi()
        progress.progress(30)  # Step 2: Listing transcripts
        time.sleep(0.1)

        transcript_list = ytt_api.list(video_id)
        progress.progress(50)  # Step 3: Selecting transcript
        time.sleep(0.1)

        try:
            transcript = transcript_list.find_manually_created_transcript(["en-US", "en"])
        except Exception:
            transcript = transcript_list.find_generated_transcript(["en"])
        progress.progress(80)  # Step 4: Fetching transcript
        time.sleep(0.1)

        transcript_text = " ".join([snippet.text for snippet in transcript.fetch()])
        progress.progress(100)  # Step 5: Done
        time.sleep(0.1)

        progress.empty()
        return transcript_text

    except Exception as e:
        progress.empty()
        st.error(f"Error fetching transcript: {e}")
        return None
