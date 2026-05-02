---
description: フル鑑定書を生成する。引数なしで profile/kantei-profile.md から自動取得。和洋11占術 + Vision鑑定（任意）を統合し、PNG/PDF/HTMLを出力
---

# /kantei

和洋11占術（+任意でVision鑑定）を統合した鑑定書（PNG/PDF/HTML）を生成する。

## 引数

- 引数なし: `profile/kantei-profile.md` を読んで自分の鑑定
- 別人鑑定の場合は profile を一時的に書き換えて実行する（複数人プロファイルは未対応）

## Claude が実行する手順

### Step 1. 前提チェック

- `profile/kantei-profile.md` を Read で読み込む。frontmatter を YAML としてパース
- 無ければ「`/kantei-setup` を先に実行してください」と案内して終了
- `senjutsu_json` で指定されたパスのファイルが存在するか確認。無ければ `/kantei-setup` Step 3 を再案内
- 必要なPythonパッケージ確認: `python3 -c "import lunar_python"` がエラーなら `pip3 install --user --break-system-packages lunar-python` を案内

### Step 2. 作業ディレクトリ準備

```bash
TODAY=$(date +%Y-%m-%d)
NAME=<profile.name_kanji from spaces removed>
WORKDIR=output/${TODAY}_${NAME}
mkdir -p $WORKDIR
```

profile から `subject.json` を組み立てて `$WORKDIR/subject.json` に保存。

### Step 3. ユーザー文脈収集

`Skill` ツールで `kantei-collect-context` を呼び出し、`$WORKDIR/context.md` を生成。
`obsidian_vault` も `memory_root` も指定が無ければスキップ。

### Step 4. 計算層実行

```bash
tools/run_kantei.sh $WORKDIR/subject.json <senjutsu_json> $WORKDIR
```

`$WORKDIR/modules.json` が出力される。11占術が並ぶ。

### Step 5. Vision鑑定（vision_consent: true のときのみ）

`Skill` ツールで `kantei-vision` を呼ぶ。
`agents/ninsou` と `agents/tesou` を `Agent` ツールで起動し、写真を読ませる。
結果を `$WORKDIR/modules.json` の `modules.ninsou` / `modules.tesou` に追記。

### Step 6. 統合（鑑定師subagent呼び出し）

`Agent` ツールで `subagent_type: kanteishi` を呼び出す。
プロンプトは以下：

```
以下のJSONから、agents/kanteishi.md の出力スキーマに従い、
匿名鑑定師として統合鑑定JSONを返せ。Markdownのコードフェンスで包まず、純粋なJSONのみ返せ。

【subject.json】
<...>

【modules.json】
<...>

【context.md】
<...>
```

返ってきた JSON を検証してから `$WORKDIR/kantei.json` に保存。
パースエラーや必須フィールド欠落時は1度だけ再試行、再失敗時は raw 応答を `kantei.raw.txt` に保存して中断。

### Step 7. レンダリング

```bash
node tools/render.js --workdir $WORKDIR
```

以下が生成される：
- `$WORKDIR/kantei.html`
- `$WORKDIR/kantei.pdf` (A4)
- `$WORKDIR/kantei.png` (1080×fullPage)

### Step 8. 完了報告

ユーザーに以下を表示：
- 出力先: `$WORKDIR/`
- 生成ファイル一覧
- `kantei.png` をチャットに添付（Read で画像表示）
- `kantei.headline` を引用して結びとする

## 失敗時の振る舞い

| 失敗箇所 | 対応 |
|---|---|
| Step 1 前提不足 | `/kantei-setup` を案内 |
| Step 4 計算エラー | エラーモジュールを `errors[]` に記録、可能な範囲で続行 |
| Step 5 Vision失敗 | スキップして他で進む |
| Step 6 subagent JSON エラー | 1回再試行、再失敗で `kantei.raw.txt` 保存して中断 |
| Step 7 Puppeteer失敗 | `npm install` 案内 |

## オプション（将来）

- `--rerun-from <step>`: 途中再開
- `--no-vision`: profile設定を無視してVision鑑定をスキップ
- `--no-context`: ユーザー文脈収集をスキップ

## 出力例

```
output/2026-05-03_横山直広/
├── subject.json
├── context.md           # ユーザー文脈
├── modules.json         # 11占術 + 任意で人相・手相
├── kantei.json          # 統合鑑定
├── kantei.html
├── kantei.pdf           # A4詳細
└── kantei.png           # 縦長サムネ
```
