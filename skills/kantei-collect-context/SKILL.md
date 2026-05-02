---
name: kantei-collect-context
description: ObsidianVaultとClaude Code memoryからユーザーの現在地・関心・悩みを抽出し、鑑定師subagentに渡すcontext.mdを生成する
---

# kantei-collect-context スキル

このプラグインの真骨頂。鑑定書を「カタログ」で終わらせず、
ユーザーの実生活に接続するための文脈収集レイヤー。

## 入力

- `profile/kantei-profile.md` の `obsidian_vault`, `memory_root`
- 出力先: `output/[案件]/context.md`

## 動作

1. **Obsidian Vault スキャン**（パスが設定されていれば）
   - 直近30日に更新された `.md` ファイルをリスト
   - 上位20件の本文を読み、テーマ・悩み・関心を抽出
   - PII（パスワード等）はマスク

2. **Claude Code memory スキャン**
   - `memory_root/*/memory/MEMORY.md` を読む
   - user/project/feedback タイプから関連性の高いものを抽出

3. **要約生成**
   - 以下の構造化された context.md を作る：

```markdown
# ユーザー文脈サマリ

## 現在の関心テーマ（直近30日）
- ...
- ...

## 現在の悩み・課題
- ...

## 直近の意思決定・転機
- ...

## 価値観・行動原理（メモリから）
- ...

## 関わっているプロジェクト
- ...
```

4. **トークン制限**
   - 全体で2000トークン以内に収める
   - 超えそうなら関連性スコアで絞る

## 失敗時の振る舞い

- ObsidianVault パス未設定 → スキップして memory のみ使う
- 両方とも空 → 「ユーザー文脈なし。命式のみで鑑定」と context.md に記載
- ファイル読取エラー → 該当ファイルをスキップして続行

## 実装メモ

- Bash で Glob → 上位N件を Read
- 個人情報の取扱いに注意（context.md は output/ 内、gitignore対象）
- ユーザーが望めば `--no-context` でこのステップをスキップ可
