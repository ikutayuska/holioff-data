#!/usr/bin/env python3
"""Generate per-region holiday JSON files from the `holidays` library.

Usage:
    python3 -m venv .venv && .venv/bin/pip install -r Tools/requirements.txt
    .venv/bin/python Tools/generate_holidays.py --out Alarm/HolidayData --years 2025-2028

The same output is both bundled with the app and uploaded to the CDN
(`holidays/v1/<REGION>.json` and `holidays/v1/index.json`).
"""
import argparse
import datetime as dt
import json
import os
import sys

import holidays

SCHEMA_VERSION = 1


def lang_code(lang: str) -> str:
    """Map the library's locale ids to the keys the app looks up.

    'en_US' -> 'en', 'zh_CN' -> 'zh-Hans', 'zh_TW' -> 'zh-Hant', 'pt_BR' -> 'pt-BR', 'pt_PT' -> 'pt'.
    """
    base, _, region = lang.partition("_")
    if base == "zh":
        return "zh-Hant" if region in ("TW", "HK", "MO") else "zh-Hans"
    if base == "pt" and region == "BR":
        return "pt-BR"
    return base


def collect(country: str, subdiv, years, categories, languages, default_language):
    """Return {(date, type, default_name): names_by_lang} for one country/subdivision."""
    result = {}
    for category in categories:
        base = holidays.country_holidays(country, subdiv=subdiv, years=years, categories=(category,))
        translated = {}
        for lang in languages:
            try:
                translated[lang] = holidays.country_holidays(
                    country, subdiv=subdiv, years=years, categories=(category,), language=lang
                )
            except Exception:
                pass
        for date, joined in base.items():
            # Several holidays on one date are joined with "; " in the same order in every language.
            default_names = joined.split("; ")
            parts_by_lang = {lang: inst.get(date, "").split("; ") for lang, inst in translated.items()}
            for idx, default_name in enumerate(default_names):
                names = {}
                for lang, parts in parts_by_lang.items():
                    if idx < len(parts) and parts[idx]:
                        names[lang_code(lang)] = parts[idx]
                names.setdefault(lang_code(default_language), default_name)
                result[(date.isoformat(), category, default_name)] = names
    return result


def build_region(code: str, years, generated: str, wanted_languages):
    probe = holidays.country_holidays(code)
    # "workday" marks substitute working days, never days off.
    categories = tuple(c for c in (probe.supported_categories or ("public",)) if c != "workday") or ("public",)
    default_language = probe.default_language or "en"
    # Keep the region's own language plus the languages the app ships with.
    languages = tuple(
        lang for lang in (probe.supported_languages or ())
        if lang == default_language or lang.partition("_")[0] in wanted_languages
    )
    subdivisions = sorted(probe.subdivisions)
    aliases = {}
    for alias, sub in (getattr(probe, "subdivisions_aliases", {}) or {}).items():
        aliases.setdefault(sub, alias)

    national = collect(code, None, years, categories, languages, default_language)
    entries = {key: {"names": names, "subdivisions": None} for key, names in national.items()}
    for sub in subdivisions:
        try:
            local = collect(code, sub, years, categories, languages, default_language)
        except Exception as exc:  # pragma: no cover - defensive
            print(f"  skip {code}-{sub}: {exc}", file=sys.stderr)
            continue
        for key, names in local.items():
            if key in national:
                continue
            entry = entries.setdefault(key, {"names": names, "subdivisions": []})
            if entry["subdivisions"] is not None:
                entry["subdivisions"].append(sub)

    holidays_out = []
    for (date, category, default_name), entry in sorted(entries.items()):
        item = {"date": date, "type": category, "names": entry["names"]}
        if entry["subdivisions"]:
            item["subdivisions"] = entry["subdivisions"]
        holidays_out.append(item)

    return {
        "schema": SCHEMA_VERSION,
        "region": code,
        "generated": generated,
        "defaultLanguage": lang_code(default_language),
        "years": list(years),
        "subdivisions": {sub: aliases.get(sub, sub) for sub in subdivisions},
        "holidays": holidays_out,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True)
    parser.add_argument("--years", default=None, help="e.g. 2025-2028 (default: last year .. +2)")
    parser.add_argument("--regions", default=None, help="comma separated ISO codes (default: all)")
    parser.add_argument("--languages", default="en,ja,zh,ko,de,fr,es,pt,it", help="translations to keep besides the region's own")
    args = parser.parse_args()

    today = dt.date.today()
    if args.years:
        start, end = (int(x) for x in args.years.split("-"))
    else:
        start, end = today.year - 1, today.year + 2
    years = list(range(start, end + 1))

    supported = holidays.list_supported_countries(include_aliases=False)
    codes = sorted(c for c in supported if len(c) == 2)
    if args.regions:
        codes = [c for c in args.regions.upper().split(",") if c in supported]

    os.makedirs(args.out, exist_ok=True)
    generated = today.isoformat()
    index = []
    for code in codes:
        try:
            data = build_region(code, years, generated, set(args.languages.split(',')))
        except Exception as exc:
            print(f"skip {code}: {exc}", file=sys.stderr)
            continue
        with open(os.path.join(args.out, f"{code}.json"), "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, separators=(",", ":"))
        index.append({"region": code, "subdivisions": data["subdivisions"], "holidays": len(data["holidays"])})
        print(f"{code}: {len(data['holidays'])} entries, {len(data['subdivisions'])} subdivisions")

    with open(os.path.join(args.out, "index.json"), "w", encoding="utf-8") as f:
        json.dump({"schema": SCHEMA_VERSION, "generated": generated, "years": years, "regions": index},
                  f, ensure_ascii=False, separators=(",", ":"))
    print(f"wrote {len(index)} regions to {args.out}")


if __name__ == "__main__":
    main()
