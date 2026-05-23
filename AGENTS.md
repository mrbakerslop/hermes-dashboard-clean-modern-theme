# AGENTS.md — Modern Clean Theme Project

## Scope

This repository is the source of truth for the Modern Clean Hermes Dashboard theme family.

Work here includes:

- Modern Clean Light source theme.
- Modern Clean Dark source theme.
- Future Modern Clean variants.
- Shared typography/layout/chrome rules.
- Shared plugin overrides that must apply to every variant.
- Build, validation, deployment, and visual QA scripts.

## Hard boundaries

- Do not edit Hermes Agent core/dashboard source for theme polish.
- Do not hand-edit live dashboard theme files as the source of truth. Deploy generated files from `dist/` instead.
- Do not store secrets in this repo.
- Do not commit generated cache files, local screenshots, credentials, or machine-specific runtime files.

## Local deployment target

Deployment scripts are intentionally generic. Pass the target theme directory explicitly or set:

```bash
export HERMES_DASHBOARD_THEME_DIR="$HOME/.hermes/dashboard-themes"
```

Then use:

```bash
python3 scripts/deploy-preview.py --dry-run
python3 scripts/deploy.py --dry-run
```

## Variant rules

- Shared changes belong in `shared/`.
- Variant files should contain only metadata, palette/backdrop/chart differences, or explicit exceptions.
- Plugin overrides that should apply to all variants belong under `shared/plugin-overrides/`.
- Rebuild and validate all variants after changing shared files.

## Verification before reporting success

Run:

```bash
python3 scripts/build.py
python3 scripts/validate.py
python3 scripts/deploy-preview.py --target-dir <dashboard-theme-dir> --dry-run
```

`scripts/validate.py` is the release blocker. It must pass after every build because it checks both source composition and generated `dist/` artifacts, including the 32 KiB dashboard CSS cap, separated Light/Dark CSS pipelines, Light-only contrast guards, Dark colour-only invariants, badge/button/header readability, theme-switcher labels, sidebar guards, Kanban layout guards, and Models menu clipping guards.

## Deployment gates

- Implementation work must not deploy to live dashboard theme targets.
- Preview deployment is allowed only through `scripts/deploy-preview.py`, which writes separately named `*-preview.yaml` theme files and `*-preview` theme IDs.
- Production deployment is allowed only through `scripts/deploy.py` after review and approval.
- Keep implementation, review, preview deployment, visual acceptance, and production promotion as separate stages.

See `notes/deployment-workflow.md` for the reusable release process.

Report:

- changed project files
- validation result
- deployment status or dry-run status
- dashboard discovery status, when checked
- whether a browser hard refresh is needed
