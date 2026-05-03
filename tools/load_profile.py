#!/usr/bin/env python3
"""profile/kantei-profile.md の YAML frontmatter を読み、subject.json を出力するヘルパー。

`/kantei` および `/kantei-setup` コマンドの内部で使う。
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def parse_frontmatter(text: str) -> dict:
    """先頭の `---\n...\n---` ブロックを YAML として読む。"""
    if not text.startswith("---"):
        raise ValueError("kantei-profile.md must start with YAML frontmatter '---'")
    end = text.find("\n---", 3)
    if end < 0:
        raise ValueError("frontmatter end '---' not found")
    fm_text = text[3:end].strip()

    try:
        import yaml  # type: ignore
        return yaml.safe_load(fm_text)
    except ImportError:
        # PyYAML が無い環境向けに最小パーサ。include_modules のリスト形式 + key:value のみ対応
        return _minimal_yaml(fm_text)


def _minimal_yaml(text: str) -> dict:
    out: dict = {}
    current_list_key: str | None = None
    for raw in text.splitlines():
        line = raw.rstrip()
        if not line or line.lstrip().startswith("#"):
            continue
        if line.startswith("  - ") or line.startswith("- "):
            val = line.split("- ", 1)[1].split("#", 1)[0].strip()
            if current_list_key:
                out.setdefault(current_list_key, []).append(val)
            continue
        if ":" in line:
            k, v = line.split(":", 1)
            k = k.strip()
            v = v.split("#", 1)[0].strip()
            if not v:
                current_list_key = k
                continue
            current_list_key = None
            if v.lower() in ("true", "yes"):
                out[k] = True
            elif v.lower() in ("false", "no"):
                out[k] = False
            elif v.startswith('"') and v.endswith('"'):
                out[k] = v[1:-1]
            else:
                try:
                    out[k] = int(v)
                except ValueError:
                    try:
                        out[k] = float(v)
                    except ValueError:
                        out[k] = v
    return out


def _coerce_str(v) -> str:
    """date / datetime オブジェクトでも文字列化する。"""
    if v is None:
        return ""
    if hasattr(v, "isoformat"):
        return v.isoformat()
    return str(v)


def build_subject(profile: dict) -> dict:
    """profile frontmatter → subject.json"""
    return {
        "name_kanji": _coerce_str(profile.get("name_kanji", "")),
        "name_kana": _coerce_str(profile.get("name_kana", "")),
        "name_romaji": _coerce_str(profile.get("name_romaji", "")),
        "birth_date": _coerce_str(profile.get("birth_date", "")),
        "birth_time": _coerce_str(profile.get("birth_time", "12:00")),
        "birth_time_known": bool(profile.get("birth_time_known", True)),
        "birth_place": _coerce_str(profile.get("birth_place", "")),
        "birth_lat": profile.get("birth_lat"),
        "birth_lon": profile.get("birth_lon"),
        "timezone": _coerce_str(profile.get("timezone", "Asia/Tokyo")),
        "gender": _coerce_str(profile.get("gender", "")),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--profile", default="profile/kantei-profile.md")
    ap.add_argument("--out-subject", help="出力する subject.json のパス")
    ap.add_argument("--print-key", help="frontmatter の特定キー値だけを stdout に出す（例: senjutsu_json）")
    args = ap.parse_args()

    p = Path(args.profile)
    if not p.exists():
        print(f"profile not found: {p}", file=sys.stderr)
        print("→ /kantei-setup を先に実行してください", file=sys.stderr)
        return 1

    profile = parse_frontmatter(p.read_text(encoding="utf-8"))

    if args.print_key:
        v = profile.get(args.print_key, "")
        print(v if v is not None else "")
        return 0

    subject = build_subject(profile)
    out = json.dumps(subject, ensure_ascii=False, indent=2)
    if args.out_subject:
        Path(args.out_subject).write_text(out + "\n", encoding="utf-8")
        print(f"wrote {args.out_subject}", file=sys.stderr)
    else:
        print(out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
