#!/usr/bin/env python3
"""九星気学。

立春切替で本命星を決定し、月命星・傾斜・後天定位を導出する。
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import date, datetime, timezone
from pathlib import Path

TOOL_VERSION = "0.1.0"

# 九星: index 1=一白水星 .. 9=九紫火星
STAR_NAMES = {
    1: ("一白水星", "水", "北", "坎"),
    2: ("二黒土星", "土", "南西", "坤"),
    3: ("三碧木星", "木", "東", "震"),
    4: ("四緑木星", "木", "南東", "巽"),
    5: ("五黄土星", "土", "中央", "中宮"),
    6: ("六白金星", "金", "北西", "乾"),
    7: ("七赤金星", "金", "西", "兌"),
    8: ("八白土星", "土", "北東", "艮"),
    9: ("九紫火星", "火", "南", "離"),
}

# 立春日は年により異なるが、4日固定として運用（厳密には2/3〜2/5）。
# 鑑定上の許容誤差。精密判定が必要なら senjutsu.jp の curJieqi を参照する。
RISSHUN_MONTH = 2
RISSHUN_DAY = 4

# 月命星表: 行=本命星(年), 列=月(2月から始まる節月)
# 出典: 九星気学の月命星表(三元干支術)
# 行 index = 本命星 (1〜9)、列 index 0=2月, 1=3月, ... 11=1月
# ただし算出は規則的なので関数で計算する
def month_star(year_star: int, sekkou_month: int) -> int:
    """節月(2月=1, ..., 1月=12)から月命星を算出。

    規則:
      - 子・卯・午・酉年生まれ(本命星 1,4,7): 2月=八白
      - 寅・巳・申・亥年生まれ(本命星 2,5,8): 2月=二黒
      - 丑・辰・未・戌年生まれ(本命星 3,6,9): 2月=五黄
    """
    base_table = {
        1: 8, 4: 8, 7: 8,
        2: 2, 5: 2, 8: 2,
        3: 5, 6: 5, 9: 5,
    }
    base = base_table[year_star]
    star = base - (sekkou_month - 1)
    while star < 1:
        star += 9
    return star


def sekkou_month(d: date) -> int:
    """節月: 2月=1, 3月=2, ..., 1月=12。
    各月の節入り日(寅月=立春2/4, 卯月=啓蟄3/5...)前後の判定は粗く月初で代用。
    精密判定は senjutsu.jp の curJieqi を後段で参照する。
    """
    m = d.month
    return ((m - 2) % 12) + 1


def honmei(birth: date) -> int:
    """本命星算出。立春前は前年扱い。"""
    y = birth.year
    if (birth.month, birth.day) < (RISSHUN_MONTH, RISSHUN_DAY):
        y -= 1
    digits = sum(int(c) for c in str(y))
    while digits > 10:
        digits = sum(int(c) for c in str(digits))
    star = 11 - digits
    if star <= 0:
        star += 9
    if star > 9:
        star -= 9
    return star


def keisha(year_star: int, month_star_val: int) -> int:
    """傾斜宮 = 月命星が落ちる本命盤の宮。

    本命盤は後天定位盤を本命星が中央に来るように回転させたもの。
    傾斜は月命星の所在宮(=後天定位)を返す。
    定位: 1=北, 2=南西, 3=東, 4=南東, 5=中央, 6=北西, 7=西, 8=北東, 9=南
    """
    return month_star_val


def compute(birth: date) -> dict:
    h = honmei(birth)
    sm = sekkou_month(birth)
    m = month_star(h, sm)
    k = keisha(h, m)

    h_name = STAR_NAMES[h]
    m_name = STAR_NAMES[m]
    k_name = STAR_NAMES[k]

    return {
        "module": "kyusei",
        "label": "九星気学",
        "source": "self-compute",
        "summary": f"本命: {h_name[0]} / 月命: {m_name[0]} / 傾斜: {k_name[3]}宮",
        "details": {
            "honmei": {
                "index": h,
                "name": h_name[0],
                "element": h_name[1],
                "direction": h_name[2],
                "kyu": h_name[3],
            },
            "getsumei": {
                "index": m,
                "name": m_name[0],
                "element": m_name[1],
                "direction": m_name[2],
                "kyu": m_name[3],
            },
            "keisha_kyu": k_name[3],
            "sekkou_month": sm,
            "note": "立春の節入り日は2/4固定で算出。厳密判定は senjutsu.jp の節気を参照",
        },
        "key_findings": [
            f"本命星は{h_name[0]}。{h_name[1]}の気を帯ぶ。",
            f"傾斜は{k_name[3]}宮にあり。",
        ],
        "compute_meta": {
            "tool_version": TOOL_VERSION,
            "computed_at": datetime.now(timezone.utc).astimezone().isoformat(),
        },
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    args = ap.parse_args()

    subject = json.loads(Path(args.input).read_text(encoding="utf-8"))
    birth = date.fromisoformat(subject["birth_date"])
    json.dump(compute(birth), sys.stdout, ensure_ascii=False, indent=2)
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
