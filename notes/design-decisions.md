# Modern Clean design decisions

## Family rules

- Modern Clean is a theme family, not a single YAML file.
- Variants such as Light and Dark should share typography, geometry, dashboard chrome rules, and plugin overrides.
- Variant files should contain palette/backdrop/chart differences and genuine variant exceptions only.
- Shared plugin overrides apply to all variants unless explicitly documented otherwise.

## Current approved Light conventions

- Clean, plain, soft grey/light surfaces.
- Ubuntu for UI text; Ubuntu Mono for monospace/code.
- Dashboard chrome uses uppercase labels/titles/controls where appropriate.
- Status/source badges favour readability over compact defaults.
- Site-wide square corners.
- Sidebar theme switcher label displays as two lines: `Modern Clean` and `(Light)`.

## Safety boundary

Theme work belongs in this repository. Live dashboard theme files are deployment targets. Hermes Agent core files are out of scope unless upstream dashboard product work is explicitly intended.
