# Shared Modern Clean theme layer

Put rules here when they should apply to every Modern Clean variant.

Recommended split:

- `tokens.yaml` — shared typography/layout/chrome tokens once extracted.
- `chrome-overrides.css` — global dashboard chrome selectors shared by all variants.
- `plugin-overrides/*.css` — plugin-specific rules that should build into every variant.

Current state: the live Modern Clean Light theme has been imported as the initial source of truth in `variants/light.yaml`. The first refactor task should extract genuinely shared CSS/tokens from that variant into this directory, then make Light and future Dark variants consume the shared layer.
