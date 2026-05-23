#!/usr/bin/env python3
"""Deploy built Modern Clean themes to a Hermes Dashboard theme directory."""
from __future__ import annotations

import argparse
import os
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
ENV_TARGET = "HERMES_DASHBOARD_THEME_DIR"


def resolve_target(value: str | None) -> Path:
    target = value or os.environ.get(ENV_TARGET)
    if not target:
        raise SystemExit(
            f"Missing target directory. Pass --target-dir or set {ENV_TARGET}."
        )
    path = Path(target).expanduser()
    if not path.exists():
        raise SystemExit(f"Theme directory does not exist: {path}")
    if not path.is_dir():
        raise SystemExit(f"Target is not a directory: {path}")
    return path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--target-dir", help="Hermes Dashboard theme directory")
    parser.add_argument("--dry-run", action="store_true", help="show what would be copied")
    args = parser.parse_args()

    target_dir = resolve_target(args.target_dir)
    themes = sorted(DIST.glob("modern-clean-*.yaml"))
    if not themes:
        raise SystemExit("No built themes found under dist/")

    for src in themes:
        dst = target_dir / src.name
        if args.dry_run:
            status = "update" if dst.exists() else "create"
            print(f"DRY-RUN {status}: {src} -> {dst}")
        else:
            shutil.copy2(src, dst)
            print(f"deployed: {src} -> {dst}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
