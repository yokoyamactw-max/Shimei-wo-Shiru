# Shimei-wo-Shiru（使命を知る）

和洋15占術を統合し、匿名の鑑定師が「使命」を告げる鑑定書をClaude Code内で生成するプラグイン。

## できること

- 氏名（漢字）・生年月日・出生時間・出生地から鑑定書を生成
- 和洋11占術を統合し、Claudeが厳格な匿名の鑑定師として「使命」を告げる
- ObsidianVaultとClaude Code memoryからユーザー文脈を読み、現在地に即した助言を返す
- 出力: 縦長PNG（SNS共有用）／A4詳細PDF（保存用）／HTML（Web表示用）

## 採用占術（11 + 任意2）

**東洋**: 姓名判断、四柱推命、紫微斗数、九星気学、宿曜占星術、算命学
**西洋**: 西洋占星術、インド占星術、数秘術
**周期**: バイオリズム、マヤ暦（銀河のマヤ流）

**Vision鑑定（オプトイン）**:
- 人相（麻衣相法） — 顔写真から
- 手相（西洋＋日本手相術） — 手のひら写真から

Vision鑑定は明示的な同意（`vision_consent: true`）を設定したユーザーのみ動作します。
写真は鑑定実行中だけ Claude API に送信され、ローカル以外には保存されません。

### 高精度の秘密

西洋占星術・インド占星術・四柱推命など計算が複雑な占術は、
[senjutsu.jp](https://www.senjutsu.jp/horoscope) の高精度JSONを活用します。
ユーザーは初回セットアップ時に**1回だけ**自分のブラウザで出生図JSONをダウンロードし、
プラグインに渡すだけ。以降の鑑定はこのJSONを使い回します。

自前実装する占術は精度が安定するもののみに絞り、流派は固定しています：
- 姓名判断: 康熙字典
- 算命学: 高尾義政流
- 数秘術: ピタゴラス式＋ヘボン式ローマ字
- マヤ暦: 「銀河のマヤ」流（ホゼ・アグエイアス系）

## インストール

```
/plugin marketplace add catchtheweb/Shimei-wo-Shiru
/plugin install shimei-wo-shiru
```

## 使い方

```
/kantei-setup     # 初回のみ。氏名・生年月日などを登録
/kantei           # フル鑑定書を生成
/kantei-daily     # 当日のバイオリズムと運勢
```

## 必要な環境

- Claude Code
- Python 3.10+（pyswisseph, lunar-python など）
- Node.js 20+（Puppeteer）
- Codex CLI（gpt-image-2 装飾画像生成用、任意）

## ライセンス

MIT
