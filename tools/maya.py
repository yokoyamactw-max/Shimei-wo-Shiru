#!/usr/bin/env python3
"""マヤ暦（銀河のマヤ流／ホゼ・アグエイアスのドリームスペル）。

注: 本実装は古典マヤ長期暦ではなく、現代日本で流通している
「銀河のマヤ」「ドリームスペル」と呼ばれる体系。
うるう日(2/29)は「時間をはずした日」として KIN を進めない。
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import date, datetime, timezone
from pathlib import Path

TOOL_VERSION = "0.1.0"

SOLAR_SEALS = [
    "赤い龍", "白い風", "青い夜", "黄色い種", "赤い蛇",
    "白い世界の橋渡し", "青い手", "黄色い星", "赤い月", "白い犬",
    "青い猿", "黄色い人", "赤い空歩く人", "白い魔法使い", "青い鷲",
    "黄色い戦士", "赤い地球", "白い鏡", "青い嵐", "黄色い太陽",
]

GALACTIC_TONES = [
    ("磁気", "1：目的を一つに定める"),
    ("月", "2：両極の挑戦"),
    ("電気", "3：奉仕に活力を"),
    ("自己存在", "4：形を定める"),
    ("倍音", "5：力を放射する"),
    ("律動", "6：均衡を組織する"),
    ("共振", "7：内なる調律"),
    ("銀河", "8：調和を体現する"),
    ("太陽", "9：意図を結晶化"),
    ("惑星", "10：完成と顕現"),
    ("スペクトル", "11：解放と創発"),
    ("水晶", "12：協力の結合"),
    ("宇宙", "13：超越と存在"),
]

WAVESPELLS = [
    "赤い龍", "白い魔法使い", "青い手", "黄色い太陽", "赤い空歩く人",
    "白い世界の橋渡し", "青い嵐", "黄色い人", "赤い蛇", "白い鏡",
    "青い猿", "黄色い種", "赤い月", "白い犬", "青い夜",
    "黄色い戦士", "赤い地球", "白い風", "青い鷲", "黄色い星",
]


def is_feb29(d: date) -> bool:
    return d.month == 2 and d.day == 29


def days_skipping_feb29(d_from: date, d_to: date) -> int:
    delta = (d_to - d_from).days
    feb29s = 0
    y = d_from.year
    while y <= d_to.year:
        try:
            f = date(y, 2, 29)
            if d_from <= f <= d_to:
                feb29s += 1
        except ValueError:
            pass
        y += 1
    return delta - feb29s


# 基準: 2013-07-26 = KIN 113（青い律動の猿、ドリームスペル新年に多用される基準）
BASE_DATE = date(2013, 7, 26)
BASE_KIN = 113


def kin_for(d: date) -> int:
    if is_feb29(d):
        return None  # 時間をはずした日
    days = days_skipping_feb29(BASE_DATE, d)
    kin = ((BASE_KIN - 1 + days) % 260) + 1
    return kin


def decompose_kin(kin: int) -> tuple[int, int]:
    """KIN番号 -> (太陽の紋章 index 1-20, 銀河の音 index 1-13)"""
    seal_idx = ((kin - 1) % 20) + 1
    tone_idx = ((kin - 1) % 13) + 1
    return seal_idx, tone_idx


def wavespell_for(kin: int) -> tuple[int, str]:
    """13日サイクルのウェイブスペル開始KIN(1, 14, 27...)から所属ウェイブを返す"""
    ws_idx = ((kin - 1) // 13)
    return ws_idx + 1, WAVESPELLS[ws_idx % 20]


def compute(birth: date, target: date) -> dict:
    if is_feb29(birth):
        return {
            "module": "maya",
            "label": "マヤ暦（銀河のマヤ流）",
            "source": "self-compute",
            "summary": "「時間をはずした日」生まれ。KINを持たない特異日として鑑定する。",
            "details": {"birth_date": birth.isoformat(), "is_day_out_of_time": True},
            "key_findings": [],
            "compute_meta": {
                "tool_version": TOOL_VERSION,
                "computed_at": datetime.now(timezone.utc).astimezone().isoformat(),
            },
        }

    birth_kin = kin_for(birth)
    today_kin = kin_for(target) if not is_feb29(target) else None

    seal_i, tone_i = decompose_kin(birth_kin)
    ws_idx, ws_name = wavespell_for(birth_kin)

    seal_name = SOLAR_SEALS[seal_i - 1]
    tone_name, tone_desc = GALACTIC_TONES[tone_i - 1]

    return {
        "module": "maya",
        "label": "マヤ暦（銀河のマヤ流）",
        "source": "self-compute",
        "summary": f"KIN{birth_kin}: {tone_name}の{seal_name}（音{tone_i}・紋章{seal_i}）",
        "details": {
            "birth_date": birth.isoformat(),
            "target_date": target.isoformat(),
            "birth_kin": birth_kin,
            "today_kin": today_kin,
            "solar_seal": {"index": seal_i, "name": seal_name},
            "galactic_tone": {"index": tone_i, "name": tone_name, "keyword": tone_desc},
            "wavespell": {"index": ws_idx, "name": ws_name},
            "note": "ホゼ・アグエイアス系ドリームスペル準拠。古典マヤ長期暦とは別体系。"
        },
        "key_findings": [
            f"本命KIN: {birth_kin}（{tone_name}の{seal_name}）",
            f"所属ウェイブスペル: {ws_name}",
        ],
        "compute_meta": {
            "tool_version": TOOL_VERSION,
            "computed_at": datetime.now(timezone.utc).astimezone().isoformat(),
        },
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--target", help="default today")
    args = ap.parse_args()

    subject = json.loads(Path(args.input).read_text(encoding="utf-8"))
    birth = date.fromisoformat(subject["birth_date"])
    target = date.fromisoformat(args.target) if args.target else date.today()
    json.dump(compute(birth, target), sys.stdout, ensure_ascii=False, indent=2)
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
