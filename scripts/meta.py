# scripts/meta.py
import json
import os
import subprocess


def _fmt_duration(seconds):
    s = int(seconds)
    h, rem = divmod(s, 3600)
    m, sec = divmod(rem, 60)
    return f"{h}:{m:02d}:{sec:02d}" if h else f"{m:02d}:{sec:02d}"


def youtube_meta(source):
    """Return meta dict for a youtube source via yt-dlp -J."""
    out = subprocess.run(
        ["yt-dlp", "-J", "--no-warnings", source["url"]],
        capture_output=True, text=True, check=True,
    ).stdout
    d = json.loads(out)
    return {
        "type": "youtube",
        "title": d.get("title", source["id"]),
        "source": source["url"],
        "channel": d.get("uploader", ""),
        "duration": _fmt_duration(d.get("duration", 0)),
        "video_id": source["id"],
    }


def local_meta(source):
    """Return meta dict for a local file via ffprobe."""
    path = source["path"]
    dur = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", path],
        capture_output=True, text=True, check=True,
    ).stdout.strip()
    title = os.path.splitext(os.path.basename(path))[0]
    return {
        "type": "local",
        "title": title,
        "source": path,
        "channel": "",
        "duration": _fmt_duration(float(dur)) if dur else "",
        "video_id": "",
    }
