# tests/test_transcript.py
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
from transcript import fmt_timestamp, youtube_link

def test_fmt_timestamp_short_and_long():
    assert fmt_timestamp(0) == "00:00"
    assert fmt_timestamp(201) == "03:21"
    assert fmt_timestamp(3801) == "1:03:21"

def test_youtube_link_appends_start_seconds():
    url = "https://www.youtube.com/watch?v=abc123"
    assert youtube_link(url, 754.7) == "https://www.youtube.com/watch?v=abc123&t=754s"

def test_youtube_link_none_for_local():
    assert youtube_link(None, 10) is None
