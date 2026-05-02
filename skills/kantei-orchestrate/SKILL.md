---
name: kantei-orchestrate
description: /kantei コマンドの全体フロー制御。前提チェック→コンテキスト収集→占術計算→画像生成→統合→レンダリングを順に呼び出す
---

# kantei-orchestrate スキル

`/kantei` から呼ばれる司令塔。各サブスキルを順に呼び出し、エラー時に停止位置を明示する。

## 入力

- `subject` JSON（profile から or 引数から組み立てられたもの）
  ```json
  {
    "name_kanji": "...",
    "name_kana": "...",
    "birth_date": "YYYY-MM-DD",
    "birth_time": "HH:MM",
    "birth_time_known": true,
    "birth_place": "...",
    "birth_lat": 0.0,
    "birth_lon": 0.0,
    "timezone": "Asia/Tokyo",
    "include_modules": [...]
  }
  ```

## フロー

1. **前提チェック**
   - Python 3.10+, Node 20+, ffmpeg(任意), Codex CLI(任意)
   - 必要なPyPIパッケージ（pyswisseph, lunar-python など）

2. **作業ディレクトリ作成**
   - `output/[YYYY-MM-DD]_[name_kanji]/` を作る
   - subject を `subject.json` に保存

3. **コンテキスト収集** → `kantei-collect-context` を呼ぶ
   - 出力: `context.md`

4. **占術計算** → `kantei-engine` を呼ぶ
   - 出力: `modules.json`

5. **装飾画像生成** → `kantei-image` を呼ぶ（任意、Codex CLI 不在ならスキップ）
   - 出力: `images/cover.png` 他

6. **統合** → `kantei-integrate` を呼ぶ
   - 出力: `kantei.json`

7. **レンダリング** → `kantei-render` を呼ぶ
   - 出力: `kantei.png`, `kantei.pdf`, `kantei.html`

## 失敗時の振る舞い

- 各ステップで例外発生時は、どのステップで失敗したか、再開コマンドを明示
- `--rerun-from <step>` で途中再開できるようにする
- 中間ファイル（modules.json など）が既にあれば、そのステップはスキップ

## 実装メモ

- 各サブスキルは独立して呼び出せる粒度にする
- 鑑定師subagent（agents/kanteishi）の呼び出しは `kantei-integrate` 内で行う
