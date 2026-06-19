# tests/test_subtitles.py
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
from subtitles import parse_vtt, pick_lang, _match_lang, LANG_PRIORITY

SAMPLE_VTT = """WEBVTT

00:00:00.000 --> 00:00:02.500
大家好

00:00:02.500 --> 00:00:05.000
今天要談的主題是

00:00:05.000 --> 00:00:07.000
今天要談的主題是 AI
"""

def test_parse_vtt_returns_seconds_and_text():
    segs = parse_vtt(SAMPLE_VTT)
    assert segs[0] == {"start": 0.0, "text": "大家好"}
    assert segs[1] == {"start": 2.5, "text": "今天要談的主題是 AI"}
    assert len(segs) == 2

def test_parse_vtt_collapses_rolling_duplicates():
    segs = parse_vtt(SAMPLE_VTT)
    texts = [s["text"] for s in segs]
    assert "今天要談的主題是" not in texts        # bare prefix dropped
    assert "今天要談的主題是 AI" in texts         # longer version kept

NO_MERGE_VTT = """WEBVTT

00:00:01.000 --> 00:00:04.000
AI is transformative

00:00:30.000 --> 00:00:33.000
AI
"""

def test_parse_vtt_keeps_independent_cues_sharing_prefix():
    segs = parse_vtt(NO_MERGE_VTT)
    texts = [s["text"] for s in segs]
    assert texts == ["AI is transformative", "AI"]

TAG_VTT = """WEBVTT

00:00:01.000 --> 00:00:03.000
<00:00:01.000><c>Hello</c> <00:00:01.500><c>world</c>
"""

def test_parse_vtt_strips_inline_tags():
    segs = parse_vtt(TAG_VTT)
    assert segs[0]["text"] == "Hello world"

SLIDING_VTT = """WEBVTT

00:00:01.000 --> 00:00:03.000
the cool thing about these guys

00:00:03.000 --> 00:00:05.000
about these guys is their trunks
"""

def test_parse_vtt_dedups_sliding_window():
    segs = parse_vtt(SLIDING_VTT)
    assert [s["text"] for s in segs] == ["the cool thing about these guys",
                                         "is their trunks"]
    # the new tail keeps the timestamp of the cue that introduced it
    assert segs[1]["start"] == 3.0

ENTITY_VTT = """WEBVTT

00:00:01.000 --> 00:00:03.000
&gt;&gt; hello &amp; welcome
"""

def test_parse_vtt_decodes_html_entities():
    segs = parse_vtt(ENTITY_VTT)
    assert segs[0]["text"] == ">> hello & welcome"

def test_pick_lang_prefers_traditional_chinese():
    available = ["en", "zh-Hans", "zh-Hant"]
    assert pick_lang(available) == "zh-Hant"
    assert pick_lang(["en", "fr"]) == "en"
    assert pick_lang(["fr", "de"]) is None

def test_lang_priority_order():
    assert LANG_PRIORITY[:4] == ["zh-Hant", "zh-Hans", "zh", "en"]

def test_match_lang_prefers_exact_then_orig_then_base():
    # original-ASR key '<base>-orig' beats bare base
    assert _match_lang(["en", "en-orig", "fr"], "en-US") == "en-orig"
    # bare base when no exact/orig
    assert _match_lang(["en", "fr"], "en-US") == "en"
    # regional variant as last resort
    assert _match_lang(["en-GB", "fr"], "en-US") == "en-GB"
    # exact match for a Chinese original
    assert _match_lang(["zh-Hant", "ja"], "zh-Hant") == "zh-Hant"
    # no match, and None language
    assert _match_lang(["fr", "de"], "en") is None
    assert _match_lang(["en"], None) is None
