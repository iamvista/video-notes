# tests/test_source.py
import os, sys, tempfile
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import pytest
from source import detect_source

@pytest.mark.parametrize("arg,expected_id", [
    ("https://www.youtube.com/watch?v=dQw4w9WgXcQ", "dQw4w9WgXcQ"),
    ("https://youtu.be/dQw4w9WgXcQ", "dQw4w9WgXcQ"),
    ("https://www.youtube.com/watch?v=dQw4w9WgXcQ&t=42s", "dQw4w9WgXcQ"),
    ("https://www.youtube.com/shorts/dQw4w9WgXcQ", "dQw4w9WgXcQ"),
])
def test_detects_youtube(arg, expected_id):
    s = detect_source(arg)
    assert s["type"] == "youtube"
    assert s["id"] == expected_id
    assert s["url"] == f"https://www.youtube.com/watch?v={expected_id}"

def test_detects_local_file():
    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as f:
        path = f.name
    s = detect_source(path)
    assert s["type"] == "local"
    assert s["path"] == os.path.abspath(path)

def test_rejects_missing_local_and_nonyoutube():
    with pytest.raises(ValueError):
        detect_source("/no/such/file.mp4")
    with pytest.raises(ValueError):
        detect_source("https://vimeo.com/12345")
