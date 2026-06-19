# video-notes

**English** · [繁體中文](README.zh-TW.md) · [日本語](README.ja.md)

A [Claude Code](https://claude.com/claude-code) skill that turns a **YouTube URL
or a local video file** into two Markdown files: a key-points note and a full
timestamped transcript.

The Python pipeline only fetches the transcript. The summary, key points, and
chapter breakdown are written by the agent reading the transcript — so the notes
read like a human took them, not like a second API call stitched them together.

## Why this one

- **Zero pip dependencies.** Seven small stdlib-only Python scripts. The only
  requirements are system tools you probably already have: `yt-dlp`, `ffmpeg`,
  `curl`.
- **Clean YouTube auto-caption de-duplication.** YouTube's rolling two-line
  auto-captions repeat almost every word. This reconstructs the transcript so it
  reads through once, with no duplicated lines — handling both the "growth" and
  "sliding-window" overlap formats.
- **Picks the original-language track, not a machine translation.** YouTube lists
  ~150 auto-translated caption tracks for any auto-captioned video. This
  deliberately takes the original-language ASR (manual subs → original manual →
  original auto) and leaves translation to the summarizing step, where fidelity
  is higher.
- **Whisper fallback when there are no subtitles.** Extracts low-bitrate mono
  audio, splits it into chunks under the API's 25 MB limit, transcribes each via
  `curl`, and merges the segment timestamps back together.

## Requirements

```bash
brew install yt-dlp ffmpeg   # macOS; use your platform's package manager otherwise
```

Python 3.9+ (standard library only — no `pip install` needed).

`OPENAI_API_KEY` is **optional** — it is read only when a video has no usable
subtitles and the Whisper fallback runs.

## Install (as a Claude Code skill)

Clone into your skills directory:

```bash
git clone https://github.com/iamvista/video-notes ~/.claude/skills/video-notes
```

Then invoke it in Claude Code:

```
/video-notes https://youtu.be/<id>
/video-notes ./talk.mp4 --out-dir ./notes --lang en
```

## Use the CLI directly (without the agent)

The pipeline is a standalone CLI. It emits `transcript.json`; you format the
notes however you like.

```bash
python3 scripts/cli.py "https://youtu.be/<id>" --lang en --out ./out
cat ./out/transcript.json
```

`transcript.json` schema:

```json
{
  "meta": {"type": "youtube", "title": "...", "source": "...", "channel": "...", "duration": "MM:SS", "video_id": "..."},
  "transcript_source": "subtitles",
  "segments": [{"start": 8.16, "text": "..."}]
}
```

## How it works

```
source.py     classify the argument: YouTube URL vs local file
meta.py       fetch title / channel / duration (yt-dlp -J or ffprobe)
subtitles.py  fetch + de-duplicate the best subtitle track  (preferred path)
audio.py      extract mono mp3 and chunk it under 25 MB      (fallback)
whisper.py    transcribe each chunk via the Whisper API      (fallback)
cli.py        orchestrate: subtitles first, Whisper if none
transcript.py timestamp + deep-link formatting helpers
```

`SKILL.md` holds the agent-facing instructions for turning `transcript.json`
into the two Markdown files.

## Customizing the output destination

`--out-dir` is the seam for personal workflows. Point it at a notes vault and
extend the frontmatter in `SKILL.md` Step 5 to match your own conventions — the
transcript pipeline stays generic.

## Tests

```bash
python3 -m pytest tests/
```

Pure-stdlib unit tests cover source detection, audio chunk planning, the VTT
parser and its de-duplication, the Whisper offset merge, and the timestamp
helpers. No network access required.

## License

MIT — see [LICENSE](LICENSE).
