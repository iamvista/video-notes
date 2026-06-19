# video-notes

[English](README.md) · [繁體中文](README.zh-TW.md) · **简体中文** · [日本語](README.ja.md) · [한국어](README.ko.md) · [Español](README.es.md) · [Français](README.fr.md)

一个 [Claude Code](https://claude.com/claude-code) skill，把 **YouTube 链接或本地视频文件**
变成两份 Markdown：一份整理好的要点笔记，一份带时间戳的完整文字稿。

Python 流水线只负责抓取文字稿。摘要、要点、章节这些需要判断的部分，交给 AI 读完文字稿后自己写，
所以笔记读起来像人做的，而不是再调用一次 API 硬凑出来的罗列。

## 为什么选它

- **零 pip 依赖。** 七个只用标准库的 Python 小脚本。需要的只有你多半早就装好的系统工具：
  `yt-dlp`、`ffmpeg`、`curl`。
- **干净的 YouTube 自动字幕去重。** YouTube 两行滚动式自动字幕几乎每个字都重复。本工具会把文字稿
  重建成一遍读到底、不重复，同时处理「成长型」和「滑动窗口型」两种重叠。
- **取原语轨，而非机器翻译。** 一个带自动字幕的视频，YouTube 会挂上约 150 条自动翻译字幕轨。本工具
  刻意只取原始语言的识别结果（人工字幕 → 原语人工 → 原语自动），把翻译留到精度更高的摘要那一步。
- **没有字幕时用 Whisper 兜底。** 抽出低比特率单声道音频，切成每块不超过 API 25 MB 上限的小段，
  用 `curl` 逐段转写，再把各段时间戳拼接回去。

## 环境要求

```bash
brew install yt-dlp ffmpeg   # macOS 示例；其他平台请用各自的包管理器
```

Python 3.9 以上（仅用标准库，无需 `pip install`）。

`OPENAI_API_KEY` 是**可选的**，只有当视频没有可用字幕、需要走 Whisper 兜底时才会读取。

## 安装（作为 Claude Code skill）

克隆到你的 skills 目录：

```bash
git clone https://github.com/iamvista/video-notes ~/.claude/skills/video-notes
```

然后在 Claude Code 里调用：

```
/video-notes https://youtu.be/<id>
/video-notes ./talk.mp4 --out-dir ./notes --lang zh
```

## 直接用 CLI（不经过 AI）

这套流水线本身就是一个独立 CLI，会输出 `transcript.json`，后续笔记怎么排版由你决定。

```bash
python3 scripts/cli.py "https://youtu.be/<id>" --lang zh --out ./out
cat ./out/transcript.json
```

`transcript.json` 结构：

```json
{
  "meta": {"type": "youtube", "title": "...", "source": "...", "channel": "...", "duration": "MM:SS", "video_id": "..."},
  "transcript_source": "subtitles",
  "segments": [{"start": 8.16, "text": "..."}]
}
```

## 工作原理

```
source.py     判断参数：YouTube 链接还是本地文件
meta.py       抓标题／频道／时长（yt-dlp -J 或 ffprobe）
subtitles.py  抓取并去重最佳字幕轨            （首选路径）
audio.py      抽出单声道 mp3 并切到 25 MB 以下 （兜底）
whisper.py    通过 Whisper API 逐块转写        （兜底）
cli.py        调度：先字幕，没有再走 Whisper
transcript.py 时间戳与深链的格式化工具
```

`SKILL.md` 收录给 AI 的指令：如何把 `transcript.json` 变成那两份 Markdown。

## 自定义输出位置

`--out-dir` 就是给个人工作流定制的接缝。把它指向你的笔记库，再按 `SKILL.md` 第五步扩展
frontmatter 字段成你习惯的格式，文字稿流水线本身保持通用。

## 测试

```bash
python3 -m pytest tests/
```

纯标准库的单元测试，覆盖来源判断、音频切块规划、VTT 解析与去重、Whisper 偏移合并，
以及时间戳工具，无需联网。

## 许可证

MIT，见 [LICENSE](LICENSE)。
