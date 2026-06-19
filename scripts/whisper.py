# scripts/whisper.py
import json
import os
import subprocess

API_URL = "https://api.openai.com/v1/audio/transcriptions"


def parse_verbose_json(payload):
    """Extract [{'start': float, 'text': str}] from Whisper verbose_json."""
    return [{"start": float(s["start"]), "text": s["text"].strip()}
            for s in payload.get("segments", [])]


def transcribe_chunk(path, lang):
    """Send one audio file to the Whisper API via curl. Returns segments."""
    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        raise RuntimeError("OPENAI_API_KEY is not set (required for Whisper fallback)")
    cmd = [
        "curl", "-sS", "--fail-with-body", API_URL,
        "-H", f"Authorization: Bearer {key}",
        "-F", f"file=@{path}",
        "-F", "model=whisper-1",
        "-F", "response_format=verbose_json",
    ]
    if lang:
        cmd += ["-F", f"language={lang}"]
    out = subprocess.run(cmd, capture_output=True, text=True, check=True).stdout
    return parse_verbose_json(json.loads(out))


def transcribe(chunks, lang):
    """Transcribe ordered chunks, shifting each chunk's segment starts by its
    offset, and concatenate. `chunks` is [{'path','start'}]."""
    segments = []
    for ch in chunks:
        for seg in transcribe_chunk(ch["path"], lang):
            segments.append({"start": seg["start"] + ch["start"],
                             "text": seg["text"]})
    return segments
