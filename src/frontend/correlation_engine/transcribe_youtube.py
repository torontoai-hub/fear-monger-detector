from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound

def get_transcript(video_id: str, preferred_languages=['en-US', 'en']) -> str:
    """
    Fetches the transcript for a given YouTube video ID.
    Prefers manually created transcripts over generated ones.
    
    Args:
        video_id (str): YouTube video ID
        preferred_languages (list): Language codes to prefer
    
    Returns:
        str: Combined transcript text
    
    Raises:
        Exception: If no transcript can be found
    """
    ytt_api = YouTubeTranscriptApi()

    try:
        transcript_list = ytt_api.list(video_id)

        # Try manual transcripts first
        transcript = None
        for lang in preferred_languages:
            try:
                transcript = transcript_list.find_manually_created_transcript([lang])
                break
            except NoTranscriptFound:
                continue

        # If no manual transcript, try generated
        if transcript is None:
            for lang in preferred_languages:
                try:
                    transcript = transcript_list.find_generated_transcript([lang])
                    break
                except NoTranscriptFound:
                    continue

        if transcript is None:
            raise NoTranscriptFound(video_id, preferred_languages, transcript_list)

        # Fetch transcript segments
        transcript_segments = transcript.fetch()
        full_text = " ".join(segment.text for segment in transcript_segments)
        return full_text

    except TranscriptsDisabled:
        raise Exception(f"Transcripts are disabled for video {video_id}")
    except NoTranscriptFound:
        raise Exception(f"No transcript found for video {video_id} with languages {preferred_languages}")
