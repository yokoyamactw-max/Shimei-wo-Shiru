#!/usr/bin/env python3
"""Unihan データベースから kTotalStrokes を取り込んで data/kakusu_unihan.json を作る。

usage:
    # まず Unihan.zip を /tmp にダウンロード
    curl -sL https://www.unicode.org/Public/UCD/latest/ucd/Unihan.zip -o /tmp/Unihan.zip
    unzip -o /tmp/Unihan.zip Unihan_IRGSources.txt -d /tmp/

    python3 tools/build_kakusu.py --input /tmp/Unihan_IRGSources.txt --output data/kakusu_unihan.json

注意:
- kTotalStrokes は新字体（簡体字含む）の画数。日本の康熙字典準拠流派では
  別途 data/kakusu_overrides.json で旧字体への補正を行う。
- 同じ漢字に複数の値（J/T/etc）がコンマ区切りで入る場合は最初の値を採用。
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", default="/tmp/Unihan_IRGSources.txt")
    ap.add_argument("--output", default="data/kakusu_unihan.json")
    args = ap.parse_args()

    table: dict[str, int] = {}
    with open(args.input, encoding="utf-8") as f:
        for line in f:
            if line.startswith("#") or not line.strip():
                continue
            parts = line.rstrip().split("\t")
            if len(parts) != 3:
                continue
            cp_str, key, value = parts
            if key != "kTotalStrokes":
                continue
            # 'U+3400' → int → chr
            try:
                cp = int(cp_str.replace("U+", ""), 16)
            except ValueError:
                continue
            ch = chr(cp)
            # 値: '5' or '5,6'（日本/中国差異）。最初を採用
            try:
                stroke = int(value.split(",")[0].strip())
            except ValueError:
                continue
            table[ch] = stroke

    out = {
        "_meta": {
            "source": "Unicode Unihan kTotalStrokes",
            "note": "新字体ベースの画数。康熙字典補正は data/kakusu_overrides.json で行う",
            "count": len(table),
        },
        "table": table,
    }

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"wrote {out_path}: {len(table)} chars", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
