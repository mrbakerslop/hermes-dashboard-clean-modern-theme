#!/usr/bin/env python3
"""Build deployable Modern Clean theme YAML files.

Modern Clean now uses separated per-theme CSS pipelines inside one project:

- variants/*.yaml contains theme metadata/tokens.
- themes/light/custom.css is the Light CSS source.
- themes/dark/custom.css is the Dark CSS source.

The build intentionally does not derive Dark from Light and does not append the
legacy shared chrome stack. Each theme owns the CSS it ships, which makes the
Dashboard 32 KiB customCSS cap explicit instead of silently dropping late shared
overrides.
"""
from __future__ import annotations

from pathlib import Path
import copy
import re
import yaml

ROOT = Path(__file__).resolve().parents[1]
VARIANTS_DIR = ROOT / "variants"
THEMES_DIR = ROOT / "themes"
DIST_DIR = ROOT / "dist"
SHARED_THEME = ROOT / "shared" / "tokens.yaml"
MAX_DASHBOARD_CSS = 32 * 1024
VARIANT_TO_DIST = {
    "light.yaml": "modern-clean-light.yaml",
    "dark.yaml": "modern-clean-dark.yaml",
}


def dist_name_for(src: Path) -> str:
    return VARIANT_TO_DIST.get(src.name, f"modern-clean-{src.stem}.yaml")


def load_yaml(path: Path) -> dict:
    data = yaml.safe_load(path.read_text())
    if not isinstance(data, dict):
        raise TypeError(f"Expected mapping in {path}, got {type(data).__name__}")
    return data


def merge_dict(base: dict, override: dict) -> dict:
    out = copy.deepcopy(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(out.get(key), dict):
            out[key] = merge_dict(out[key], value)
        else:
            out[key] = value
    return out


def compact_css(css: str) -> str:
    """Remove formatting-only whitespace from shipped CSS.

    The dashboard serves customCSS under a hard 32 KiB cap. Source CSS stays
    readable in themes/<variant>/custom.css, while the generated dist artifact
    drops indentation and repeated blank lines. Deliberately keep comments and
    selector/property spacing intact because validation uses those marker strings
    to prove critical guards survive before the cap.
    """
    lines = [line.strip() for line in css.splitlines()]
    compacted = "\n".join(lines)
    compacted = re.sub(r"\n{2,}", "\n", compacted)
    return compacted.strip()


def load_theme_css(stem: str) -> str:
    theme_dir = THEMES_DIR / stem
    if not theme_dir.exists():
        raise FileNotFoundError(f"Missing separated theme CSS directory: {theme_dir.relative_to(ROOT)}")

    parts: list[str] = []
    # custom.css is the canonical source; extra numbered/layer files may be added
    # later without reintroducing Light/Dark cross-contamination.
    for path in sorted(theme_dir.glob("*.css")):
        css = path.read_text().strip()
        if css:
            parts.append(css)
    if not parts:
        raise FileNotFoundError(f"No CSS sources found in {theme_dir.relative_to(ROOT)}")
    return compact_css("\n\n".join(parts))


def compose_variant(src: Path, shared_theme: dict) -> dict:
    variant = load_yaml(src)
    merged = merge_dict(shared_theme, variant)
    css = load_theme_css(src.stem)
    if len(css) > MAX_DASHBOARD_CSS:
        raise ValueError(
            f"{src.stem} CSS exceeds dashboard cap: {len(css)} > {MAX_DASHBOARD_CSS}. "
            "Trim the per-theme source instead of relying on clipped output."
        )
    merged["customCSS"] = css
    return merged


def print_size_report(variants: list[Path]) -> None:
    print("CSS size report:")
    for src in sorted(variants, key=lambda p: (0, p.stem) if p.stem == "light" else (1, p.name)):
        css = load_theme_css(src.stem)
        remaining = MAX_DASHBOARD_CSS - len(css)
        print(f"- {src.stem}: {len(css)} bytes source/served, {remaining} bytes cap headroom")


def main() -> int:
    shared_theme = load_yaml(SHARED_THEME)
    variants = sorted(VARIANTS_DIR.glob("*.yaml"))
    if not variants:
        raise SystemExit("No variants found")

    DIST_DIR.mkdir(exist_ok=True)
    built: list[Path] = []
    ordered_variants = sorted(variants, key=lambda p: (0, p.stem) if p.stem == "light" else (1, p.name))

    for src in ordered_variants:
        merged = compose_variant(src, shared_theme)
        dst = DIST_DIR / dist_name_for(src)
        dst.write_text(
            yaml.safe_dump(
                merged,
                sort_keys=False,
                default_flow_style=False,
                allow_unicode=True,
            )
        )
        built.append(dst.relative_to(ROOT))

    print("Built:")
    for path in built:
        print(f"- {path}")
    print_size_report(ordered_variants)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
