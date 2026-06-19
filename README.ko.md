# video-notes

[English](README.md) · [繁體中文](README.zh-TW.md) · [简体中文](README.zh-CN.md) · [日本語](README.ja.md) · **한국어** · [Español](README.es.md) · [Français](README.fr.md)

**YouTube URL 또는 로컬 동영상 파일**을 두 개의 Markdown으로 바꿔 주는
[Claude Code](https://claude.com/claude-code) 스킬입니다. 하나는 핵심 요점 노트, 다른 하나는
타임스탬프가 붙은 전체 자막 스크립트입니다.

Python 파이프라인은 스크립트(자막) 가져오기만 담당합니다. 요약, 요점, 챕터처럼 판단이 필요한
부분은 스크립트를 읽은 AI가 직접 작성합니다. 그래서 노트가 사람이 정리한 것처럼 읽히고, API를
한 번 더 호출해 억지로 이어 붙인 목록처럼 되지 않습니다.

## 왜 이 도구인가

- **pip 의존성 제로.** 표준 라이브러리만 사용하는 작은 Python 스크립트 7개. 필요한 것은 대부분
  이미 설치되어 있을 시스템 도구뿐입니다: `yt-dlp`, `ffmpeg`, `curl`.
- **깔끔한 YouTube 자동 자막 중복 제거.** YouTube의 두 줄 롤링 자동 자막은 거의 모든 단어가
  반복됩니다. 이 도구는 스크립트를 재구성해 중복 없이 한 번에 읽히도록 만들며, "성장형"과
  "슬라이딩 윈도우형" 두 가지 겹침 방식을 모두 처리합니다.
- **기계 번역이 아닌 원어 트랙 선택.** 자동 자막이 있는 영상에는 YouTube가 약 150개의 자동 번역
  자막 트랙을 붙여 둡니다. 이 도구는 의도적으로 원어 인식 결과(수동 자막 → 원어 수동 → 원어 자동)만
  가져오고, 번역은 정확도가 더 높은 요약 단계에 맡깁니다.
- **자막이 없을 때 Whisper로 폴백.** 저비트레이트 모노 오디오를 추출하고, API의 25 MB 한도를
  넘지 않는 청크로 나눈 뒤, `curl`로 각 청크를 전사하고 세그먼트 타임스탬프를 다시 합칩니다.

## 요구 사항

```bash
brew install yt-dlp ffmpeg   # macOS 예시. 다른 환경에서는 각자의 패키지 매니저를 사용하세요
```

Python 3.9 이상(표준 라이브러리만 사용, `pip install` 불필요).

`OPENAI_API_KEY`는 **선택 사항**으로, 영상에 사용할 수 있는 자막이 없어 Whisper 폴백이 실행될
때만 읽힙니다.

## 설치 (Claude Code 스킬로)

skills 디렉터리에 클론합니다:

```bash
git clone https://github.com/iamvista/video-notes ~/.claude/skills/video-notes
```

그런 다음 Claude Code에서 호출합니다:

```
/video-notes https://youtu.be/<id>
/video-notes ./talk.mp4 --out-dir ./notes --lang ko
```

## CLI 직접 사용 (AI 없이)

이 파이프라인 자체가 독립 실행형 CLI입니다. `transcript.json`을 출력하므로 노트 형식은 자유롭게
정할 수 있습니다.

```bash
python3 scripts/cli.py "https://youtu.be/<id>" --lang ko --out ./out
cat ./out/transcript.json
```

`transcript.json` 스키마:

```json
{
  "meta": {"type": "youtube", "title": "...", "source": "...", "channel": "...", "duration": "MM:SS", "video_id": "..."},
  "transcript_source": "subtitles",
  "segments": [{"start": 8.16, "text": "..."}]
}
```

## 동작 방식

```
source.py     인자 판별: YouTube URL인지 로컬 파일인지
meta.py       제목/채널/길이 가져오기 (yt-dlp -J 또는 ffprobe)
subtitles.py  최적 자막 트랙 가져오기 + 중복 제거   (우선 경로)
audio.py      모노 mp3 추출 후 25 MB 이하로 분할     (폴백)
whisper.py    Whisper API로 청크별 전사             (폴백)
cli.py        조율: 먼저 자막, 없으면 Whisper
transcript.py 타임스탬프 및 딥링크 포매팅 헬퍼
```

`SKILL.md`에는 `transcript.json`을 두 개의 Markdown으로 변환하기 위한 AI용 지침이 들어 있습니다.

## 출력 위치 커스터마이즈

`--out-dir`이 개인 워크플로를 위한 연결 지점입니다. 노트 보관소를 지정하고 `SKILL.md` 5단계에서
frontmatter 필드를 자신의 관례에 맞게 확장하세요. 스크립트 파이프라인 자체는 범용으로 유지됩니다.

## 테스트

```bash
python3 -m pytest tests/
```

표준 라이브러리만 사용하는 단위 테스트로, 소스 판별, 오디오 청크 계획, VTT 파싱 및 중복 제거,
Whisper 오프셋 병합, 타임스탬프 헬퍼를 다룹니다. 네트워크 연결은 필요 없습니다.

## 라이선스

MIT — [LICENSE](LICENSE)를 참고하세요.
