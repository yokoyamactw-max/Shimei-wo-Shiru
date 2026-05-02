---
description: 鑑定の初回セットアップ。氏名・生年月日・出生時間・出生地を登録し、senjutsu.jp の出生図JSONを取り込む
---

# /kantei-setup

このコマンドは Shimei-wo-Shiru プラグインの初回セットアップを行う。

## 動作

### Step 1. 既存設定スキャン

- 既存の `profile/kantei-profile.md` があれば差分のみ確認
- `~/.claude/projects/*/memory/MEMORY.md` から user メモリを読み、
  生年月日や氏名が既知なら自動補完

### Step 2. 必須項目の聴取

`AskUserQuestion` で以下を聞く（自動補完できなかった項目のみ）：

- 氏名（漢字、姓と名の間にスペース）
- 氏名（ヘボン式ローマ字、数秘術で使う）
- 生年月日（YYYY-MM-DD）
- 出生時間（HH:MM、不明なら「不明」）
- 出生地（都道府県＋市区町村）
- 性別（M/F、senjutsu.jp の入力に対応）

### Step 3. senjutsu.jp 出生図JSONの取得（重要）

鑑定の精度を最大化するため、senjutsu.jp の高精度計算結果を取り込む。
このステップは**1回だけ**で、以降の鑑定はこのJSONを使い回す。

**ユーザーへの案内文**：

```
【鑑定精度を最大化するため、出生図データを取得します】

以下の手順で1回だけ作業をお願いします：

1. ブラウザで開く:
   https://www.senjutsu.jp/horoscope

2. 入力:
   - 生年月日: {birth_date}
   - 出生時刻: {birth_time}
   - 都道府県: {birth_place の都道府県部分}
   - 性別: {gender}

3. 計算ボタンを押す

4. ページ下部の「JSONダウンロード」ボタンをクリック

5. ダウンロードした horoscope_*.json を以下に置く:
   {repo_path}/input/

6. 完了したら「OK」と入力してください
```

ユーザーが OK を返したら：
- `input/horoscope_*.json` を Glob で検索
- 見つかったファイルを `profile/kantei-profile.md` の `senjutsu_json` に記録
- JSONの `input.date`, `input.time`, `input.gender` などを開いて、
  Step 2 の入力と一致するか検証（不一致なら警告）

### Step 3.5. 人相・手相（任意・オプトイン）

ユーザーに `AskUserQuestion` で確認：
「人相・手相鑑定も加えますか？（顔写真と手のひら写真が必要、Claude API への送信に同意が必要）」

「はい」の場合のみ：

**プライバシー同意の明示**：
```
【プライバシー方針】
- 写真は鑑定実行中だけ Claude API に送信されます
- ローカルファイル以外には保存されません
- input/ ディレクトリは git 管理外です（写真が外部公開されることはありません）
- いつでもローカルから削除できます
- 同意しない場合は人相・手相は省略され、他の11占術のみで鑑定します

同意しますか？ (yes/no)
```

`yes` のみ次へ進む。`vision_consent: true` を profile に書く。

**撮影ガイド**：
```
【顔写真】input/face.jpg として置いてください
- 正面・無表情・自然光
- 髪で額や眉を隠さない
- メガネは外す
- 1024px以上推奨

【手のひら写真】input/hand_R.jpg（利き手）
- 利き手の手のひら全体（指は自然に開く）
- 影が落ちないよう斜め上から
- 主要線がはっきり写るピント
- 1024px以上推奨
- 任意で input/hand_L.jpg（反対の手）も置けば、先天/現在を読み分けます
```

ファイル配置を確認後、profile に photo_face / photo_hand_right / photo_hand_left を記録し、
include_modules に `ninsou` `tesou` を追加する。

### Step 4. profile/kantei-profile.md 書き出し

`profile/kantei-profile.md.template` をベースに、聴取値を埋めて
`profile/kantei-profile.md` を生成。

### Step 5. 完了案内

```
セットアップ完了。

次のコマンドで鑑定書を生成できます：
  /kantei         — フル鑑定書（PNG/PDF/HTML）
  /kantei-daily   — 当日のバイオリズム鑑定（短文）
```

## 失敗時の振る舞い

- 出生時間不明 → `birth_time_known: false` で正午固定にフォールバック
  （senjutsu.jp 側でも時刻不明オプションがあるので、それを使うよう案内）
- 出生地のジオコーディング失敗 → 緯度経度の手動入力を促す
- senjutsu.jp JSONが見つからない → Step 3 を再実行

## 注意

- `profile/kantei-profile.md` と `input/horoscope_*.json` は個人情報を含むため
  `.gitignore` 対象。配布版は `kantei-profile.md.template` のみ含む
- senjutsu.jp は client-side JavaScript で計算されており、ユーザー自身の
  ブラウザでの個人利用そのもの。プラグインから直接アクセスはしない
