# tests/test_audio.py
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
from audio import plan_chunks

def test_single_chunk_when_under_limit():
    chunks = plan_chunks(file_bytes=10_000_000, duration_s=600, max_bytes=24_000_000)
    assert chunks == [{"index": 0, "start": 0.0, "length": 600.0}]

def test_multiple_chunks_split_evenly_by_time():
    chunks = plan_chunks(file_bytes=48_000_000, duration_s=600, max_bytes=24_000_000)
    assert len(chunks) == 2
    assert chunks[0] == {"index": 0, "start": 0.0, "length": 300.0}
    assert chunks[1]["start"] == 300.0

def test_rounds_chunk_count_up():
    chunks = plan_chunks(file_bytes=50_000_000, duration_s=900, max_bytes=24_000_000)
    assert len(chunks) == 3
    assert chunks[0]["start"] == 0.0
    assert abs(chunks[1]["start"] - 300.0) < 1e-6
