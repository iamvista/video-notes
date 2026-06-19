# video-notes

[English](README.md) · **繁體中文** · [日本語](README.ja.md)

一個 [Claude Code](https://claude.com/claude-code) skill，把 **YouTube 連結或本地影片檔**
變成兩份 Markdown：一份整理過的重點筆記，一份帶時間戳的完整逐字稿。

Python 管線只負責抓逐字稿。摘要、重點、章節這些需要判斷的部分，交給 AI 讀完逐字稿後自己寫，
所以筆記讀起來像人做的，而不是再呼叫一次 API 硬湊出來的條列。

## 為什麼選這個

- **零 pip 依賴。** 七支只用標準函式庫的 Python 小腳本。需要的只有你大概早就裝好的系統工具：
  `yt-dlp`、`ffmpeg`、`curl`。
- **乾淨的 YouTube 自動字幕去重。** YouTube 兩行滾動式自動字幕幾乎每個字都重複。這個工具會
  把逐字稿重建成讀一次到底、不重複，同時處理「成長型」與「滑動視窗型」兩種重疊。
- **抓原文軌，不抓機器翻譯。** 一支有自動字幕的影片，YouTube 會掛上大約 150 條自動翻譯字幕軌。
  這個工具刻意只取原始語言的辨識結果（人工字幕 → 原文人工 → 原文自動），把翻譯留到摘要那一步，
  品質更高。
- **沒有字幕時用 Whisper 後備。** 抽出低位元率單聲道音訊，切成每塊不超過 API 25 MB 上限的小段，
  用 `curl` 逐段轉錄，再把各段時間戳接回去。

## 環境需求

```bash
brew install yt-dlp ffmpeg   # macOS；其他平臺請用對應的套件管理器
```

Python 3.9 以上（只用標準函式庫，不必 `pip install`）。

`OPENAI_API_KEY` 是**選用的**，只有當影片沒有可用字幕、需要走 Whisper 後備時才會讀取。

## 安裝（作為 Claude Code skill）

複製到你的 skills 目錄：

```bash
git clone https://github.com/iamvista/video-notes ~/.claude/skills/video-notes
```

接著在 Claude Code 裡呼叫：

```
/video-notes https://youtu.be/<id>
/video-notes ./talk.mp4 --out-dir ./notes --lang zh
```

## 直接用 CLI（不透過 AI）

這套管線本身就是一個獨立 CLI，會吐出 `transcript.json`，後續筆記怎麼排版由你決定。

```bash
python3 scripts/cli.py "https://youtu.be/<id>" --lang zh --out ./out
cat ./out/transcript.json
```

`transcript.json` 結構：

```json
{
  "meta": {"type": "youtube", "title": "...", "source": "...", "channel": "...", "duration": "MM:SS", "video_id": "..."},
  "transcript_source": "subtitles",
  "segments": [{"start": 8.16, "text": "..."}]
}
```

## 運作方式

```
source.py     判斷參數：YouTube 連結還是本地檔
meta.py       抓標題／頻道／長度（yt-dlp -J 或 ffprobe）
subtitles.py  抓取並去重最佳字幕軌            （優先路徑）
audio.py      抽出單聲道 mp3 並切到 25 MB 以下 （後備）
whisper.py    透過 Whisper API 逐塊轉錄        （後備）
cli.py        調度：先字幕，沒有才走 Whisper
transcript.py 時間戳與深層連結的格式化工具
```

`SKILL.md` 收錄給 AI 的指示：怎麼把 `transcript.json` 變成那兩份 Markdown。

## 自訂輸出目的地

`--out-dir` 就是給個人工作流客製的接縫。把它指向你的筆記庫，再依照 `SKILL.md` 第五步擴充
frontmatter 欄位成你習慣的格式，逐字稿管線本身保持通用。

## 測試

```bash
python3 -m pytest tests/
```

純標準函式庫的單元測試，涵蓋來源判斷、音訊切塊規劃、VTT 解析與去重、Whisper 偏移合併，
以及時間戳工具，不需要連網。

## 授權

MIT，見 [LICENSE](LICENSE)。
