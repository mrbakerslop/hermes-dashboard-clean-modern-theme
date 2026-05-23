#!/usr/bin/env python3
"""Deploy preview copies of built Modern Clean themes to a Hermes Dashboard theme directory.

Preview deployment deliberately does not overwrite production theme files. It copies
`dist/modern-clean-*.yaml` to the target directory with `-preview` filenames and
unique `name:` identifiers so the dashboard picker can show them separately for
testing.
"""
from __future__ import annotations

import argparse
import os
from pathlib import Path
import shutil
import tempfile

import yaml

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


def preview_label(label: str | None, stem: str) -> str:
    base = label or stem.replace("-", " ").title()
    if "preview" in base.lower():
        return base
    return f"{base} Preview"


def make_preview(src: Path, tmpdir: Path, target_dir: Path) -> tuple[Path, Path, str, str]:
    data = yaml.safe_load(src.read_text()) or {}
    if not isinstance(data, dict):
        raise SystemExit(f"{src}: expected YAML mapping")
    original_name = data.get("name") or src.stem
    preview_name = f"{original_name}-preview"
    data["name"] = preview_name
    data["label"] = preview_label(data.get("label"), src.stem)
    data["description"] = (
        (data.get("description") or "").rstrip()
        + "\n\nPreview copy deployed from the Modern Clean theme project; safe to remove."
    )

    out_name = f"{src.stem}-preview{src.suffix}"
    out = tmpdir / out_name
    out.write_text(yaml.safe_dump(data, sort_keys=False, allow_unicode=True), encoding="utf-8")
    return out, target_dir / out_name, str(original_name), preview_name


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--target-dir", help="Hermes Dashboard theme directory")
    parser.add_argument("--dry-run", action="store_true", help="show preview files that would be copied")
    parser.add_argument("--dark-only", action="store_true", help="deploy only dark preview (alias for --only dark)")
    parser.add_argument("--only", choices=["light", "dark"], help="deploy only one variant preview")
    args = parser.parse_args()

    if args.dark_only:
        if args.only:
            raise SystemExit("--dark-only cannot be used with --only")
        args.only = "dark"

    target_dir = resolve_target(args.target_dir)
    themes = sorted(DIST.glob("modern-clean-*.yaml"))
    if args.only:
        themes = [p for p in themes if p.stem.endswith(f"-{args.only}")]
    if not themes:
        raise SystemExit("No matching built themes found under dist/")

    with tempfile.TemporaryDirectory() as td:
        tmpdir = Path(td)
        for src in themes:
            preview_src, dst, original_name, preview_name = make_preview(src, tmpdir, target_dir)
            if args.dry_run:
                status = "update" if dst.exists() else "create"
                print(f"DRY-RUN {status}: {src.name} ({original_name}) -> {dst.name} ({preview_name})")
            else:
                shutil.copy2(preview_src, dst)
                print(f"preview deployed: {dst} ({preview_name})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
