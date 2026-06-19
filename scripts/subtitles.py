# scripts/subtitles.py
import html
import json
import os
import re
import subprocess

LANG_PRIORITY = ["zh-Hant", "zh-Hans", "zh", "en"]

_TS = re.compile(r"(\d+):(\d{2}):(\d{2})[.,](\d{3})\s*-->")
_MERGE_GAP = 5.0  # seconds; rolling-caption cues update within a few seconds


def _ts_to_seconds(h, m, s, ms):
    return int(h) * 3600 + int(m) * 60 + int(s) + int(ms) / 1000.0


def _new_words(pw, tw):
    """Given previous and current cue word-lists, return the words of `tw` that
    are new relative to a rolling-window overlap with `pw`.

    Finds the largest k where the last k words of `pw` equal the first k words of
    `tw` (the YouTube auto-caption sliding window), and returns the remaining tail
    of `tw` joined as a string. Returns "" if `tw` is fully contained in `pw`, or
    None if there is no overlap at all.
    """
    max_k = min(len(pw), len(tw))
    for k in range(max_k, 0, -1):
        if pw[-k:] == tw[:k]:
            return " ".join(tw[k:])
    return None


def parse_vtt(vtt_text):
    """Parse WebVTT text into [{'start': float, 'text': str}].

    De-duplicates YouTube rolling auto-captions two ways:
    - Growth: a later cue that extends the previous one (previous text is a
      prefix of the new text) within _MERGE_GAP seconds replaces the previous
      segment with the longer text.
    - Sliding window: when a cue's leading words repeat the previous cue's
      trailing words (the 2-line rolling format), only the genuinely new tail
      words are emitted, so the transcript reads once through without repeats.
    Inline VTT tags are stripped and HTML entities (e.g. &gt;) are decoded.
    """
    segments = []
    lines = vtt_text.splitlines()
    i = 0
    while i < len(lines):
        m = _TS.match(lines[i].strip())
        if not m:
            i += 1
            continue
        start = _ts_to_seconds(*m.groups())
        i += 1
        text_lines = []
        while i < len(lines) and lines[i].strip() and "-->" not in lines[i]:
            # strip inline VTT tags like <c> and <00:00:00.000>, then decode
            # HTML entities such as &gt;&gt; / &amp; / &#39;
            clean = html.unescape(re.sub(r"<[^>]+>", "", lines[i])).strip()
            if clean:
                text_lines.append(clean)
            i += 1
        text = " ".join(text_lines).strip()
        if not text:
            continue
        if segments:
            prev = segments[-1]
            # Growth: previous text is a prefix of the new text and they are
            # close in time -> keep the longer, single segment.
            if (text.startswith(prev["text"]) and
                    start - prev["start"] <= _MERGE_GAP):
                segments[-1] = {"start": prev["start"], "text": text}
                continue
            # Sliding window: emit only the new tail words after the overlap.
            new = _new_words(prev["text"].split(), text.split())
            if new is not None:
                if new:
                    segments.append({"start": start, "text": new})
                continue
        segments.append({"start": start, "text": text})
    return segments


def pick_lang(available):
    """Choose the best subtitle language code from those available."""
    for lang in LANG_PRIORITY:
        if lang in available:
            return lang
    return None


def _match_lang(available, lang):
    """Find the best key in `available` for a spoken-language code like 'en-US'.

    Tries the exact code, then '<base>-orig' (YouTube's original-ASR key), then
    the bare base ('en'), then any regional variant ('en-GB'). Returns None if
    no match (or if `lang` is falsy).
    """
    if not lang:
        return None
    base = lang.split("-")[0]
    for cand in (lang, f"{base}-orig", base):
        if cand in available:
            return cand
    for a in available:
        if a == base or a.startswith(base + "-"):
            return a
    return None


def _list_available_subs(url):
    """Return (manual_langs, auto_langs, original_lang) via yt-dlp JSON dump."""
    out = subprocess.run(
        ["yt-dlp", "-J", "--no-warnings", url],
        capture_output=True, text=True, check=True,
    ).stdout
    data = json.loads(out)
    return (list((data.get("subtitles") or {}).keys()),
            list((data.get("automatic_captions") or {}).keys()),
            data.get("language"))


def fetch_subtitles(url, workdir):
    """Fetch the best subtitle track for a YouTube URL as normalized segments.

    Selection order:
      1. Manual subtitles in a LANG_PRIORITY language (human captions, best).
      2. Manual subtitles in the video's original spoken language.
      3. Auto-captions in the original spoken language (faithful ASR).
    Auto-translated captions (YouTube lists ~150 of them for any auto-captioned
    video) are intentionally NOT used: an auto-translated track is lower fidelity
    than the original-language transcript, which the caller can translate when
    summarizing.

    Returns segments, None if no usable track exists, or raises RuntimeError if a
    track was found but its download failed (e.g. HTTP 429 rate-limiting).
    """
    manual, auto, orig = _list_available_subs(url)
    lang = pick_lang(manual)
    use_auto = False
    if lang is None:
        lang = _match_lang(manual, orig)
    if lang is None:
        lang = _match_lang(auto, orig)
        use_auto = lang is not None
    if lang is None:
        return None
    flag = "--write-auto-sub" if use_auto else "--write-sub"
    try:
        subprocess.run(
            ["yt-dlp", flag, "--sub-lang", lang, "--sub-format", "vtt",
             "--skip-download", "--no-warnings",
             "-o", os.path.join(workdir, "subs.%(ext)s"), url],
            check=True, capture_output=True, text=True,
        )
    except subprocess.CalledProcessError as e:
        lines = (e.stderr or "").strip().splitlines()
        detail = lines[-1] if lines else f"exit {e.returncode}"
        raise RuntimeError(
            f"Subtitle download failed for '{lang}': {detail}. "
            "YouTube may be rate-limiting (retry shortly), or set OPENAI_API_KEY "
            "to transcribe with Whisper instead."
        )
    for fn in os.listdir(workdir):
        if fn.startswith("subs") and fn.endswith(".vtt"):
            with open(os.path.join(workdir, fn), encoding="utf-8") as fh:
                return parse_vtt(fh.read())
    return None
