---
description: フル鑑定書を生成する。引数なしで profile/kantei-profile.md から自動取得、引数指定で別人鑑定も可能
---

# /kantei

和洋15占術を統合した鑑定書（PNG/PDF/HTML）を生成する。

## 引数

- 引数なし: `profile/kantei-profile.md` を読んで自分の鑑定
- `/kantei "山田太郎" 1990-03-15 09:30 "京都市"`: 指定した人物の鑑定（profile非依存）

## 動作フロー

1. **前提チェック**
   - `profile/kantei-profile.md` の存在確認（無ければ `/kantei-setup` を案内）
   - Python・Node・必要ライブラリの存在確認

2. **コンテキスト収集** → `kantei-collect-context` スキルを呼ぶ
   - ObsidianVault から最近30日のメモを要約
   - Claude Code memory（user/project）から関連情報を取得

3. **占術計算** → `kantei-engine` スキルを呼ぶ
   - 15占術を並列実行（`tools/*.py`）
   - 結果を `output/[YYYY-MM-DD]_[氏名]/modules.json` に保存

4. **装飾画像生成** → `kantei-image` スキルを呼ぶ
   - Codex CLI（gpt-image-2）で表紙＋章扉絵を並列生成
   - `output/.../images/` に保存

5. **統合鑑定文生成** → `kantei-integrate` スキルが `agents/kanteishi` subagent を呼ぶ
   - modules.json + コンテキスト要約を入力
   - 厳格鑑定師ペルソナで統合JSONを出力（headline / mission / talents / todo_now / warnings / life_phases / lucky）
   - `output/.../kantei.json` に保存

6. **レンダリング** → `kantei-render` スキルを呼ぶ
   - Puppeteer で `templates/kantei_thumb.html` → `kantei.png`（1080×1920）
   - Puppeteer で `templates/kantei_pdf.html` → `kantei.pdf`（A4）
   - `templates/kantei_web.html` をコピーして `kantei.html`

7. **完了**
   - `output/[YYYY-MM-DD]_[氏名]/` のパスを表示
   - PNG をチャットに添付表示

## 失敗時の振る舞い

- 各ステップで失敗した場合、どのステップかを明示
- modules.json が既に存在する場合はスキップ可（`--rerun` で強制再計算）
- 装飾画像生成は任意（Codex CLI が無ければスキップしてプレーン背景を使う）

## 出力例

```
output/2026-05-02_横山直広/
├── kantei.png          # 1080×1920 縦長サムネ
├── kantei.pdf          # A4 詳細鑑定書
├── kantei.html         # ブラウザ表示用
├── kantei.json         # 統合鑑定結果
├── modules.json        # 各占術の生データ
├── context.md          # 収集したユーザー文脈
└── images/             # 装飾画像
    ├── cover.png
    ├── shichu.png
    └── ...
```
