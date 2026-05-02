---
name: kantei-render
description: kantei.json と装飾画像から、PNG（縦長サムネ）/ PDF（A4詳細）/ HTML（Web表示）の3種を Puppeteer で出力する
---

# kantei-render スキル

最終レンダリング層。3種の出力を生成する。

## 入力

- `output/[案件]/kantei.json`（統合鑑定）
- `output/[案件]/modules.json`（占術別生データ）
- `output/[案件]/images/`（任意）
- `templates/kantei_thumb.html`
- `templates/kantei_pdf.html`
- `templates/kantei_web.html`

## 動作

### 1. データ注入

`tools/render.js` が3つのテンプレを読み、以下を埋め込む：
- 鑑定師の文（kantei.json の各セクション）
- 占術別の表（modules.json から五格表・命式表・出生図など）
- 画像パス（images/ から相対参照）

### 2. PNG生成（縦長サムネ）

- Puppeteer で `kantei_thumb.html` を 1080×1920 でレンダリング
- 出力: `output/[案件]/kantei.png`
- 用途: SNSシェア、X投稿向け

### 3. PDF生成（A4詳細）

- Puppeteer で `kantei_pdf.html` を A4 縦でレンダリング
- 出力: `output/[案件]/kantei.pdf`
- 章立ては `agents/kanteishi.md` のスキーマに対応：
  1. 表紙
  2. 鑑定の総論（headline / constitution）
  3. 各占術章（modules.json）
  4. 統合：使命 / 天賦 / 取り組むべきこと / 罠
  5. 人生の山場（life_phases）
  6. ラッキー要素

### 4. HTML生成（Web表示）

- `kantei_web.html` のテンプレに値を埋めて `output/[案件]/kantei.html` へ
- 章ごとアコーディオン
- バイオリズムは Chart.js で当日±30日のグラフ
- レスポンシブ

## 失敗時の振る舞い

- Puppeteer 起動失敗 → `npm install puppeteer` を案内
- フォント不足（Noto Serif JP） → ダウンロード手順を表示してフォールバック
- 画像不在 → プレーン装飾のCSSに切替え

## 実装メモ

- フォント: `Noto Serif JP` を `data/fonts/` に同梱、`@font-face` でローカル参照
- 縦書きが必要な箇所は CSS `writing-mode: vertical-rl`
- A4 PDF は `@page` で余白とサイズを制御
- Puppeteer の `page.pdf()` は `format: 'A4'`, `printBackground: true`
