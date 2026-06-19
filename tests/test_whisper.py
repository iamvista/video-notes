# tests/test_whisper.py
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import whisper

def test_parse_verbose_json_extracts_segments():
    payload = {"segments": [
        {"start": 0.0, "text": " 你好"},
        {"start": 3.2, "text": " 世界"},
    ]}
    segs = whisper.parse_verbose_json(payload)
    assert segs == [{"start": 0.0, "text": "你好"}, {"start": 3.2, "text": "世界"}]

def test_transcribe_applies_chunk_offset(monkeypatch):
    calls = []
    def fake_transcribe_chunk(path, lang):
        calls.append(path)
        return [{"start": 1.0, "text": "a"}, {"start": 5.0, "text": "b"}]
    monkeypatch.setattr(whisper, "transcribe_chunk", fake_transcribe_chunk)
    chunks = [{"path": "c0.mp3", "start": 0.0}, {"path": "c1.mp3", "start": 300.0}]
    segs = whisper.transcribe(chunks, lang="zh")
    assert [s["start"] for s in segs] == [1.0, 5.0, 301.0, 305.0]
    assert calls == ["c0.mp3", "c1.mp3"]
