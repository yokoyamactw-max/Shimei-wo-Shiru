#!/usr/bin/env python3
"""senjutsu.jp の horoscope JSON を、各占術モジュール形式に分解する。

usage:
    python parse_senjutsu.py --input <horoscope.json> --module <astrology|vedic|shichu|shukuyo|sanmei_meishiki>

出力:
    stdout に各モジュールの統一フォーマットJSONを書き出す。
    出力スキーマは skills/kantei-engine/SKILL.md 参照。
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

TOOL_VERSION = "0.1.0"

NAKSHATRA_TO_SHUKUYO_27 = [
    "昴", "畢", "觜", "参", "井", "鬼", "柳",
    "星", "張", "翼", "軫", "角", "亢", "氐",
    "房", "心", "尾", "箕", "斗", "女", "虚",
    "危", "室", "壁", "奎", "婁", "胃",
]


def _meta(now: datetime) -> dict:
    return {
        "tool_version": TOOL_VERSION,
        "computed_at": now.isoformat(),
    }


def parse_astrology(data: dict, now: datetime) -> dict:
    src = data["western_tropical_placidus"]
    return {
        "module": "astrology",
        "label": "西洋占星術",
        "source": "senjutsu.jp",
        "summary": f"AC {src['ascDeg']:.1f}° / MC {src['mcDeg']:.1f}° / アスペクト{len(src['aspects'])}本",
        "details": {
            "method": src.get("method"),
            "longitudes": src["lons"],
            "asc": src["ascDeg"],
            "mc": src["mcDeg"],
            "houses": src["houses"],
            "house_cusps": src["cusps"],
            "aspects": src["aspects"],
            "transit_aspects": src.get("transitAspects", []),
            "transit_lons": src.get("transitLons", {}),
        },
        "key_findings": [],
        "compute_meta": _meta(now),
    }


def parse_vedic(data: dict, now: datetime) -> dict:
    src = data["vedic_sidereal_lahiri"]
    return {
        "module": "vedic",
        "label": "インド占星術（シデリアル・ラヒリ）",
        "source": "senjutsu.jp",
        "summary": f"ラグナ星座 {src['lagnaRashiIdx']} / 主要ヨーガ {len(src.get('yogas', []))}個",
        "details": {
            "ayanamsha": src["ayanamshaDeg"],
            "sidereal_longitudes": src["siderealLons"],
            "lagna": src["lagnaSid"],
            "lagna_rashi_idx": src["lagnaRashiIdx"],
            "houses": src["houses"],
            "nakshatras": src["nakshatras"],
            "bodies_by_rashi": src["bodiesByRashi"],
            "dasha": src["dasha"],
            "ashtakavarga": src["ashtakavarga"],
            "shadbala": src["shadbala"],
            "dignities": src["dignities"],
            "retrogrades": src["retrogrades"],
            "yogas": src.get("yogas", []),
        },
        "key_findings": [y.get("name") for y in src.get("yogas", []) if y.get("name")],
        "compute_meta": _meta(now),
    }


def parse_shichu(data: dict, now: datetime) -> dict:
    """四柱推命（定気法を採用）。

    senjutsu.jp の各柱は {gz: int, gzStr: '乙酉'} 形式。
    gzStr の1文字目が天干、2文字目が地支。
    """
    src = data["sizhu_bazi"]["dingqi"]

    def gz_pair(pillar: dict) -> dict:
        gz = pillar.get("gzStr", "")
        return {
            "stem": gz[0] if len(gz) >= 1 else "",
            "branch": gz[1] if len(gz) >= 2 else "",
            "gz": pillar.get("gz"),
            "gz_str": gz,
        }

    year_p = gz_pair(src["year"])
    month_p = gz_pair(src["month"])
    day_p = gz_pair(src["day"])
    hour_p = gz_pair(src["hour"])

    summary = (
        f"年柱{year_p['gz_str']} 月柱{month_p['gz_str']} "
        f"日柱{day_p['gz_str']} 時柱{hour_p['gz_str']} "
        f"({src['dayWuxing']}・{src['dayYinyang']})"
    )

    return {
        "module": "shichu",
        "label": "四柱推命（定気法）",
        "source": "senjutsu.jp",
        "summary": summary,
        "details": {
            "method": src.get("method"),
            "year": year_p,
            "month": month_p,
            "day": day_p,
            "hour": hour_p,
            "day_stem": src["dayStem"],
            "day_yinyang": src["dayYinyang"],
            "day_wuxing": src["dayWuxing"],
            "kubou": src.get("kubou", []),
            "zoukan_all": src.get("zoukanAll", {}),
            "daiun": src.get("daiun", {}),
            "ryunen": src.get("ryunen", []),
            "current_jieqi": src.get("curJieqi", {}),
            "next_jieqi": src.get("nxtJieqi", {}),
            "days_from_setsuiri": src.get("daysFromSetsuiri"),
        },
        "key_findings": [
            f"日干 {src['dayStem']}（{src['dayWuxing']}・{src['dayYinyang']}）",
        ],
        "compute_meta": _meta(now),
    }


def parse_shukuyo(data: dict, now: datetime) -> dict:
    """宿曜占星術：senjutsu.jp の月ナクシャトラから27宿を導出。"""
    moon = data["vedic_sidereal_lahiri"]["nakshatras"]["Moon"]
    nak_idx = moon.get("nakIdx", moon.get("idx", moon.get("index")))
    pada = moon.get("pada")
    shuku_idx = nak_idx if isinstance(nak_idx, int) and 0 <= nak_idx < 27 else None
    name = NAKSHATRA_TO_SHUKUYO_27[shuku_idx] if shuku_idx is not None else None
    return {
        "module": "shukuyo",
        "label": "宿曜占星術（27宿）",
        "source": "senjutsu.jp+derived",
        "summary": f"本命宿: {name}宿 / パーダ {pada}" if name else "本命宿の判定不能",
        "details": {
            "moon_nakshatra": moon,
            "shuku_27_idx": shuku_idx,
            "shuku_name": name,
            "pada": pada,
        },
        "key_findings": [],
        "compute_meta": _meta(now),
    }


def parse_sanmei_meishiki(data: dict, now: datetime) -> dict:
    """算命学の命式部分のみ。主星・従星は別途 tools/sanmei.py で算出する。"""
    src = data["sizhu_bazi"]["dingqi"]
    pillars = {k: src[k].get("gzStr", "") for k in ("year", "month", "day", "hour")}
    return {
        "module": "sanmei_meishiki",
        "label": "算命学・命式（共通部）",
        "source": "senjutsu.jp",
        "summary": (
            f"年{pillars['year']} 月{pillars['month']} "
            f"日{pillars['day']} 時{pillars['hour']}"
        ),
        "details": {
            "pillars": pillars,
            "day_stem": src["dayStem"],
            "note": "主星・従星(高尾流)は Phase 1.5 で導出予定",
        },
        "key_findings": [],
        "compute_meta": _meta(now),
    }


PARSERS = {
    "astrology": parse_astrology,
    "vedic": parse_vedic,
    "shichu": parse_shichu,
    "shukuyo": parse_shukuyo,
    "sanmei_meishiki": parse_sanmei_meishiki,
}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--input", required=True, help="senjutsu.jp horoscope JSON のパス")
    ap.add_argument("--module", required=True, choices=PARSERS.keys())
    args = ap.parse_args()

    path = Path(args.input)
    if not path.exists():
        print(f"input not found: {path}", file=sys.stderr)
        return 1

    data = json.loads(path.read_text(encoding="utf-8"))
    now = datetime.now(timezone.utc).astimezone()

    result = PARSERS[args.module](data, now)
    json.dump(result, sys.stdout, ensure_ascii=False, indent=2)
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
