# scripts/cli.py
import argparse
import json
import os
import tempfile

import source as source_mod
import meta as meta_mod
import subtitles as subtitles_mod
import audio as audio_mod
import whisper as whisper_mod


def build_transcript(arg, lang, workdir):
    src = source_mod.detect_source(arg)
    if src["type"] == "youtube":
        meta = meta_mod.youtube_meta(src)
        segments = subtitles_mod.fetch_subtitles(src["url"], workdir)
        if segments:
            return {"meta": meta, "transcript_source": "subtitles",
                    "segments": segments}
    else:
        meta = meta_mod.local_meta(src)

    # Whisper fallback (no subtitles, or local file)
    audio_path = audio_mod.extract_audio(src, workdir)
    chunks = audio_mod.split_audio(audio_path, workdir)
    segments = whisper_mod.transcribe(chunks, lang)
    return {"meta": meta, "transcript_source": "whisper", "segments": segments}


def main(argv=None):
    p = argparse.ArgumentParser(prog="video-notes")
    p.add_argument("source", help="YouTube URL or local video path")
    p.add_argument("--lang", default="zh", help="transcription language hint")
    p.add_argument("--out", required=True, help="output dir for transcript.json")
    args = p.parse_args(argv)

    os.makedirs(args.out, exist_ok=True)
    try:
        with tempfile.TemporaryDirectory() as workdir:
            result = build_transcript(args.source, args.lang, workdir)
    except (ValueError, RuntimeError) as e:
        p.error(str(e))
    out_path = os.path.join(args.out, "transcript.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(out_path)


if __name__ == "__main__":
    main()
