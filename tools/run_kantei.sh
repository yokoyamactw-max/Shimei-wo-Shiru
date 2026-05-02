#!/usr/bin/env bash
# /kantei コマンドの計算層。orchestrate スキルが内部で呼ぶ。
# Step 1〜3 (取り込み・自前計算・集約) を担当。
# Step 4 (統合)・Step 5 (レンダリング) は Claude Code 側から呼ぶ。
#
# 使い方:
#   tools/run_kantei.sh <subject.json> <senjutsu.json> <workdir>

set -euo pipefail

SUBJECT=${1:?subject.json required}
SENJUTSU=${2:?senjutsu.json required}
WORKDIR=${3:?workdir required}
REPO_ROOT=$(cd "$(dirname "$0")/.." && pwd)

mkdir -p "$WORKDIR"
cp "$SUBJECT" "$WORKDIR/subject.json"

TMPDIR=$(mktemp -d)
trap 'rm -rf "$TMPDIR"' EXIT

PARSE="python3 $REPO_ROOT/tools/parse_senjutsu.py --input $SENJUTSU"

echo "[kantei-engine] senjutsu.jp 取り込み..." >&2
$PARSE --module astrology       > "$TMPDIR/astrology.json"
$PARSE --module vedic           > "$TMPDIR/vedic.json"
$PARSE --module shichu          > "$TMPDIR/shichu.json"
$PARSE --module shukuyo         > "$TMPDIR/shukuyo.json"
$PARSE --module sanmei_meishiki > "$TMPDIR/sanmei_meishiki.json"

echo "[kantei-engine] 自前計算..." >&2
python3 "$REPO_ROOT/tools/seimei.py"     --input "$SUBJECT" > "$TMPDIR/seimei.json"
python3 "$REPO_ROOT/tools/numerology.py" --input "$SUBJECT" > "$TMPDIR/numerology.json"
python3 "$REPO_ROOT/tools/kyusei.py"     --input "$SUBJECT" > "$TMPDIR/kyusei.json"
python3 "$REPO_ROOT/tools/biorhythm.py"  --input "$SUBJECT" > "$TMPDIR/biorhythm.json"
python3 "$REPO_ROOT/tools/maya.py"       --input "$SUBJECT" > "$TMPDIR/maya.json"
python3 "$REPO_ROOT/tools/shibun.py"     --input "$SUBJECT" > "$TMPDIR/shibun.json"   || echo '{"module":"shibun","error":true}' > "$TMPDIR/shibun.json"
python3 "$REPO_ROOT/tools/sanmei.py"     --input "$SUBJECT" --senjutsu "$SENJUTSU" > "$TMPDIR/sanmei.json"

echo "[kantei-engine] modules.json 集約..." >&2
SUBJECT_FILE="$SUBJECT" TMPDIR="$TMPDIR" WORKDIR="$WORKDIR" python3 <<'PYEOF'
import json, os
tmp = os.environ["TMPDIR"]
workdir = os.environ["WORKDIR"]
with open(os.environ["SUBJECT_FILE"], encoding="utf-8") as f:
    subject = json.load(f)
modules = {}
errors = []
keys = ["astrology","vedic","shichu","shukuyo","sanmei_meishiki",
        "seimei","numerology","kyusei","biorhythm","maya",
        "shibun","sanmei"]
for k in keys:
    p = f"{tmp}/{k}.json"
    try:
        with open(p, encoding="utf-8") as f:
            modules[k] = json.load(f)
    except Exception as e:
        errors.append({"module": k, "error": str(e)})

# sanmei_meishiki は内部用の中間データなので、最終的には sanmei が上書き
if "sanmei" in modules and "sanmei_meishiki" in modules:
    del modules["sanmei_meishiki"]

agg = {"subject": subject, "modules": modules, "errors": errors}
with open(f"{workdir}/modules.json", "w", encoding="utf-8") as f:
    json.dump(agg, f, ensure_ascii=False, indent=2)
print(f"[kantei-engine] wrote {workdir}/modules.json: {len(modules)} modules, {len(errors)} errors")
PYEOF

echo "[kantei-engine] 完了。次は agents/kanteishi で統合してください。" >&2
echo "$WORKDIR/modules.json"
