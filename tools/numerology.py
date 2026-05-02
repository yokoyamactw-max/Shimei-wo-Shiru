#!/usr/bin/env python3
"""数秘術（ピタゴラス式）。

ヘボン式ローマ字の氏名と生年月日から:
- ライフパスナンバー (生年月日合計)
- ディスティニーナンバー (氏名全体)
- ソウルナンバー (母音のみ)
- パーソナリティナンバー (子音のみ)
- バースデーナンバー (出生日)

を算出する。マスターナンバー(11/22/33)は単純化せず保持する。
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import date, datetime, timezone
from pathlib import Path

TOOL_VERSION = "0.1.0"

PYTHAGOREAN = {
    "A": 1, "B": 2, "C": 3, "D": 4, "E": 5, "F": 6, "G": 7, "H": 8, "I": 9,
    "J": 1, "K": 2, "L": 3, "M": 4, "N": 5, "O": 6, "P": 7, "Q": 8, "R": 9,
    "S": 1, "T": 2, "U": 3, "V": 4, "W": 5, "X": 6, "Y": 7, "Z": 8,
}
VOWELS = set("AEIOU")
MASTER_NUMBERS = {11, 22, 33}

MEANINGS = {
    1: "独立・先駆・始まり。一なる者。",
    2: "協調・受容・対の力。仲立ち。",
    3: "創造・表現・喜び。光を放つ者。",
    4: "堅実・基盤・組織。礎を築く者。",
    5: "自由・変化・冒険。風となる者。",
    6: "調和・愛・責任。守護する者。",
    7: "探究・霊性・孤独。深淵を覗く者。",
    8: "力・成果・物質。築き支配する者。",
    9: "完成・奉仕・普遍。大いなる帰着。",
    11: "霊感・直観・伝達。マスターの数。",
    22: "建築・実現・大成。マスタービルダー。",
    33: "慈愛・献身・癒し。マスターヒーラー。",
}


def reduce_number(n: int) -> int:
    while n > 9 and n not in MASTER_NUMBERS:
        n = sum(int(c) for c in str(n))
    return n


def name_value(name: str, predicate=None) -> int:
    total = 0
    for ch in name.upper():
        if ch.isalpha() and ch in PYTHAGOREAN:
            if predicate is None or predicate(ch):
                total += PYTHAGOREAN[ch]
    return reduce_number(total)


def compute(name_romaji: str, birth: date) -> dict:
    name_clean = "".join(c for c in name_romaji.upper() if c.isalpha() or c == " ")

    life_path = reduce_number(
        sum(int(c) for c in birth.strftime("%Y%m%d"))
    )
    destiny = name_value(name_clean)
    soul = name_value(name_clean, lambda c: c in VOWELS)
    personality = name_value(name_clean, lambda c: c not in VOWELS)
    birthday = reduce_number(birth.day)

    numbers = {
        "life_path": life_path,
        "destiny": destiny,
        "soul": soul,
        "personality": personality,
        "birthday": birthday,
    }

    summary = f"LP{life_path} D{destiny} S{soul} P{personality} B{birthday}"

    return {
        "module": "numerology",
        "label": "数秘術（ピタゴラス式・ヘボン式）",
        "source": "self-compute",
        "summary": summary,
        "details": {
            "name_input": name_romaji,
            "name_normalized": name_clean,
            "birth_date": birth.isoformat(),
            "numbers": numbers,
            "meanings": {k: MEANINGS.get(v, "") for k, v in numbers.items()},
        },
        "key_findings": [
            f"ライフパス {life_path}: {MEANINGS.get(life_path, '')}",
            f"ディスティニー {destiny}: {MEANINGS.get(destiny, '')}",
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
    name = subject.get("name_romaji") or subject.get("name_kana", "")
    if not name:
        print("name_romaji or name_kana required in subject.json", file=sys.stderr)
        return 1
    birth = date.fromisoformat(subject["birth_date"])

    json.dump(compute(name, birth), sys.stdout, ensure_ascii=False, indent=2)
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
