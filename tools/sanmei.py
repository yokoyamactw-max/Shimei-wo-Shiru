#!/usr/bin/env python3
"""算命学（高尾義政流）の主星・従星算出。

入力: 命式（年柱・月柱・日柱・時柱の干支）。
本実装は senjutsu.jp の sizhu_bazi.dingqi を流用するか、
subject.json から birth_date/time でオンザフライ算出する。

出力:
- 陰占の十大主星（年干・月干・時干 → 日干に対する十神 → 算命学の星）
- 十二大従星（日干 × 各地支）
- 天中殺・空亡

陽占（人体図に5主星配置）は本実装では割愛。Phase 2 で追加可。
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

TOOL_VERSION = "0.1.0"

STEMS = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
BRANCHES = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]

# 干の五行と陰陽
STEM_ELEM = {
    "甲": ("木", "陽"), "乙": ("木", "陰"),
    "丙": ("火", "陽"), "丁": ("火", "陰"),
    "戊": ("土", "陽"), "己": ("土", "陰"),
    "庚": ("金", "陽"), "辛": ("金", "陰"),
    "壬": ("水", "陽"), "癸": ("水", "陰"),
}

# 五行相生: 木→火→土→金→水→木
SHENG = {"木": "火", "火": "土", "土": "金", "金": "水", "水": "木"}
# 五行相剋: 木→土, 土→水, 水→火, 火→金, 金→木
KE = {"木": "土", "土": "水", "水": "火", "火": "金", "金": "木"}


def ten_god(day_stem: str, other_stem: str) -> str:
    """日干から見た他の干の十神（比肩/劫財/食神/傷官/偏財/正財/偏官/正官/偏印/印綬）。"""
    de, dy = STEM_ELEM[day_stem]
    oe, oy = STEM_ELEM[other_stem]
    same_yy = (dy == oy)

    # 十神: 同陰陽 = 比肩/食神/正財/正官/印綬、異陰陽 = 劫財/傷官/偏財/偏官/偏印
    if oe == de:  # 同行
        return "比肩" if same_yy else "劫財"
    if SHENG[de] == oe:  # 日干が生じるもの
        return "食神" if same_yy else "傷官"
    if SHENG[oe] == de:  # 日干を生じるもの（=印星）
        return "印綬" if same_yy else "偏印"
    if KE[de] == oe:  # 日干が剋すもの（=財星）
        return "正財" if same_yy else "偏財"
    if KE[oe] == de:  # 日干を剋すもの（=官星）
        return "正官" if same_yy else "偏官"
    return "?"


# 十神 → 算命学の十大主星名
TEN_GOD_TO_SHUSEI = {
    "比肩": "貫索星",
    "劫財": "石門星",
    "食神": "鳳閣星",
    "傷官": "調舒星",
    "偏財": "禄存星",
    "正財": "司禄星",
    "偏官": "車騎星",
    "正官": "牽牛星",
    "偏印": "龍高星",
    "印綬": "玉堂星",
}

# 十二大従星: 日干 × 十二支 → 従星
# 十二大従星の順序（十二運星の対応）:
# 絶=天報星, 胎=天印星, 養=天貴星, 長生=天恍星, 沐浴=天南星, 冠帯=天禄星,
# 建禄=天将星, 帝旺=天堂星, 衰=天胡星, 病=天極星, 死=天庫星, 墓=天馳星
JUSEI_BY_UNSEI = {
    "絶": "天報星", "胎": "天印星", "養": "天貴星",
    "長生": "天恍星", "沐浴": "天南星", "冠帯": "天禄星",
    "建禄": "天将星", "帝旺": "天堂星", "衰": "天胡星",
    "病": "天極星", "死": "天庫星", "墓": "天馳星",
}

# 十二運星表（伝統的な四柱推命の表）
# 行: 日干、列: 支(子=0..亥=11)
# 出典: 標準的な十二運星早見表
UNSEI_TABLE = {
    "甲": ["沐浴","冠帯","建禄","帝旺","衰","病","死","墓","絶","胎","養","長生"],
    "乙": ["病","衰","帝旺","建禄","冠帯","沐浴","長生","養","胎","絶","墓","死"],
    "丙": ["胎","養","長生","沐浴","冠帯","建禄","帝旺","衰","病","死","墓","絶"],
    "丁": ["絶","墓","死","病","衰","帝旺","建禄","冠帯","沐浴","長生","養","胎"],
    "戊": ["胎","養","長生","沐浴","冠帯","建禄","帝旺","衰","病","死","墓","絶"],
    "己": ["絶","墓","死","病","衰","帝旺","建禄","冠帯","沐浴","長生","養","胎"],
    "庚": ["死","墓","絶","胎","養","長生","沐浴","冠帯","建禄","帝旺","衰","病"],
    "辛": ["長生","養","胎","絶","墓","死","病","衰","帝旺","建禄","冠帯","沐浴"],
    "壬": ["帝旺","衰","病","死","墓","絶","胎","養","長生","沐浴","冠帯","建禄"],
    "癸": ["建禄","冠帯","沐浴","長生","養","胎","絶","墓","死","病","衰","帝旺"],
}


def jusei(day_stem: str, branch: str) -> str:
    """十二大従星: 日干 × 地支 → 従星名。"""
    bidx = BRANCHES.index(branch)
    unsei = UNSEI_TABLE[day_stem][bidx]
    return JUSEI_BY_UNSEI[unsei]


# 天中殺（空亡）: 日柱の干支から導出
# 日柱 (甲子〜癸亥の60干支) → 天中殺の地支2つ
def kuubou_from_day(day_stem: str, day_branch: str) -> tuple[str, str]:
    """日柱の干支60組合せから空亡（天中殺）の地支ペアを返す。

    旬（10干支ごとの組）で決まる:
      甲子旬: 戌亥
      甲戌旬: 申酉
      甲申旬: 午未
      甲午旬: 辰巳
      甲辰旬: 寅卯
      甲寅旬: 子丑
    """
    s = STEMS.index(day_stem)
    b = BRANCHES.index(day_branch)
    # 60干支のインデックス: stem=s, branch=bを満たすNを求める
    # N % 10 == s, N % 12 == b → 中国の中国剰余定理
    # シンプル: 0..59 から探索
    N = -1
    for n in range(60):
        if n % 10 == s and n % 12 == b:
            N = n
            break
    if N < 0:
        return ("?", "?")
    # 旬(10ごと)
    jun = N // 10
    KUUBOU = [("戌","亥"),("申","酉"),("午","未"),("辰","巳"),("寅","卯"),("子","丑")]
    return KUUBOU[jun]


def parse_pillars(s: str) -> tuple[str, str]:
    """'乙酉' のような2文字を (天干, 地支) に分解。"""
    if not s or len(s) < 2:
        return ("", "")
    return (s[0], s[1])


def compute(subject: dict, senjutsu_path: str | None = None) -> dict:
    """senjutsu_path が指定されていればそこから命式を読む。
    無ければ lunar-python で算出。"""
    if senjutsu_path and Path(senjutsu_path).exists():
        sj = json.loads(Path(senjutsu_path).read_text(encoding="utf-8"))
        d = sj["sizhu_bazi"]["dingqi"]
        year = d["year"]["gzStr"]
        month = d["month"]["gzStr"]
        day = d["day"]["gzStr"]
        hour = d["hour"].get("gzStr", "")
    else:
        from lunar_python import Solar  # type: ignore
        y, mo, da = map(int, subject["birth_date"].split("-"))
        if subject.get("birth_time_known", True):
            h, mi = map(int, subject["birth_time"].split(":"))
        else:
            h, mi = 12, 0
        s = Solar.fromYmdHms(y, mo, da, h, mi, 0)
        ec = s.getLunar().getEightChar()
        year = ec.getYear()
        month = ec.getMonth()
        day = ec.getDay()
        hour = ec.getTime() if subject.get("birth_time_known", True) else ""

    ystem, ybranch = parse_pillars(year)
    mstem, mbranch = parse_pillars(month)
    dstem, dbranch = parse_pillars(day)
    hstem, hbranch = parse_pillars(hour)

    # 主星: 年干・月干・時干について十大主星
    shusei = {
        "year": TEN_GOD_TO_SHUSEI.get(ten_god(dstem, ystem), "?"),
        "month": TEN_GOD_TO_SHUSEI.get(ten_god(dstem, mstem), "?"),
        "day_self": "貫索星",  # 日干＝自分自身、貫索星扱い
        "hour": TEN_GOD_TO_SHUSEI.get(ten_god(dstem, hstem), "?") if hstem else None,
    }

    # 従星: 日干 × 各地支
    jusei_map = {
        "year": jusei(dstem, ybranch),
        "month": jusei(dstem, mbranch),
        "day": jusei(dstem, dbranch),
        "hour": jusei(dstem, hbranch) if hbranch else None,
    }

    kuubou = kuubou_from_day(dstem, dbranch)

    summary = (
        f"日干{dstem}({STEM_ELEM[dstem][0]}・{STEM_ELEM[dstem][1]}) / "
        f"年主星: {shusei['year']} / 月主星: {shusei['month']} / "
        f"天中殺: {kuubou[0]}{kuubou[1]}"
    )

    return {
        "module": "sanmei",
        "label": "算命学（高尾流・陰占）",
        "source": "self-compute+senjutsu" if senjutsu_path else "self-compute",
        "summary": summary,
        "details": {
            "pillars": {"year": year, "month": month, "day": day, "hour": hour},
            "day_master": {
                "stem": dstem,
                "element": STEM_ELEM[dstem][0],
                "yinyang": STEM_ELEM[dstem][1],
            },
            "shusei_juudai": shusei,
            "jusei_juuni": jusei_map,
            "tenchuusatsu": list(kuubou),
            "note": "陰占（命式の主星・従星）のみ。陽占（人体図5主星）は次版で対応",
        },
        "key_findings": [
            f"日干 {dstem}（{STEM_ELEM[dstem][0]}・{STEM_ELEM[dstem][1]}）",
            f"年主星: {shusei['year']} / 月主星: {shusei['month']}" + (f" / 時主星: {shusei['hour']}" if shusei['hour'] else ""),
            f"日従星: {jusei_map['day']}" + (f" / 時従星: {jusei_map['hour']}" if jusei_map['hour'] else ""),
            f"天中殺: {kuubou[0]}{kuubou[1]}",
        ],
        "compute_meta": {
            "tool_version": TOOL_VERSION,
            "computed_at": datetime.now(timezone.utc).astimezone().isoformat(),
        },
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--senjutsu", help="senjutsu.jp horoscope JSON のパス（あれば命式を流用）")
    args = ap.parse_args()

    subject = json.loads(Path(args.input).read_text(encoding="utf-8"))
    json.dump(compute(subject, args.senjutsu), sys.stdout, ensure_ascii=False, indent=2)
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
