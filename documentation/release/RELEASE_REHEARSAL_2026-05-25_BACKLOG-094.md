# Release Rehearsal Evidence (BACKLOG-094)

Date: 2026-05-25
Mode: BUILD_REHEARSAL (no publish)
Branch: develop
Version: 0.4.17-beta.38
Related Final Audit: documentation/test-runs/BACKLOG-094_final_audit.md (PASS WITH FIXES)

## Gates Run

1. Release readiness metadata check:
   - Command: `python C:\Users\pruve\.codex\skills\janus-build-release\scripts\validate_release_readiness.py --repo C:\KI\Janus-Projekt --mode rehearsal`
   - Result: PASS WITH WARNINGS (dirty tree, previous manifest drift)

2. Version consistency check:
   - package.json / package-lock.json / backend/version.py
   - Result: PASS (`0.4.17-beta.38` synced)

3. Pre-build verification:
   - Command: `python C:\KI\Janus-Projekt\tools\pre_build_check.py` (rerun with `PYTHONUTF8=1`)
   - Result: PASS (14/14)

4. Installer rehearsal build + manifest verification:
   - Command: `npm run build-installer -- --publish never`
   - Result: PASS
   - Substeps:
     - `electron-builder --publish never`
     - `npm run generate:update-manifest`
     - `npm run verify:update-artifacts`

## Artifact Evidence

- Installer: `release/janus-setup-0.4.17-beta.38.exe`
- latest.yml version: `0.4.17-beta.38`
- Manifest: `release/janus-update-manifest.json`
- Manifest version: `0.4.17-beta.38`
- SHA512:
  - `J1IBuCjCDm6S/O/in/YJGCtBbJ7N/PY8kC0G1Fd5o5jOWigpmUOgkYNhf7crqCvjfNn15ezb42R5L94MlK4q/A==`
- SHA256:
  - `c1b8672804b8665357013568203b0dfe781fb0aaa92ed355c4b7b7645b997193`

## Publish State

- Publish approval phrase received: NO
- Published release: NO
- Canonical result: RELEASE NOT PUBLISHED (rehearsal complete, publish gate not entered)
