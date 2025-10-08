import pytz
from datetime import datetime, timedelta


def estimate_playback_window(video_duration, buffer_minutes=5, test_time_str=None):
    """Estimate start/end times for playback window."""
    now = datetime.datetime.now(pytz.timezone("US/Eastern"))

    if test_time_str:
        test_time = datetime.datetime.strptime(test_time_str, "%H:%M")
        now = now.replace(hour=test_time.hour, minute=test_time.minute, second=0, microsecond=0)

    start_dt = now - datetime.timedelta(minutes=buffer_minutes)
    end_dt = start_dt + datetime.timedelta(seconds=video_duration)

    return start_dt, end_dt

