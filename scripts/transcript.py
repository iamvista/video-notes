# scripts/transcript.py

def fmt_timestamp(seconds):
    """Format seconds as MM:SS, or H:MM:SS when >= 1 hour."""
    s = int(seconds)
    h, rem = divmod(s, 3600)
    m, sec = divmod(rem, 60)
    if h:
        return f"{h}:{m:02d}:{sec:02d}"
    return f"{m:02d}:{sec:02d}"


def youtube_link(url, seconds):
    """Return a YouTube deep-link with &t=Ns, or None if url is falsy."""
    if not url:
        return None
    return f"{url}&t={int(seconds)}s"
