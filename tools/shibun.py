#!/usr/bin/env python3
"""紫微斗数（しびとすう）。

標準的な算出順序：
  1. 旧暦の月・日・時を求める（lunar-python）
  2. 命宮・身宮の所在を地支で導出
  3. 五行局を年干支と命宮地支から決定
  4. 紫微星の位置を五行局と旧暦日から算出
  5. 14主星・四化（化禄・化権・化科・化忌）を配置
  6. 12宮（命宮・兄弟宮・夫妻宮…）を命宮から逆時計回りに配置

主星すべての配置・羊陀火鈴等の補佐星は本実装では割愛し、
14主星と12宮、四化、五行局までを対象とする（基本版）。
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

TOOL_VERSION = "0.1.0"

BRANCHES = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]
STEMS = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]

PALACE_NAMES = [
    "命宮", "兄弟宮", "夫妻宮", "子女宮", "財帛宮", "疾厄宮",
    "遷移宮", "奴僕宮", "官禄宮", "田宅宮", "福徳宮", "父母宮",
]

# 五行局: (年干局法 + 命宮地支) → 局
# 年干: 甲己→0, 乙庚→1, 丙辛→2, 丁壬→3, 戊癸→4
# 命宮地支インデックス(寅=0始まり): 寅卯=0, 辰巳=1, 午未=2, 申酉=3, 戌亥=4, 子丑=5
# 表は紫微斗数全書による
WUXING_BUREAU_TABLE = [
    # 年干組: [寅卯, 辰巳, 午未, 申酉, 戌亥, 子丑]
    ["水二局", "火六局", "木三局", "土五局", "金四局", "水二局"],  # 甲己
    ["金四局", "水二局", "火六局", "木三局", "土五局", "金四局"],  # 乙庚
    ["土五局", "金四局", "水二局", "火六局", "木三局", "土五局"],  # 丙辛
    ["木三局", "土五局", "金四局", "水二局", "火六局", "木三局"],  # 丁壬
    ["火六局", "木三局", "土五局", "金四局", "水二局", "火六局"],  # 戊癸
]

BUREAU_NUM = {"水二局": 2, "木三局": 3, "金四局": 4, "土五局": 5, "火六局": 6}

# 紫微星の所在（五行局 × 旧暦日）→ 紫微星地支（寅=0..丑=11、子からのインデックス）
# 紫微全書算出公式：
#   r = lunar_day mod bureau_num
#   q = lunar_day // bureau_num
#   余りがゼロでなければ、(bureau_num - r) を奇数なら逆行、偶数なら順行で q+1 から動かす
# 簡略実装: 紫微斗数全書算出表の代用として、定石公式を実装する
def ziwei_position(bureau: str, lunar_day: int) -> int:
    """紫微星の地支インデックス(子=0..亥=11)を返す。

    アルゴリズム:
      1. q = lunar_day / bureau_num の整数商, r = lunar_day mod bureau_num
      2. if r == 0: 紫微 = (q-1) 番目の位置を 寅 から起算して順行
         else: 紫微 = (q + something) 位置、(bureau_num - r) を以下の規則で進む
            (bureau_num - r) が奇数なら逆行、偶数なら順行
      この標準公式に従い、寅(=2 in 子=0系)を起点に計算する。
    """
    n = BUREAU_NUM[bureau]
    q, r = divmod(lunar_day, n)
    if r == 0:
        # 商をそのまま使う
        offset = q - 1
        # 寅起点で順行
        return (2 + offset) % 12
    else:
        m = n - r
        # まず q 番目の位置を起点として
        base = (2 + q) % 12  # 寅起点で q 進む
        if m % 2 == 1:
            # 逆行
            return (base - m) % 12
        else:
            # 順行
            return (base + m) % 12


# 紫微星から導く14主星の相対配置
# 紫微の位置を基準に、それぞれが何宮ずれているか（時計回り=+、反時計回り=-）
# 紫微斗数全書による標準配置
# 紫微系: 紫微/天機/太陽/武曲/天同/廉貞
# 天府系: 天府/太陰/貪狼/巨門/天相/天梁/七殺/破軍
# 紫微 → 天機(-1) → 太陽(-3) → 武曲(-4) → 天同(-5) → 廉貞(-8)
# 天府は紫微と対峙する位置（紫微+寅と申を結ぶ軸で対称）。
ZIWEI_GROUP = {
    "紫微": 0, "天機": -1, "太陽": -3, "武曲": -4, "天同": -5, "廉貞": -8,
}


def tianfu_from_ziwei(ziwei_idx: int) -> int:
    """天府は紫微と寅申軸で対称、すなわち (寅+申) - 紫微 を取る。
    寅=2, 申=8, 寅+申=10。
    """
    return (10 - ziwei_idx) % 12


# 天府系は天府を基準に時計回り(順行)で配置
TIANFU_GROUP = {
    "天府": 0, "太陰": 1, "貪狼": 2, "巨門": 3, "天相": 4,
    "天梁": 5, "七殺": 6, "破軍": 10,  # 破軍は天府+10
}


# 四化: 年干 → (化禄, 化権, 化科, 化忌)
SI_HUA = {
    "甲": ("廉貞", "破軍", "武曲", "太陽"),
    "乙": ("天機", "天梁", "紫微", "太陰"),
    "丙": ("天同", "天機", "文昌", "廉貞"),
    "丁": ("太陰", "天同", "天機", "巨門"),
    "戊": ("貪狼", "太陰", "右弼", "天機"),
    "己": ("武曲", "貪狼", "天梁", "文曲"),
    "庚": ("太陽", "武曲", "天府", "天同"),
    "辛": ("巨門", "太陽", "文曲", "文昌"),
    "壬": ("天梁", "紫微", "左輔", "武曲"),
    "癸": ("破軍", "巨門", "太陰", "貪狼"),
}


def life_palace(lunar_month: int, hour_branch: str) -> int:
    """命宮の地支インデックス(子=0..亥=11)を返す。

    寅から旧暦月分を順行し、そこから生まれ時(子=0)分を逆行する。
    """
    h = BRANCHES.index(hour_branch)
    return (2 + (lunar_month - 1) - h) % 12


def body_palace(lunar_month: int, hour_branch: str) -> int:
    """身宮: 寅から月を順行、さらに時を順行（命宮とは時の方向が逆）。"""
    h = BRANCHES.index(hour_branch)
    return (2 + (lunar_month - 1) + h) % 12


def wuxing_bureau(year_stem: str, life_palace_idx: int) -> str:
    # 年干組
    g = year_stem
    if g in ("甲", "己"): row = 0
    elif g in ("乙", "庚"): row = 1
    elif g in ("丙", "辛"): row = 2
    elif g in ("丁", "壬"): row = 3
    else: row = 4  # 戊・癸

    # 命宮地支グループ: 寅卯=0, 辰巳=1, 午未=2, 申酉=3, 戌亥=4, 子丑=5
    bidx = life_palace_idx
    if bidx in (2, 3): col = 0
    elif bidx in (4, 5): col = 1
    elif bidx in (6, 7): col = 2
    elif bidx in (8, 9): col = 3
    elif bidx in (10, 11): col = 4
    else: col = 5  # 子丑

    return WUXING_BUREAU_TABLE[row][col]


def place_main_stars(ziwei_idx: int) -> dict[str, int]:
    """14主星を地支インデックスに配置して返す。"""
    stars = {}
    for name, off in ZIWEI_GROUP.items():
        stars[name] = (ziwei_idx + off) % 12

    tf = tianfu_from_ziwei(ziwei_idx)
    for name, off in TIANFU_GROUP.items():
        stars[name] = (tf + off) % 12

    return stars


def palaces_from_life(life_idx: int) -> dict[str, str]:
    """命宮を起点に12宮を逆時計回り（命宮→兄弟宮→夫妻宮→…）に配置。
    返り値: {"命宮": "申", "兄弟宮": "未", ...}
    """
    out = {}
    for i, name in enumerate(PALACE_NAMES):
        idx = (life_idx - i) % 12
        out[name] = BRANCHES[idx]
    return out


def stars_in_palace(stars: dict[str, int], life_idx: int) -> dict[str, list[str]]:
    """各宮（地支）に在る主星のリストを返す。"""
    palace_to_stars: dict[int, list[str]] = {i: [] for i in range(12)}
    for name, idx in stars.items():
        palace_to_stars[idx].append(name)

    out = {}
    for i, name in enumerate(PALACE_NAMES):
        idx = (life_idx - i) % 12
        out[name] = palace_to_stars[idx]
    return out


def compute(subject: dict) -> dict:
    from lunar_python import Solar  # type: ignore

    if not subject.get("birth_time_known", True):
        return {
            "module": "shibun",
            "label": "紫微斗数",
            "source": "self-compute",
            "summary": "出生時刻不明のため紫微斗数の作成は不可。",
            "details": {"reason": "birth_time_unknown"},
            "key_findings": [],
            "compute_meta": {
                "tool_version": TOOL_VERSION,
                "computed_at": datetime.now(timezone.utc).astimezone().isoformat(),
            },
        }

    y, mo, d = map(int, subject["birth_date"].split("-"))
    h, mi = map(int, subject["birth_time"].split(":"))

    s = Solar.fromYmdHms(y, mo, d, h, mi, 0)
    lunar = s.getLunar()
    ec = lunar.getEightChar()

    lunar_month = lunar.getMonth()
    if lunar_month < 0:
        lunar_month = -lunar_month  # 閏月は絶対値で扱う(暫定)
    lunar_day = lunar.getDay()
    hour_branch = ec.getTimeZhi()
    year_stem = ec.getYearGan()

    life_idx = life_palace(lunar_month, hour_branch)
    body_idx = body_palace(lunar_month, hour_branch)
    bureau = wuxing_bureau(year_stem, life_idx)
    ziwei_idx = ziwei_position(bureau, lunar_day)

    main_stars = place_main_stars(ziwei_idx)
    palaces = palaces_from_life(life_idx)
    stars_per_palace = stars_in_palace(main_stars, life_idx)

    sihua = SI_HUA.get(year_stem, ("?", "?", "?", "?"))
    sihua_dict = {
        "化禄": sihua[0],
        "化権": sihua[1],
        "化科": sihua[2],
        "化忌": sihua[3],
    }

    life_branch = BRANCHES[life_idx]
    main_in_life = stars_per_palace["命宮"]

    summary = (
        f"命宮: {life_branch}({','.join(main_in_life) if main_in_life else '空宮'}) / "
        f"五行局: {bureau} / 紫微星: {BRANCHES[ziwei_idx]}"
    )

    return {
        "module": "shibun",
        "label": "紫微斗数（基本版）",
        "source": "self-compute",
        "summary": summary,
        "details": {
            "lunar_month": lunar_month,
            "lunar_day": lunar_day,
            "hour_branch": hour_branch,
            "year_stem": year_stem,
            "life_palace_branch": life_branch,
            "body_palace_branch": BRANCHES[body_idx],
            "wuxing_bureau": bureau,
            "ziwei_branch": BRANCHES[ziwei_idx],
            "main_stars_position": {k: BRANCHES[v] for k, v in main_stars.items()},
            "twelve_palaces": palaces,
            "stars_per_palace": stars_per_palace,
            "si_hua": sihua_dict,
            "note": "14主星と12宮、四化までの基本版。羊陀火鈴・文昌文曲等の補佐星は次版で対応",
        },
        "key_findings": [
            f"命宮在{life_branch}",
            f"五行局: {bureau}",
            f"四化: 化禄={sihua[0]} / 化権={sihua[1]} / 化科={sihua[2]} / 化忌={sihua[3]}",
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
    json.dump(compute(subject), sys.stdout, ensure_ascii=False, indent=2)
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
