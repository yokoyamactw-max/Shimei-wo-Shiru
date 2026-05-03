# Shimei-wo-Shiru（使命を知る）

> 和洋11占術 + Vision鑑定（人相・手相）を統合し、匿名の鑑定師が「使命」を告げる鑑定書をClaude Code内で生成するプラグイン。

![status](https://img.shields.io/badge/status-private--alpha-orange)
![license](https://img.shields.io/badge/license-MIT-blue)

---

## できること

- 氏名（漢字）・生年月日・出生時間・出生地から個別の鑑定書を生成
- **和洋11占術 + 任意のVision鑑定2つ（人相・手相）= 最大13占術**を統合
- ObsidianVault と Claude Code memory からユーザーの現在地を読み、生きた助言を返す
- 出力3点セット: 縦長PNG（SNS共有用）／ A4詳細PDF（保存用）／ HTML（Web表示用）

## 採用占術

| 系統 | 占術 |
|---|---|
| **東洋（命式系）** | 姓名判断 / 四柱推命 / 紫微斗数 / 九星気学 / 宿曜占星術 / 算命学 |
| **西洋（位相系）** | 西洋占星術 / インド占星術（シデリアル・ラヒリ） / 数秘術 |
| **周期系** | バイオリズム / マヤ暦（銀河のマヤ流） |
| **Vision鑑定（オプトイン）** | 人相（麻衣相法） / 手相（西洋＋日本手相術） |

### 流派固定

精度を担保するため、以下の流派に固定しています：
- **姓名判断**: 康熙字典（10万字Unihanベース＋約60件の正字補正）
- **算命学**: 高尾義政流
- **数秘術**: ピタゴラス式 ＋ ヘボン式ローマ字
- **マヤ暦**: 「銀河のマヤ」流（ホゼ・アグエイアス系のドリームスペル）
- **人相**: 麻衣相法
- **手相**: 西洋手相術 ＋ 日本手相術の標準項目

### 高精度の秘密

西洋占星術・インド占星術・四柱推命・宿曜は、計算が複雑で自前実装が不安定になりやすいため、
[senjutsu.jp](https://www.senjutsu.jp/horoscope) の高精度JSONを活用します。

ユーザーは初回セットアップ時に**1回だけ**自分のブラウザで出生図JSONをダウンロードし、
プラグインに渡すだけ。以降の鑑定はこのJSONを使い回します。
このサイトは IAE 2021 Lahiri / Astronomy Engine / Meeus を使った client-side JavaScript 計算で、
**個人利用そのもの**にあたります。プラグイン自体が senjutsu.jp に直接アクセスすることはありません。

## インストール

```bash
# まだprivateなのでcloneで:
git clone https://github.com/yokoyamactw-max/Shimei-wo-Shiru
cd Shimei-wo-Shiru

# Pythonライブラリ
pip3 install --user --break-system-packages lunar-python PyYAML

# Node.js (Puppeteer)
npm install
```

将来的にmarketplace公開後は:
```
/plugin marketplace add catchtheweb/Shimei-wo-Shiru
/plugin install shimei-wo-shiru
```

## 使い方

```bash
/kantei-setup     # 初回のみ。氏名・生年月日などを登録、senjutsu.jpのJSON取得
/kantei           # フル鑑定書を生成（PNG/PDF/HTML）
/kantei-daily     # 当日のバイオリズムと運勢の短文鑑定
```

## 鑑定書の構成（A4 5ページ）

```
表紙          四神印章付きの和風意匠（codex-image-genで生成）
第一章        鑑定の総論（ヘッドライン + 命の本質200字）
第二章        使命と道筋（使命3〜5項目 + 天賦の才3〜5項目）
第三章        行動と戒め（取り組むべきこと5項目 + 避けるべき罠3項目）
第四章        各占術所見（11〜13占術のカード）
第五章        人生の山場 + 当日のバイオリズム + ラッキー要素 + 結びの一文
```

## プライバシー方針

- `profile/kantei-profile.md`（個人情報を含む）と `input/`（写真・senjutsu.jp JSON）は**git管理外**
- 出力 `output/` も同様
- Vision鑑定（人相・手相）は **明示同意（vision_consent: true）** が必要
- 写真は鑑定実行中だけ Claude API へ送信、保存はローカルのみ
- 配布版に含まれるのはテンプレートと共通ロジックのみで、個人情報は混入しません

## 必要な環境

| 要素 | バージョン |
|---|---|
| Claude Code | 最新版 |
| Python | 3.10+ |
| Node.js | 20+ |
| 主要Pythonライブラリ | lunar-python, PyYAML |
| Codex CLI（任意） | 装飾画像生成用、ChatGPT Plus契約があれば追加課金なし |

## アーキテクチャ

```
/kantei
  └─ kantei-orchestrate
       ├─ kantei-collect-context    （Obsidian/memory要約）
       ├─ kantei-engine             （11占術計算）
       │    ├─ parse_senjutsu.py    （senjutsu.jp JSONから5占術抽出）
       │    └─ seimei/shibun/sanmei/numerology/kyusei/biorhythm/maya
       ├─ kantei-vision  ← オプトイン （顔・手の写真からninsou/tesou）
       ├─ kantei-integrate          （kanteishi subagentで統合）
       └─ kantei-render             （Puppeteer で PNG/PDF/HTML）
```

## ディレクトリ構造

```
Shimei-wo-Shiru/
├── .claude-plugin/plugin.json
├── README.md / LICENSE / CLAUDE.md
├── commands/                # /kantei, /kantei-setup, /kantei-daily
├── agents/                  # kanteishi（鑑定師）, ninsou（観相師）, tesou（手相師）
├── skills/                  # 6スキル
├── tools/                   # 占術計算スクリプト + Puppeteerレンダラ
├── data/                    # 画数辞書、Unihanデータ
├── templates/               # PDF/PNG用HTMLテンプレ
├── profile/                 # ユーザー個人化（gitignore）
├── input/                   # senjutsu.jp JSONや写真（gitignore）
└── output/                  # 生成された鑑定書（gitignore）
```

## ライセンス

MIT License — `LICENSE` 参照。

`data/kakusu_unihan.json` は Unicode Consortium の Unihan データベース (UCD) から派生し、
Unicode License に従います。

## 作者

横山直広 / [株式会社キャッチザウェブ](https://catchtheweb.co.jp)
