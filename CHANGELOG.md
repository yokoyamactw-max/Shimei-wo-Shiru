# Changelog

## [0.1.0] - 2026-05-03 — Private Alpha

初回リリース。13占術 (11 + 任意のVision 2) を統合する鑑定書プラグイン。

### Added

**Phase 1 (MVP)**
- `parse_senjutsu.py`: senjutsu.jp の出生図JSONから5占術抽出（西洋占星術・インド占星術・四柱推命・宿曜・算命学命式）
- 自前計算ツール: `biorhythm.py` / `numerology.py` / `kyusei.py` / `maya.py` / `seimei.py`
- `templates/kantei_pdf.html`: A4 5ページの章立てテンプレ
- `tools/render.js`: Puppeteer で PNG / PDF / HTML 出力
- `tools/run_kantei.sh`: 計算層の orchestration

**Phase 1.5**
- `shibun.py`: 紫微斗数（命宮・身宮・五行局・紫微星・14主星・12宮・四化）
- `sanmei.py`: 算命学（高尾流の十大主星・十二大従星・天中殺）
- `tools/load_profile.py`: profile YAML frontmatter → subject.json builder

**Phase 2 (Vision)**
- `agents/ninsou.md`: 観相師subagent（麻衣相法、倫理ガード入り）
- `agents/tesou.md`: 手相師subagent（西洋＋日本手相術）
- `skills/kantei-vision/SKILL.md`: vision_consent オプトインの動作仕様
- 写真は鑑定中のみ Claude API 送信、ローカル外保存なし

**Phase 3 (Design)**
- `codex-image-gen` で和風表紙背景画像（四神印章・金線枠・雲紋・金箔散らし）
- Noto Serif JP / Shippori Mincho ウェブフォント
- 章扉化（第一〜第五章）

**Phase 1.5+ (Dictionary)**
- `data/kakusu_unihan.json`: Unicode Unihan kTotalStrokes 10万字
- `data/kakusu.json`: 新字体→康熙字典補正テーブル（約60件）
- 「横=16」「縦=17」など伝統流派採用の補正

### Architecture
- 11占術中、5つは senjutsu.jp 流用、6つは自前計算
- Vision鑑定 2つは Claude Vision 経由
- 統合は匿名の鑑定師subagent（agents/kanteishi.md）が担当
