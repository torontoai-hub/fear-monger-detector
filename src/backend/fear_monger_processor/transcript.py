from youtube_transcript_api import YouTubeTranscriptApi
from urllib.parse import urlparse, parse_qs
import streamlit as st

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

def fetch_transcript(video_id):
    try:
        ytt_api = YouTubeTranscriptApi()
        transcript_list = ytt_api.list(video_id)
        try:
            transcript = transcript_list.find_manually_created_transcript(["en-US", "en"])
        except Exception:
            transcript = transcript_list.find_generated_transcript(["en"])
        return " ".join([snippet.text for snippet in transcript.fetch()])
    except Exception as e:
        st.error(f"Error fetching transcript: {e}")
        return None
