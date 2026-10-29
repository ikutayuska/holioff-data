#!/usr/bin/env python3
"""Regenerate the holiday data and replace `v1/` only when the holidays actually changed.

The generator stamps every file with today's date. Keeping the old files when nothing
but that stamp would change means the app only downloads data that is really newer.

Usage: python3 tools/publish.py [--years 2025-2028]
"""
import argparse
import json
import pathlib
import shutil
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent


def without_stamp(path: pathlib.Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    data.pop("generated", None)
    return data


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--years", default="")
    parser.add_argument("--out", default=str(ROOT / "v1"))
    args = parser.parse_args()
    out = pathlib.Path(args.out)

    build = pathlib.Path(tempfile.mkdtemp(prefix="holioff-"))
    cmd = [sys.executable, str(ROOT / "generate_holidays.py"), "--out", str(build)]
    if args.years:
        cmd += ["--years", args.years]
    subprocess.run(cmd, check=True)

    new_files = sorted(p.name for p in build.glob("*.json"))
    old_files = sorted(p.name for p in out.glob("*.json")) if out.exists() else []
    changed = new_files != old_files or any(
        without_stamp(build / name) != without_stamp(out / name) for name in new_files
    )
    if not changed:
        print("holiday data unchanged; keeping the current files")
        return 0

    if out.exists():
        shutil.rmtree(out)
    shutil.copytree(build, out)
    print(f"holiday data updated: {len(new_files)} files written to {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
