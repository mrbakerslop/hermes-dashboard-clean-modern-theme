# Plugin overrides

Plugin-specific Modern Clean overrides belong here when they should apply to all variants.

Examples:

- `analytics.css`
- `kanban.css`
- `achievements.css`
- `cronalytics.css`

Rule: do not copy/paste plugin fixes independently into Light and Dark. Add the shared override here, rebuild all variants, then verify each deployed variant.

Workflow:

1. Add one focused `.css` file per plugin or plugin issue. Use a leading comment with the plugin name and the reason for the override; that comment doubles as a stable verification marker.
2. Keep selectors plugin-scoped where practical. Avoid broad dashboard-wide selectors in this directory; shared dashboard chrome belongs in `shared/chrome-overrides.css`.
3. Run `python3 scripts/validate.py`. Validation fails if any non-empty shared plugin override is missing from a composed source variant or generated dist file.
4. Run `python3 scripts/build.py` to regenerate every `dist/modern-clean-*.yaml` file.
5. Verify at least Light and Dark by checking the marker appears in both `dist/modern-clean-light.yaml` and `dist/modern-clean-dark.yaml` before deployment.

Build inclusion rule: `scripts/build.py` loads every non-empty `shared/plugin-overrides/*.css` file in sorted filename order and inserts the combined CSS into every variant's `customCSS` after shared chrome and before variant-specific CSS. Future variants inherit the same plugin overrides automatically as long as they live under `variants/*.yaml`.
