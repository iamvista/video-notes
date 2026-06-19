# scripts/audio.py
import math
import os
import subprocess

MAX_BYTES = 24_000_000  # stay under Whisper's 25MB hard limit


def plan_chunks(file_bytes, duration_s, max_bytes=MAX_BYTES):
    """Compute even time-based chunks so each stays under max_bytes.

    Returns [{"index": int, "start": float_seconds, "length": float_seconds}].
    Splitting by time assumes a roughly constant bitrate (true for the
    low-bitrate mono audio we extract).
    """
    n = max(1, math.ceil(file_bytes / max_bytes))
    seg = duration_s / n
    return [{"index": i, "start": round(i * seg, 6), "length": round(seg, 6)}
            for i in range(n)]


def extract_audio(source, workdir):
    """Extract low-bitrate mono mp3 from a youtube/local source.

    `source` is the dict from source.detect_source. Returns the audio path.
    """
    out = os.path.join(workdir, "audio.mp3")
    if source["type"] == "youtube":
        subprocess.run(
            ["yt-dlp", "-x", "--audio-format", "mp3",
             "--postprocessor-args", "-ar 16000 -ac 1 -b:a 64k",
             "--no-warnings", "-o", os.path.join(workdir, "audio.%(ext)s"),
             source["url"]],
            check=True, capture_output=True, text=True,
        )
    else:
        subprocess.run(
            ["ffmpeg", "-y", "-i", source["path"],
             "-vn", "-ar", "16000", "-ac", "1", "-b:a", "64k", out],
            check=True, capture_output=True, text=True,
        )
    return out


def split_audio(audio_path, workdir, max_bytes=MAX_BYTES):
    """Split audio into chunk files per plan_chunks. Returns
    [{"path": str, "start": float}] in order. Single chunk -> original path."""
    file_bytes = os.path.getsize(audio_path)
    duration_s = _probe_duration(audio_path)
    plan = plan_chunks(file_bytes, duration_s, max_bytes)
    if len(plan) == 1:
        return [{"path": audio_path, "start": 0.0}]
    result = []
    for c in plan:
        cpath = os.path.join(workdir, f"chunk_{c['index']:03d}.mp3")
        subprocess.run(
            ["ffmpeg", "-y", "-i", audio_path,
             "-ss", str(c["start"]), "-t", str(c["length"]),
             "-c", "copy", cpath],
            check=True, capture_output=True, text=True,
        )
        result.append({"path": cpath, "start": c["start"]})
    return result


def _probe_duration(path):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", path],
        capture_output=True, text=True, check=True,
    ).stdout.strip()
    return float(out)
