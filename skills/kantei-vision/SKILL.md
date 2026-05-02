---
name: kantei-vision
description: 顔写真・手のひら写真からClaude Visionで人相・手相を読み取り、modules.json に統合する。観相と手相は専用subagent（agents/ninsou・agents/tesou）で別個に分析する。
---

# kantei-vision スキル

人相（顔写真）・手相（手のひら写真）を Claude Vision で読み取り、
鑑定書の追加章として組み込む。

## 入力

- `profile/kantei-profile.md` の以下を参照：
  - `vision_consent: true` （明示同意フラグ）
  - `photo_face: input/face.jpg` （顔写真パス、任意）
  - `photo_hand: input/hand.jpg` または `photo_hand_right`/`photo_hand_left` （手のひら写真）

## 動作

### Step 0. 同意確認

`vision_consent: true` でない場合は何もせず終了。
ユーザーに「人相・手相鑑定を加えるには profile に `vision_consent: true` を設定し、写真を input/ に置いてください」と案内。

### Step 1. 写真の存在確認と品質チェック

- `photo_face` が指定されていれば Read で確認、無ければ skip
- `photo_hand` （または左右別）が指定されていれば Read で確認、無ければ skip
- 写真サイズが極端に小さい（< 256px 相当）場合は警告ログを残し、subagent に「品質不足」を返す可能性を伝える

### Step 2. 人相鑑定（顔写真がある場合）

`Agent` ツールで `subagent_type: ninsou` を呼ぶ：
- prompt に写真パスと「Readで画像を読み込んで麻衣相法に基づき鑑定し、定義済みスキーマでJSONのみ返せ」を指示
- 出力を `output/[案件]/ninsou.json` に保存

### Step 3. 手相鑑定（手のひら写真がある場合）

`Agent` ツールで `subagent_type: tesou` を呼ぶ：
- 両手分があれば「右=現在、左=先天」として両方読み、片方しかなければ現在運として読むよう指示
- 出力を `output/[案件]/tesou.json` に保存

### Step 4. modules.json への統合

既存の `modules.json` を読み、`modules.ninsou` / `modules.tesou` フィールドを追加して書き戻す。

## プライバシー方針（完全ローカル方式）

- 写真は鑑定実行中のみ Claude API に送信される（Vision推論のため一時的に）
- API応答後、ローカルファイル以外には保存されない
- `input/` と `output/` は `.gitignore` 対象
- ユーザーが手動で写真を `input/` から削除すれば完全に手元から消える
- `vision_consent: true` を明示的に設定したユーザーのみ動作する（オプトイン）

## 失敗時の振る舞い

- 写真ファイル不在 → 該当章をスキップ、`modules.json` には追加しない
- subagent からの応答が JSON パース不能 → 1回だけ再試行、再失敗時は該当章スキップ
- 写真品質不足 → subagent が `image_quality: "不足"` を返す → 鑑定書では「観取困難」と表示

## 並列化

人相と手相は独立タスクなので、`Agent` の並列呼び出しが可能なら同時に走らせる。

## 実装メモ

- subagent は `Read` ツールのみ持つ（書き込みは親側で行う）
- 親スキルは subagent から返ってきた JSON 文字列を受け取り、ファイルへ書く
- subagent プロンプトには「Markdown のコードフェンスで包まず純粋な JSON を返せ」と明示
