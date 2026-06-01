#!/usr/bin/env python3
"""Validate Modern Clean theme source and generated dist files.

Validation is intentionally aligned with the separated per-theme CSS pipeline:
Light and Dark each own the CSS they ship under themes/<variant>/custom.css.
No theme is allowed to rely on dashboard clipping to hide excess CSS.
"""
from __future__ import annotations

from pathlib import Path
import copy
import re
import sys
import yaml

ROOT = Path(__file__).resolve().parents[1]
REQUIRED_TOP_LEVEL = {"name", "label", "palette", "typography", "layout"}
SHARED_THEME = ROOT / "shared" / "tokens.yaml"
VARIANTS_DIR = ROOT / "variants"
THEMES_DIR = ROOT / "themes"
DIST_DIR = ROOT / "dist"
BUILD_SCRIPT = ROOT / "scripts" / "build.py"
MAX_DASHBOARD_CSS = 32 * 1024


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
    """Mirror build.py's formatting-only compaction for cap checks."""
    lines = [line.strip() for line in css.splitlines()]
    compacted = "\n".join(lines)
    compacted = re.sub(r"\n{2,}", "\n", compacted)
    return compacted.strip()


def load_theme_css(stem: str) -> str:
    theme_dir = THEMES_DIR / stem
    parts: list[str] = []
    if theme_dir.exists():
        for path in sorted(theme_dir.glob("*.css")):
            css = path.read_text().strip()
            if css:
                parts.append(css)
    return compact_css("\n\n".join(parts)) if parts else ""


def compose_from_sources(path: Path) -> dict:
    shared = load_yaml(SHARED_THEME)
    variant = load_yaml(path)
    merged = merge_dict(shared, variant)
    merged["customCSS"] = load_theme_css(path.stem)
    return merged


def validate_theme(data: dict, source: str) -> list[str]:
    errors: list[str] = []
    if not isinstance(data, dict):
        return [f"{source}: expected mapping at top level"]

    missing = sorted(REQUIRED_TOP_LEVEL - set(data))
    if missing:
        errors.append(f"{source}: missing required keys: {', '.join(missing)}")

    name = data.get("name")
    if not isinstance(name, str) or not name.startswith("modern-clean"):
        errors.append(f"{source}: theme name should start with 'modern-clean' (got {name!r})")

    css = data.get("customCSS", "")
    if css is not None and not isinstance(css, str):
        errors.append(f"{source}: customCSS must be a string when present")
    return errors


def validate_separated_pipeline() -> list[str]:
    errors: list[str] = []
    script = BUILD_SCRIPT.read_text()
    forbidden = ["SHARED_CHROME", "dark_safe_light_css", "DARK_CSS_REPLACEMENTS", "shared/plugin-overrides"]
    for needle in forbidden:
        if needle in script:
            errors.append(f"{BUILD_SCRIPT}: build script still references legacy shared/derived pipeline marker {needle!r}")
    for stem in ("light", "dark"):
        css = load_theme_css(stem)
        if not css:
            errors.append(f"{THEMES_DIR / stem}: missing separated CSS source")
        if len(css) > MAX_DASHBOARD_CSS:
            errors.append(f"{THEMES_DIR / stem}: CSS exceeds dashboard cap ({len(css)} > {MAX_DASHBOARD_CSS})")
    return errors


def validate_wordmark_guard(data: dict, source: str) -> list[str]:
    css = (data.get("customCSS") or "")[:MAX_DASHBOARD_CSS]
    required = [
        "Modern Clean protected invariants",
        "Hermes Agent wordmark",
        "body aside > div:first-child .text-midground",
        "text-transform: uppercase !important",
        "font-size: 1.38rem !important",
    ]
    missing = [needle for needle in required if needle not in css]
    return [f"{source}: wordmark guard missing before dashboard cap: {', '.join(missing)}"] if missing else []


def validate_sidebar_footer_guard(data: dict, source: str) -> list[str]:
    css = (data.get("customCSS") or "")[:MAX_DASHBOARD_CSS]
    required = [
        "Sidebar footer version/org",
        "a[href=\"https://nousresearch.com\"]",
        "white-space: nowrap !important",
        "min-width: max-content !important",
        "letter-spacing: 0.12em !important",
    ]
    missing = [needle for needle in required if needle not in css]
    return [f"{source}: sidebar footer no-wrap guard missing before dashboard cap: {', '.join(missing)}"] if missing else []


def validate_sidebar_system_status_guard(data: dict, source: str) -> list[str]:
    css = (data.get("customCSS") or "")[:MAX_DASHBOARD_CSS]
    required = [
        "Sidebar system status: compact no-wrap three-line block",
        "a[href=\"/sessions\"] > div",
        "font-size: 0.56rem !important",
        "white-space: nowrap !important",
        "overflow-wrap: normal !important",
        "word-break: normal !important",
    ]
    missing = [needle for needle in required if needle not in css]
    return [f"{source}: sidebar system status no-wrap guard missing before dashboard cap: {', '.join(missing)}"] if missing else []


def validate_sidebar_nav_density_guard(data: dict, source: str) -> list[str]:
    css = (data.get("customCSS") or "")[:MAX_DASHBOARD_CSS]
    required = [
        "html body aside :is(nav a,nav [role=\"link\"],[role=\"navigation\"] a)",
        "font-size:.8rem!important",
        "line-height:1.2!important",
        "padding-top:.225rem!important",
        "padding-bottom:.225rem!important",
    ]
    missing = [needle for needle in required if needle not in css]
    return [f"{source}: sidebar nav density guard missing before dashboard cap: {', '.join(missing)}"] if missing else []


def validate_button_polarity_guard(data: dict, source: str) -> list[str]:
    css = (data.get("customCSS") or "")[:MAX_DASHBOARD_CSS]
    is_dark = "modern-clean-dark" in str(data.get("name", ""))
    common = ["Button polarity", "html body main :is(button, [role=\"button\"])"]
    required = common + (["background: #141d2b !important", "color: #e6edf5 !important"] if is_dark else ["background: #f3f4f5 !important", "color: #1f2937 !important"])
    errors: list[str] = []
    missing = [needle for needle in required if needle not in css]
    if missing:
        errors.append(f"{source}: button polarity guard missing before dashboard cap: {', '.join(missing)}")
    if is_dark and "background: #f3f4f5 !important" in css:
        errors.append(f"{source}: Dark button polarity still contains Light button background before the CSS cap")
    if not is_dark and "background: #141d2b !important" in css:
        errors.append(f"{source}: Light button polarity contains Dark button background before the CSS cap")
    return errors


def validate_logs_uppercase_guard(data: dict, source: str) -> list[str]:
    css = (data.get("customCSS") or "")[:MAX_DASHBOARD_CSS]
    required = [
        "Logs controls",
        "main div[role=\"toolbar\"]",
        "header[role=\"banner\"] :is(span, label, button, [role=\"button\"])",
        "text-transform: uppercase !important",
    ]
    missing = [needle for needle in required if needle not in css]
    return [f"{source}: Logs uppercase guard missing before dashboard cap: {', '.join(missing)}"] if missing else []


def validate_dashboard_button_casing_guard(data: dict, source: str) -> list[str]:
    css = (data.get("customCSS") or "")[:MAX_DASHBOARD_CSS]
    required = [
        "Dashboard button casing",
        ":is(header,aside,main) :is(button,[role=\"button\"],a[role=\"button\"])",
        "text-transform:uppercase!important",
    ]
    missing = [needle for needle in required if needle not in css]
    return [f"{source}: dashboard button casing guard missing before dashboard cap: {', '.join(missing)}"] if missing else []


def validate_header_status_readability_guard(data: dict, source: str) -> list[str]:
    css = (data.get("customCSS") or "")[:MAX_DASHBOARD_CSS]
    is_dark = "modern-clean-dark" in str(data.get("name", ""))
    required = [
        "Page-header adjacent status",
        "header[role=\"banner\"] h1 + div",
        "font-size: 0.72rem !important",
        "opacity: 1 !important",
    ]
    required += ["color: #e6edf5 !important", "background-color: #151e2c !important"] if is_dark else ["color: #1f2937 !important", "background-color: #eef0f2 !important"]
    missing = [needle for needle in required if needle not in css]
    return [f"{source}: page-header status readability guard missing before dashboard cap: {', '.join(missing)}"] if missing else []


def validate_yellow_badge_guard(data: dict, source: str) -> list[str]:
    css = data.get("customCSS") or ""
    is_dark = "modern-clean-dark" in str(data.get("name", ""))
    if is_dark:
        if "#ffe08a" in css or "modern-clean-light-yellow-badges" in css:
            return [f"{source}: Dark must not include the Light-only yellow badge override"]
        return []
    required = [".hermes-kanban .hermes-kanban-priority", "#ffe08a", "#4a3414"]
    missing = [needle for needle in required if needle not in css[:MAX_DASHBOARD_CSS]]
    return [f"{source}: Light yellow badge guard missing before dashboard cap: {', '.join(missing)}"] if missing else []


def validate_light_cream_contrast_guard(data: dict, source: str) -> list[str]:
    css = (data.get("customCSS") or "")[:MAX_DASHBOARD_CSS]
    is_dark = "modern-clean-dark" in str(data.get("name", ""))
    marker = "Light cream/beige contrast"
    if is_dark:
        return [f"{source}: Dark must not include the Light-only cream/beige contrast override"] if marker in css else []
    required = [marker, "bg-[#ffe6cb]", "rgba(71,85,105,.72)", "text-[#ffe6cb]", "#475569"]
    missing = [needle for needle in required if needle not in css]
    return [f"{source}: Light cream/beige contrast guard missing before dashboard cap: {', '.join(missing)}"] if missing else []


def validate_light_warning_orange_guard(data: dict, source: str) -> list[str]:
    is_dark = "modern-clean-dark" in str(data.get("name", ""))
    warning = (data.get("colorOverrides") or {}).get("warning")
    css = (data.get("customCSS") or "")[:MAX_DASHBOARD_CSS]
    if is_dark:
        errors = []
        if warning != "#e4b16d":
            errors.append(f"{source}: Dark warning colour changed unexpectedly ({warning!r})")
        if "Light warning/orange text contrast" in css or "#7c2d12" in css:
            errors.append(f"{source}: Dark must not include the Light-only warning/orange contrast override")
        return errors
    errors = []
    if warning != "#7c2d12":
        errors.append(f"{source}: Light warning colour should be darker orange #7c2d12 (got {warning!r})")
    required = ["Light warning/orange text contrast", "text-amber-500", "text-warning/50", "text-warning/80", "#7c2d12"]
    missing = [needle for needle in required if needle not in css]
    if missing:
        errors.append(f"{source}: Light warning/orange contrast guard missing before dashboard cap: {', '.join(missing)}")
    return errors


def validate_dashboard_badge_readability_guard(data: dict, source: str) -> list[str]:
    css = (data.get("customCSS") or "")[:MAX_DASHBOARD_CSS]
    is_dark = "modern-clean-dark" in str(data.get("name", ""))
    required = [
        "Dashboard badges/status pills",
        ":is(header,aside,main) span[class*=\"font-compressed\"]",
        "font-size:.68rem!important",
        "text-transform:uppercase!important",
        "span[class*=\"font-compressed\"][class*=\"text-success\"]",
    ]
    required += (
        ["background:#151e2c!important", "color:#e6edf5!important", "color:#63d982!important"]
        if is_dark
        else ["background:#eef0f2!important", "color:#1f2937!important", "color:#1f5a35!important"]
    )
    missing = [needle for needle in required if needle not in css]
    return [f"{source}: dashboard badge readability guard missing before dashboard cap: {', '.join(missing)}"] if missing else []


def validate_models_use_as_menu_guard(data: dict, source: str) -> list[str]:
    css = (data.get("customCSS") or "")[:MAX_DASHBOARD_CSS]
    required = ["Models Use As menu", "data-use-as-menu", "overflow:visible!important", "z-index:80!important"]
    missing = [needle for needle in required if needle not in css]
    return [f"{source}: Models Use As menu clipping guard missing before dashboard cap: {', '.join(missing)}"] if missing else []


def validate_header_search_clear_guard(data: dict, source: str) -> list[str]:
    css = (data.get("customCSS") or "")[:MAX_DASHBOARD_CSS]
    required = [
        "header[role=banner] div:has(input)>button[aria-label][class][class]",
        "position:absolute!important",
        "min-height:0!important",
        "display:none!important",
    ]
    missing = [needle for needle in required if needle not in css]
    return [f"{source}: page-header search clear-button guard missing before dashboard cap: {', '.join(missing)}"] if missing else []


def validate_card_heading_uppercase_guard(data: dict, source: str) -> list[str]:
    css = (data.get("customCSS") or "")[:MAX_DASHBOARD_CSS]
    required = [
        "Card headings: all-caps",
        "html body main [class*=\"bg-card\"] > [class*=\"border-b\"]",
        "html body main .ha-card-title",
        "text-transform:uppercase!important",
    ]
    missing = [needle for needle in required if needle not in css]
    return [f"{source}: card heading uppercase guard missing before dashboard cap: {', '.join(missing)}"] if missing else []


def validate_dark_order(data: dict, source: str) -> list[str]:
    if "modern-clean-dark" not in str(data.get("name", "")):
        return []
    css = (data.get("customCSS") or "")[:MAX_DASHBOARD_CSS]
    errors: list[str] = []
    missing = [needle for needle in ("color-scheme: dark", "MODERN CLEAN\\A(DARK)") if needle not in css]
    if missing:
        errors.append(f"{source}: dark CSS missing before dashboard cap: {', '.join(missing)}")
    if "MODERN CLEAN\\A(LIGHT)" in css:
        errors.append(f"{source}: dark CSS still contains Light theme-switcher label")
    return errors


def validate_css_size(data: dict, source: str) -> list[str]:
    css = data.get("customCSS") or ""
    if len(css) > MAX_DASHBOARD_CSS:
        return [f"{source}: customCSS exceeds dashboard cap ({len(css)} > {MAX_DASHBOARD_CSS})"]
    return []


def run_guards(data: dict, source: str) -> list[str]:
    errors: list[str] = []
    errors.extend(validate_theme(data, source))
    errors.extend(validate_css_size(data, source))
    errors.extend(validate_wordmark_guard(data, source))
    errors.extend(validate_sidebar_footer_guard(data, source))
    errors.extend(validate_sidebar_system_status_guard(data, source))
    errors.extend(validate_sidebar_nav_density_guard(data, source))
    errors.extend(validate_button_polarity_guard(data, source))
    errors.extend(validate_logs_uppercase_guard(data, source))
    errors.extend(validate_dashboard_button_casing_guard(data, source))
    errors.extend(validate_header_status_readability_guard(data, source))
    errors.extend(validate_yellow_badge_guard(data, source))
    errors.extend(validate_light_cream_contrast_guard(data, source))
    errors.extend(validate_light_warning_orange_guard(data, source))
    errors.extend(validate_dashboard_badge_readability_guard(data, source))
    errors.extend(validate_models_use_as_menu_guard(data, source))
    errors.extend(validate_header_search_clear_guard(data, source))
    errors.extend(validate_card_heading_uppercase_guard(data, source))
    errors.extend(validate_dark_order(data, source))
    return errors


def main() -> int:
    variant_paths = sorted(VARIANTS_DIR.glob("*.yaml"))
    dist_paths = sorted(DIST_DIR.glob("*.yaml"))
    if not variant_paths and not dist_paths:
        print("No theme YAML files found under variants/ or dist/", file=sys.stderr)
        return 1

    errors: list[str] = []
    errors.extend(validate_separated_pipeline())

    for path in variant_paths:
        try:
            merged = compose_from_sources(path)
        except Exception as exc:  # noqa: BLE001
            errors.append(f"{path}: failed to compose shared + separated theme CSS ({exc})")
            continue
        errors.extend(run_guards(merged, f"{path} (composed)"))

    for path in dist_paths:
        try:
            data = yaml.safe_load(path.read_text())
        except Exception as exc:  # noqa: BLE001
            errors.append(f"{path}: YAML parse failed: {exc}")
            continue
        errors.extend(run_guards(data, str(path)))

    if errors:
        print("Validation failed:")
        for err in errors:
            print(f"- {err}")
        return 1

    print(f"Validation passed: {len(variant_paths)} source variant(s), {len(dist_paths)} dist file(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
