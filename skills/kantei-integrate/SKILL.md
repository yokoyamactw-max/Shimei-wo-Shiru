---
name: kantei-integrate
description: modules.json と context.md を agents/kanteishi に渡し、厳格鑑定師として統合鑑定JSONを生成させる
---

# kantei-integrate スキル

15占術の生データを「使命」へと束ねる統合レイヤー。
鑑定師subagent（`agents/kanteishi`）を呼び出す。

## 入力

- `output/[案件]/modules.json`
- `output/[案件]/context.md`
- `output/[案件]/subject.json`

## 動作

1. 入力3ファイルを読み込み、subagent への入力ペイロードを構成
   ```json
   {
     "subject": {...},
     "modules": {...},
     "user_context": "（context.md の本文）"
   }
   ```

2. **subagent 起動**
   - `Agent` ツールで `subagent_type: kanteishi` を指定
   - プロンプトに上記ペイロードと「JSONで返せ」の指示を含める
   - `agents/kanteishi.md` の出力スキーマに従わせる

3. **検証**
   - 返ってきたJSONをパース
   - スキーマ違反（必須フィールド欠落、型違い）があれば1回だけ再試行
   - 2回失敗時は raw 応答をデバッグ用に保存して中断

4. `output/[案件]/kantei.json` に保存

## 出力スキーマ

`agents/kanteishi.md` 参照。

## 失敗時の振る舞い

- subagent タイムアウト（>5分）→ 中断、再実行を案内
- JSON パースエラー → raw 応答を `kantei.raw.txt` に保存し、ユーザーに表示

## 実装メモ

- subagent は独立コンテキストで動くので、メイン会話のトークンを節約できる
- プロンプトキャッシュを意識して、鑑定師ペルソナ部（agents/kanteishi.md 本文）を
  プレフィクスに置く
