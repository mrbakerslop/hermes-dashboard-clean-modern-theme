# Deployment workflow

This project uses a gated deployment pipeline so implementation work cannot quietly become a live dashboard change.

## Roles

- **Implementation**: edit source files only, then build and validate.
- **Review**: inspect the diff, generated artifacts, and validation output.
- **Preview deployment**: publish preview copies to a chosen Hermes Dashboard theme directory.
- **Visual acceptance**: select the preview theme in the dashboard and confirm the visible result.
- **Production promotion**: copy generated `dist/` files to the live dashboard theme directory after approval.

## Recommended pipeline

1. **Implementation**
   - Edit files under `themes/`, `variants/`, `shared/`, or `scripts/`.
   - Run:
     ```bash
     python3 scripts/build.py
     python3 scripts/validate.py
     ```
   - Do not deploy from implementation work.

2. **Review gate**
   - Inspect project diff.
   - Confirm generated `dist/` files are current.
   - Confirm validation passes.
   - Run preview deployment in dry-run mode:
     ```bash
     python3 scripts/deploy-preview.py --target-dir <dashboard-theme-dir> --dry-run
     ```

3. **Preview deployment**
   - Deploy preview copies only:
     ```bash
     python3 scripts/deploy-preview.py --target-dir <dashboard-theme-dir>
     ```
   - Preview files are written as:
     ```text
     modern-clean-light-preview.yaml
     modern-clean-dark-preview.yaml
     ```
   - Preview theme IDs are suffixed with `-preview`, so they appear separately in the theme picker and do not overwrite live themes.

4. **Visual acceptance**
   - Select the preview theme in the dashboard.
   - Hard refresh the browser if the theme selector does not update immediately.
   - If accepted, explicitly approve production promotion.

5. **Production promotion**
   - Run the production deploy only after approval:
     ```bash
     python3 scripts/deploy.py --target-dir <dashboard-theme-dir>
     ```
   - This updates the real deploy targets from `dist/`.
   - Verify dashboard discovery afterward if the dashboard exposes a theme API.

## Release-card model

If using a task board, represent deployment stages as separate cards:

```text
implementation -> review -> preview deploy -> visual acceptance -> production promote
```

Implementation cards must not run `scripts/deploy.py`.

Preview deploy cards may run `scripts/deploy-preview.py`.

Production promote cards must start blocked and remain blocked until promotion is explicitly approved.

## Useful card templates

### Review gate

```text
review: validate Modern Clean theme release

Review the current Modern Clean theme build as the release gate before any preview deployment.

Acceptance:
1. Run python3 scripts/build.py.
2. Run python3 scripts/validate.py.
3. Run python3 scripts/deploy-preview.py --target-dir <dashboard-theme-dir> --dry-run.
4. Inspect git diff and confirm the change is limited to the intended theme/project files.
5. Confirm no live dashboard theme files were modified by this review card.

Report:
- changed files
- validation result
- dry-run deployment output
- whether preview deployment is ready
```

### Preview deploy

```text
deploy: publish Modern Clean preview themes

Deploy Modern Clean preview themes for visual testing. This card is safe to run only after the review gate passes.

Acceptance:
1. Run python3 scripts/build.py.
2. Run python3 scripts/validate.py.
3. Run python3 scripts/deploy-preview.py --target-dir <dashboard-theme-dir>.
4. Verify the expected preview theme IDs are available in the dashboard.
5. Do not run production deployment.

Report:
- preview files updated
- preview theme IDs
- dashboard discovery result
- refresh note
```

### Production promote

```text
promote: deploy approved Modern Clean theme to live target

Production promotion gate for Modern Clean themes. Only proceed after explicit approval.

Acceptance:
1. Confirm explicit promotion approval is present.
2. Run python3 scripts/build.py.
3. Run python3 scripts/validate.py.
4. Run python3 scripts/deploy.py --target-dir <dashboard-theme-dir> --dry-run.
5. Run python3 scripts/deploy.py --target-dir <dashboard-theme-dir>.
6. Verify the dashboard sees the promoted live theme.

Report:
- production files updated
- validation result
- dashboard discovery result
- refresh note
```
