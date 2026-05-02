# Shimei-wo-Shiru — プラグイン共通指示

このプラグインは、氏名・生年月日・出生時間・出生地から和洋15占術を統合し、
匿名の鑑定師が「使命」を告げる鑑定書（PNG/PDF/HTML）をClaude Code内で生成します。

## レイヤー構造

| 層 | 場所 | 性格 |
|---|---|---|
| 共通レイヤー | `commands/`, `skills/`, `agents/`, `tools/`, `data/`, `templates/` | 全ユーザー共通。プラグインアップデート対象 |
| 個人化レイヤー | `profile/kantei-profile.md` | ユーザーごと。`/kantei-setup` で生成 |
| 環境レイヤー | `output/`, `.env` | git管理外 |

**重要**: 共通レイヤーから個人化レイヤー（`profile/kantei-profile.md`）に依存する形で書く。
ハードコードされた個人情報を `skills/` や `commands/` に書かない。

## 鑑定師ペルソナ

鑑定師は**匿名**。固有名は付けない。
口調は「厳格・プロフェッショナル」で固定。慰めや迎合はしない。
詳細は `agents/kanteishi.md` を参照。

## コマンド

- `/kantei-setup` — 初回設定。氏名・生年月日・出生時間・出生地を `profile/kantei-profile.md` に保存
- `/kantei` — フル鑑定書を生成（引数なしで profile から自動）
- `/kantei-daily` — 当日のバイオリズムと運勢のみ短文で

## スキル

- `kantei-orchestrate` — 全体フロー制御
- `kantei-collect-context` — Obsidian Vault と Claude Code memory からユーザー文脈を収集
- `kantei-engine` — 15占術の計算実行（Python）
- `kantei-integrate` — 鑑定師subagentで統合鑑定文を生成
- `kantei-image` — Codex CLI / gpt-image-2 で装飾画像を生成
- `kantei-render` — Puppeteer で PNG/PDF/HTML 出力

## 占術範囲（11+2占術）

東洋: 姓名判断、四柱推命、紫微斗数、九星気学、宿曜占星術、算命学
西洋: 西洋占星術、インド占星術、数秘術
周期: バイオリズム、マヤ暦（銀河のマヤ流）
**Vision（オプトイン）**: 人相（麻衣相法）、手相（西洋＋日本手相術）

### 出処の方針

- **senjutsu.jp の出生図JSONを最大活用**：西洋占星術・インド占星術・四柱推命・
  宿曜（月ナクシャトラ）・算命学（命式）はこのJSONから取り込む
- **自前計算**：姓名判断・紫微斗数・数秘術・九星気学・算命学（主星/従星）・
  バイオリズム・マヤ暦
- **流派固定**：姓名判断は康熙字典、算命学は高尾流、数秘術はピタゴラス式＋
  ヘボン式ローマ字、マヤ暦は銀河のマヤ流
- **除外**：0学占い（アルゴリズム非公開）、動物占い（商標）、ヒューマンデザイン、
  ルーン、タロット

## 出力規約

- `output/[YYYY-MM-DD]_[氏名]/` に格納
- `kantei.png`（縦長サムネ）、`kantei.pdf`（A4詳細）、`kantei.html`（Web表示）、`modules.json`（占術別生データ）
- 各スキルは中間ファイルを保存し、途中で失敗してもそのステップから再開できるようにする

## 個人情報の取り扱い

- `profile/kantei-profile.md` には生年月日・出生地などが含まれる → `.gitignore` 対象
- `output/` も `.gitignore` 対象
- 配布版は `profile/kantei-profile.md.template` のみ含む

## 配布版としての注意

- このリポジトリはGitHub marketplaceで配布される前提
- ハードコードされたパス・個人情報を共通レイヤーに書かない
- スキル更新時は `profile/` を上書きしない
- 動作にAPIキーが必要なものは `.env` から読み込む
