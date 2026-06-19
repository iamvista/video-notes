---
name: video-notes
description: Use when the user gives a YouTube link or a local video file and wants an automatic transcript plus key-points notes. Triggers on /video-notes, "transcribe this video", "影片重點", "整理逐字稿", "影片逐字稿".
---

# Video Notes

Turn a YouTube URL or local video file into two Markdown files: a key-points
note and a full timestamped transcript.

Usage: `/video-notes <url-or-local-path> [--out-dir <dir>] [--lang <code>]`

Pipeline: a stdlib-only Python CLI fetches the transcript (YouTube subtitles
first, Whisper API fallback) and emits `transcript.json`. You then read that JSON
and author the two Markdown files yourself — the summary, key points, and
chapters are your work, not a separate API call.

## Step 1: Parse the arguments

From the user input extract:
- `source` — the YouTube URL or local file path (required)
- `--out-dir` — destination folder for the two Markdown files. If omitted,
  default to `./video-notes/` in the current working directory.
- `--lang` — transcription language hint passed to Whisper (default `en`). Has
  no effect when subtitles are used; only matters for the Whisper fallback.

## Step 2: Check dependencies

Run `which yt-dlp ffmpeg ffprobe curl`. If any is missing, tell the user the
install command (`brew install yt-dlp ffmpeg`, or your platform's equivalent)
and stop. Do NOT check `OPENAI_API_KEY` yet — it is only needed if the video has
no subtitles.

## Step 3: Run the transcript pipeline

```bash
SKILL_DIR=<path-to-this-skill>
OUT=$(mktemp -d)
python3 "$SKILL_DIR/scripts/cli.py" "<source>" --lang <lang> --out "$OUT"
```

Notes:
- The scripts are stdlib-only — any Python 3.9+ works. If you prefer an isolated
  interpreter, create a venv once (`python3 -m venv .venv`) and use its python;
  no `pip install` is needed.
- On success the command prints the path to `$OUT/transcript.json`.
- The CLI surfaces clean errors (exit code ≠ 0):
  - "Not a recognized YouTube URL or existing local file" → bad source argument.
  - "OPENAI_API_KEY is not set" → the video had no subtitles and Whisper is
    needed; tell the user to export `OPENAI_API_KEY` and re-run.
  - A `yt-dlp` failure on a private/members-only video → report it and note that
    `--cookies-from-browser <browser>` may be needed.

## Step 4: Read the transcript

Read `$OUT/transcript.json`. Schema:
```json
{
  "meta": {"type","title","source","channel","duration","video_id"},
  "transcript_source": "subtitles" | "whisper",
  "segments": [{"start": 8.16, "text": "…"}]
}
```
`start` is in seconds.

## Step 5: Author the two output files

Write both files into the `--out-dir` (default `./video-notes/`). Build the slug
`YYYY-MM-DD-<safe-title>` — lower-case, kebab-case, ASCII-safe. For YouTube
sources prefer the video's ORIGINAL upload date (yt-dlp `upload_date`); otherwise
use today's date.

### `<slug>-notes.md`
Frontmatter:
```yaml
---
title: <meta.title>
source: <meta.source>
channel: <meta.channel>
duration: <meta.duration>
date: <YYYY-MM-DD>
tags: [video-notes]
---
```

Body:
- `## TL;DR` — a 3-5 sentence summary you write from the transcript.
- `## Key Points` — key points grouped by theme (bullet list).
- `## Chapters` — chapters as `- [MM:SS] topic`. Derive chapter boundaries by
  reading the transcript and grouping segments by topic shift; use the `start` of
  the first segment in each group, formatted MM:SS (or H:MM:SS past an hour). For
  YouTube sources, make each timestamp a link:
  `[MM:SS](<meta.source>&t=<start>s)`.

Write the note in the same language as the video (or whatever language the user
asks for). For consistent formatting you may reuse the shipped helpers in
`scripts/transcript.py`: `fmt_timestamp(seconds)` returns "MM:SS"/"H:MM:SS" and
`youtube_link(url, seconds)` builds the `&t=Ns` link (returns None for local
sources). Either call them or format by hand to the same convention.

### `<slug>-transcript.md`
Frontmatter (`title`, `source`, `type: transcript`), then every segment on its
own line as `[MM:SS] text`.

## Step 6: Report

Print the two absolute output paths and the one-line TL;DR so the user can jump
straight to the files.

## Extending: route notes into your own knowledge base

`--out-dir` is the seam for personal workflows. Point it at, say, an Obsidian
vault's inbox and add your own frontmatter convention (extra `entities:`,
`source_url`, `compiled: false`, etc.) in Step 5. The pipeline stays generic;
the destination and the note schema are yours to customize.
