# video-notes

[English](README.md) · [繁體中文](README.zh-TW.md) · [简体中文](README.zh-CN.md) · **日本語** · [한국어](README.ko.md) · [Español](README.es.md) · [Français](README.fr.md)

**YouTube の URL またはローカル動画ファイル**を 2 つの Markdown に変換する
[Claude Code](https://claude.com/claude-code) スキルです。1 つは要点をまとめたノート、
もう 1 つはタイムスタンプ付きの完全な文字起こしです。

Python パイプラインは文字起こしの取得だけを担当します。要約・要点・チャプターといった
判断が必要な部分は、文字起こしを読んだ AI が自分で書きます。だからノートは人が取ったように
読め、API をもう一度呼んで継ぎ接ぎしたような箇条書きにはなりません。

## 選ばれる理由

- **pip 依存ゼロ。** 標準ライブラリだけの小さな Python スクリプト 7 本。必要なのは、たいてい
  すでに入っているシステムツールだけです：`yt-dlp`、`ffmpeg`、`curl`。
- **YouTube 自動字幕のきれいな重複除去。** YouTube の 2 行スクロール式自動字幕はほとんどの語が
  重複します。本ツールは文字起こしを再構成し、重複なく一度で読み通せるようにします。「成長型」と
  「スライディングウィンドウ型」の両方の重なりに対応します。
- **機械翻訳ではなく原語トラックを選ぶ。** 自動字幕付きの動画には、YouTube が約 150 本の自動翻訳
  字幕トラックを用意しています。本ツールはあえて原語の認識結果（手動字幕 → 原語の手動 → 原語の自動）
  を取得し、翻訳は精度の高い要約ステップに委ねます。
- **字幕がないときは Whisper にフォールバック。** 低ビットレートのモノラル音声を抽出し、API の
  25 MB 上限を超えないチャンクに分割し、`curl` で 1 つずつ文字起こしして、各セグメントの
  タイムスタンプを結合し直します。

## 必要環境

```bash
brew install yt-dlp ffmpeg   # macOS の例。他の環境では各自のパッケージマネージャを使用
```

Python 3.9 以上（標準ライブラリのみ、`pip install` 不要）。

`OPENAI_API_KEY` は**任意**です。動画に使える字幕がなく、Whisper フォールバックが走るときだけ
読み込まれます。

## インストール（Claude Code スキルとして）

skills ディレクトリにクローンします：

```bash
git clone https://github.com/iamvista/video-notes ~/.claude/skills/video-notes
```

Claude Code で呼び出します：

```
/video-notes https://youtu.be/<id>
/video-notes ./talk.mp4 --out-dir ./notes --lang ja
```

## CLI を直接使う（AI を介さずに）

パイプライン自体が独立した CLI です。`transcript.json` を出力するので、ノートの整形は自由に
行えます。

```bash
python3 scripts/cli.py "https://youtu.be/<id>" --lang ja --out ./out
cat ./out/transcript.json
```

`transcript.json` のスキーマ：

```json
{
  "meta": {"type": "youtube", "title": "...", "source": "...", "channel": "...", "duration": "MM:SS", "video_id": "..."},
  "transcript_source": "subtitles",
  "segments": [{"start": 8.16, "text": "..."}]
}
```

## しくみ

```
source.py     引数を判定：YouTube URL かローカルファイルか
meta.py       タイトル／チャンネル／長さを取得（yt-dlp -J または ffprobe）
subtitles.py  最適な字幕トラックを取得して重複除去   （優先パス）
audio.py      モノラル mp3 を抽出し 25 MB 以下に分割  （フォールバック）
whisper.py    Whisper API でチャンクごとに文字起こし  （フォールバック）
cli.py        統括：まず字幕、なければ Whisper
transcript.py タイムスタンプとディープリンクの整形ヘルパー
```

`SKILL.md` には、`transcript.json` を 2 つの Markdown に変換するための AI 向け指示が入っています。

## 出力先のカスタマイズ

`--out-dir` が個人ワークフロー向けの接続点です。ノートのライブラリを指定し、`SKILL.md` の
ステップ 5 で frontmatter の項目を自分の流儀に合わせて拡張してください。文字起こしパイプライン
自体は汎用のまま保たれます。

## テスト

```bash
python3 -m pytest tests/
```

標準ライブラリのみのユニットテストで、ソース判定・音声チャンク計画・VTT パースと重複除去・
Whisper のオフセット結合・タイムスタンプヘルパーをカバーします。ネットワーク接続は不要です。

## ライセンス

MIT — [LICENSE](LICENSE) を参照してください。
