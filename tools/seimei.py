#!/usr/bin/env python3
"""姓名判断（康熙字典・五格）。

天格(姓)・人格(姓末+名頭)・地格(名)・外格(姓頭+名末、または総格-人格)・総格(全画数) を算出。
画数は data/kakusu.json (康熙字典基準) を参照。新字体は正字体の画数で登録されている。
辞書未収録の漢字は errors に記録し、該当格の判定は不可とする。
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

TOOL_VERSION = "0.1.0"

# 81霊数の吉凶（簡易版。詳細解釈は agents/kanteishi が行う）
KICHI_KYO = {
    1: "吉", 2: "凶", 3: "吉", 4: "凶", 5: "吉", 6: "吉", 7: "吉", 8: "吉",
    9: "凶", 10: "凶", 11: "吉", 12: "凶", 13: "吉", 14: "凶", 15: "吉", 16: "吉",
    17: "吉", 18: "吉", 19: "凶", 20: "凶", 21: "吉", 22: "凶", 23: "吉", 24: "吉",
    25: "吉", 26: "凶", 27: "凶", 28: "凶", 29: "吉", 30: "凶", 31: "吉", 32: "吉",
    33: "吉", 34: "凶", 35: "吉", 36: "凶", 37: "吉", 38: "吉", 39: "吉", 40: "凶",
    41: "吉", 42: "凶", 43: "凶", 44: "凶", 45: "吉", 46: "凶", 47: "吉", 48: "吉",
    49: "凶", 50: "凶", 51: "凶", 52: "吉", 53: "凶", 54: "凶", 55: "凶", 56: "凶",
    57: "吉", 58: "凶", 59: "凶", 60: "凶", 61: "吉", 62: "凶", 63: "吉", 64: "凶",
    65: "吉", 66: "凶", 67: "吉", 68: "吉", 69: "凶", 70: "凶", 71: "吉", 72: "凶",
    73: "吉", 74: "凶", 75: "凶", 76: "凶", 77: "吉", 78: "凶", 79: "凶", 80: "凶",
    81: "吉",
}

# 三才配置（天格・人格・地格それぞれの末尾数字を五行に変換）
# 1,2=木 / 3,4=火 / 5,6=土 / 7,8=金 / 9,0=水
def to_gogyo(n: int) -> str:
    last = n % 10
    if last in (1, 2): return "木"
    if last in (3, 4): return "火"
    if last in (5, 6): return "土"
    if last in (7, 8): return "金"
    return "水"


def load_dict(repo_root: Path) -> tuple[dict, dict]:
    """補正テーブル(優先) と Unihan(フォールバック) の両方を返す。"""
    overrides_path = repo_root / "data" / "kakusu.json"
    unihan_path = repo_root / "data" / "kakusu_unihan.json"

    overrides = {}
    if overrides_path.exists():
        overrides = json.loads(overrides_path.read_text(encoding="utf-8")).get("table", {})

    unihan = {}
    if unihan_path.exists():
        unihan = json.loads(unihan_path.read_text(encoding="utf-8")).get("table", {})

    return overrides, unihan


def lookup_stroke(ch: str, overrides: dict, unihan: dict) -> int | None:
    """補正テーブル → Unihan の順で画数を引く。"""
    if ch in overrides and isinstance(overrides[ch], int):
        return overrides[ch]
    if ch in unihan and isinstance(unihan[ch], int):
        return unihan[ch]
    return None


def count_strokes(name: str, overrides: dict, unihan: dict) -> tuple[list[int], list[str]]:
    """各文字の画数リストと、辞書未収録文字のリストを返す。"""
    counts = []
    unknown = []
    for ch in name:
        if ch in (" ", "　"):
            continue
        s = lookup_stroke(ch, overrides, unihan)
        if s is not None:
            counts.append(s)
        else:
            counts.append(None)
            unknown.append(ch)
    return counts, unknown


def compute(sei: str, mei: str, overrides: dict, unihan: dict) -> dict:
    sei_counts, sei_unknown = count_strokes(sei, overrides, unihan)
    mei_counts, mei_unknown = count_strokes(mei, overrides, unihan)
    unknown = sei_unknown + mei_unknown

    def safe_sum(xs):
        if any(x is None for x in xs):
            return None
        return sum(xs)

    tenkaku = safe_sum(sei_counts)
    chikaku = safe_sum(mei_counts)
    sokaku = (
        tenkaku + chikaku
        if tenkaku is not None and chikaku is not None
        else None
    )

    # 人格 = 姓の末字 + 名の頭字
    jinkaku = None
    if sei_counts and mei_counts and sei_counts[-1] is not None and mei_counts[0] is not None:
        jinkaku = sei_counts[-1] + mei_counts[0]

    # 外格 = 総格 - 人格 (一文字姓・一文字名は別計算だが今は通常パターンのみ)
    gaikaku = None
    if sokaku is not None and jinkaku is not None:
        gaikaku = sokaku - jinkaku

    def k(n):
        return KICHI_KYO.get(n, "—") if n is not None else "—"

    sansai = None
    if tenkaku is not None and jinkaku is not None and chikaku is not None:
        sansai = f"{to_gogyo(tenkaku)}・{to_gogyo(jinkaku)}・{to_gogyo(chikaku)}"

    findings = []
    if jinkaku is not None:
        findings.append(f"人格 {jinkaku}画 ({k(jinkaku)})")
    if sokaku is not None:
        findings.append(f"総格 {sokaku}画 ({k(sokaku)})")
    if sansai:
        findings.append(f"三才配置 {sansai}")

    summary_parts = []
    for label, val in [("天", tenkaku), ("人", jinkaku), ("地", chikaku), ("外", gaikaku), ("総", sokaku)]:
        summary_parts.append(f"{label}{val if val is not None else '?'}")
    summary = " ".join(summary_parts)

    return {
        "module": "seimei",
        "label": "姓名判断（康熙字典・五格）",
        "source": "self-compute",
        "summary": summary,
        "details": {
            "sei": sei,
            "mei": mei,
            "sei_strokes": sei_counts,
            "mei_strokes": mei_counts,
            "kakuw": {
                "tenkaku": {"value": tenkaku, "kichi": k(tenkaku)},
                "jinkaku": {"value": jinkaku, "kichi": k(jinkaku)},
                "chikaku": {"value": chikaku, "kichi": k(chikaku)},
                "gaikaku": {"value": gaikaku, "kichi": k(gaikaku)},
                "sokaku": {"value": sokaku, "kichi": k(sokaku)},
            },
            "sansai": sansai,
            "unknown_chars": unknown,
        },
        "key_findings": findings,
        "compute_meta": {
            "tool_version": TOOL_VERSION,
            "computed_at": datetime.now(timezone.utc).astimezone().isoformat(),
            "warnings": (
                [f"辞書未収録: {''.join(unknown)}（data/kakusu.json に追加してください）"]
                if unknown else []
            ),
        },
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--repo-root", default=str(Path(__file__).parent.parent))
    args = ap.parse_args()

    subject = json.loads(Path(args.input).read_text(encoding="utf-8"))
    name = subject.get("name_kanji", "").strip()
    if " " in name or "　" in name:
        parts = name.replace("　", " ").split(" ", 1)
        sei, mei = parts[0], parts[1] if len(parts) > 1 else ""
    else:
        sei = name[:1]
        mei = name[1:]

    overrides, unihan = load_dict(Path(args.repo_root))
    json.dump(compute(sei, mei, overrides, unihan), sys.stdout, ensure_ascii=False, indent=2)
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
