# scripts/source.py
import os
import re

_YT_PATTERNS = [
    re.compile(r"(?:youtube\.com/watch\?(?:.*&)?v=)([A-Za-z0-9_-]{11})"),
    re.compile(r"(?:youtu\.be/)([A-Za-z0-9_-]{11})"),
    re.compile(r"(?:youtube\.com/shorts/)([A-Za-z0-9_-]{11})"),
]


def detect_source(arg):
    """Classify a CLI argument as a YouTube video or a local file.

    Returns a dict:
      youtube -> {"type": "youtube", "id": <id>, "url": <canonical watch url>}
      local   -> {"type": "local", "path": <absolute path>}
    Raises ValueError if neither.
    """
    for pat in _YT_PATTERNS:
        m = pat.search(arg)
        if m:
            vid = m.group(1)
            return {"type": "youtube", "id": vid,
                    "url": f"https://www.youtube.com/watch?v={vid}"}
    if os.path.isfile(arg):
        return {"type": "local", "path": os.path.abspath(arg)}
    raise ValueError(f"Not a recognized YouTube URL or existing local file: {arg}")
