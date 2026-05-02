#!/usr/bin/env python3
"""バイオリズム計算。

身体23/感情28/知性33/直感38日周期。
出生日からの経過日数を周期で割った正弦値（-1〜+1）で当日値を表す。
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from datetime import date, datetime, timezone
from pathlib import Path

TOOL_VERSION = "0.1.0"

CYCLES = {
    "physical": 23,
    "emotional": 28,
    "intellectual": 33,
    "intuitive": 38,
}

LABELS_JA = {
    "physical": "身体",
    "emotional": "感情",
    "intellectual": "知性",
    "intuitive": "直感",
}


def _trend(value: float, prev: float) -> str:
    if value > prev + 0.01:
        return "上昇"
    if value < prev - 0.01:
        return "下降"
    return "横ばい"


def compute(birth: date, target: date) -> dict:
    days = (target - birth).days
    today = {}
    yesterday = {}
    forecast_days = []
    for k, period in CYCLES.items():
        v_today = math.sin(2 * math.pi * days / period)
        v_yest = math.sin(2 * math.pi * (days - 1) / period)
        today[k] = {
            "value": round(v_today, 4),
            "percent": round(v_today * 100, 1),
            "trend": _trend(v_today, v_yest),
            "label": LABELS_JA[k],
            "period": period,
        }
        yesterday[k] = round(v_yest, 4)

    for offset in range(-15, 16):
        d = days + offset
        forecast_days.append({
            "offset": offset,
            "physical": round(math.sin(2 * math.pi * d / 23), 4),
            "emotional": round(math.sin(2 * math.pi * d / 28), 4),
            "intellectual": round(math.sin(2 * math.pi * d / 33), 4),
            "intuitive": round(math.sin(2 * math.pi * d / 38), 4),
        })

    summary_parts = []
    for k, v in today.items():
        sign = "+" if v["value"] >= 0 else ""
        summary_parts.append(f"{v['label']}{sign}{int(v['percent'])}%")
    summary = " / ".join(summary_parts)

    return {
        "module": "biorhythm",
        "label": "バイオリズム",
        "source": "self-compute",
        "summary": summary,
        "details": {
            "birth_date": birth.isoformat(),
            "target_date": target.isoformat(),
            "days_since_birth": days,
            "today": today,
            "forecast_31d": forecast_days,
        },
        "key_findings": [],
        "compute_meta": {
            "tool_version": TOOL_VERSION,
            "computed_at": datetime.now(timezone.utc).astimezone().isoformat(),
        },
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True, help="subject.json")
    ap.add_argument("--target", help="target date YYYY-MM-DD (default: today)")
    args = ap.parse_args()

    subject = json.loads(Path(args.input).read_text(encoding="utf-8"))
    birth = date.fromisoformat(subject["birth_date"])
    target = date.fromisoformat(args.target) if args.target else date.today()

    json.dump(compute(birth, target), sys.stdout, ensure_ascii=False, indent=2)
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
