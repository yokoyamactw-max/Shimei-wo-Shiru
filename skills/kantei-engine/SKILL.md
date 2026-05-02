---
name: kantei-engine
description: 11占術の計算実行。senjutsu.jp の出生図JSONから取り込めるものは取り込み、自前計算が必要なものは tools/ 配下のPythonスクリプトで並列計算してmodules.jsonに統合する
---

# kantei-engine スキル

11占術の計算実行レイヤー。senjutsu.jp の高精度JSONを最大活用し、
自前計算は精度が安定するもののみに絞る。

## 入力

- `output/[案件]/subject.json`（profileから組み立てた被鑑定者情報）
- `profile/kantei-profile.md` の `senjutsu_json` パス
- `profile/kantei-profile.md` の `include_modules`

## 占術ラインナップと出処

| # | モジュール | ID | 出処 | 主担当 |
|---|---|---|---|---|
| 1 | 姓名判断 | `seimei` | 自前 | `tools/seimei.py` + `data/kakusu.json` (康熙字典固定) |
| 2 | 四柱推命 | `shichu` | senjutsu.jp | `sizhu_bazi.dingqi` を整形 |
| 3 | 紫微斗数 | `shibun` | 自前 | `tools/shibun.py` + `lunar-python` |
| 4 | 西洋占星術 | `astrology` | senjutsu.jp | `western_tropical_placidus` を整形 |
| 5 | インド占星術 | `vedic` | senjutsu.jp | `vedic_sidereal_lahiri` を整形 |
| 6 | 数秘術 | `numerology` | 自前 | `tools/numerology.py`（ピタゴラス式・ヘボン式固定） |
| 7 | 九星気学 | `kyusei` | 自前 | `tools/kyusei.py` |
| 8 | 宿曜占星術 | `shukuyo` | senjutsu.jp流用 | `vedic.nakshatras.Moon` から27宿を導出 |
| 9 | 算命学 | `sanmei` | senjutsu.jp + 自前 | 命式は `sizhu_bazi`、主星・従星は `tools/sanmei.py`（高尾流） |
| 10 | バイオリズム | `biorhythm` | 自前 | `tools/biorhythm.py` |
| 11 | マヤ暦 | `maya` | 自前 | `tools/maya.py`（銀河のマヤ流） |

## 動作フロー

### Step 1. senjutsu.jp JSON 取り込み

1. `profile.senjutsu_json` のパスから JSON を読む
2. 内容と `subject.json` の生年月日・性別が一致するか検証
3. `tools/parse_senjutsu.py` で各占術モジュール形式に分解：
   - `astrology` ← `western_tropical_placidus`
   - `vedic` ← `vedic_sidereal_lahiri`
   - `shichu` ← `sizhu_bazi.dingqi`（定気法を採用）
   - `shukuyo` ← `vedic_sidereal_lahiri.nakshatras.Moon` から27宿テーブル参照で導出
   - `sanmei`（命式部分）← `sizhu_bazi.dingqi` の干支
4. 各モジュールJSONを stdout に書き出し

### Step 2. 自前計算（並列実行）

`include_modules` に含まれる自前モジュールを並列実行：
- `python tools/seimei.py --input subject.json`
- `python tools/shibun.py --input subject.json`
- `python tools/numerology.py --input subject.json`
- `python tools/kyusei.py --input subject.json`
- `python tools/sanmei.py --input subject.json --senjutsu input/horoscope_*.json`（命式を流用）
- `python tools/biorhythm.py --input subject.json`
- `python tools/maya.py --input subject.json`

### Step 3. 集約

すべての結果を `output/[案件]/modules.json` に統合：

```json
{
  "subject": {...},
  "source": {
    "senjutsu_json": "input/horoscope_xxx.json",
    "senjutsu_meta": { "exportedAt": "...", "tool": "..." }
  },
  "modules": {
    "seimei": {...},
    "shichu": {...},
    "shibun": {...},
    "astrology": {...},
    "vedic": {...},
    "numerology": {...},
    "kyusei": {...},
    "shukuyo": {...},
    "sanmei": {...},
    "biorhythm": {...},
    "maya": {...}
  },
  "errors": []
}
```

## 各モジュールの出力スキーマ（共通）

```json
{
  "module": "shichu",
  "label": "四柱推命",
  "source": "senjutsu.jp" | "self-compute",
  "summary": "（80字以内のサマリ）",
  "details": { "（占術固有の構造化データ）": "..." },
  "key_findings": ["...", "..."],
  "compute_meta": {
    "tool_version": "0.1.0",
    "computed_at": "2026-05-03T10:00:00+09:00"
  }
}
```

## 精度方針（重要）

| 項目 | 方針 |
|---|---|
| 姓名判断の画数 | **康熙字典に固定**。新字体は対応する正字体の画数を採用（例: 沢→澤=17画） |
| 数秘術の文字変換 | **ピタゴラス式 + ヘボン式ローマ字**に固定 |
| 算命学の流派 | **高尾義政流**に固定 |
| マヤ暦 | **「銀河のマヤ」流**（ホゼ・アグエイアス系）に固定。古典マヤ暦とは別物と明記 |
| 宿曜の月位置 | senjutsu.jp の シデリアル月ナクシャトラを採用。自前計算しない |
| 出生時間不明 | 時刻依存占術（紫微斗数の時柱、宿曜のパーダ等）は警告つきで省略 |

## 失敗時の振る舞い

- senjutsu.jp JSON 不在 → 中断、`/kantei-setup` を案内
- 単一占術の失敗 → `errors` に記録して続行（鑑定書では「該当占術はスキップ」と明示）
- 全占術が失敗 → 中断してエラー表示
- `--rerun` 指定時は既存 modules.json を無視して全再計算

## 実装メモ

- 並列度は CPU コア数まで（`xargs -P` または GNU parallel）
- 各自前スクリプトは `--input <subject.json>` を受け、stdout に JSON を吐く CLI
- `tools/parse_senjutsu.py` は senjutsu.jp スキーマのバージョン変更に備え、
  `_meta.tool` と `_meta.exportedAt` を確認してから処理
