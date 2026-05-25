---
name: janus-build-release
description: Build, package, verify, and optionally publish Janus releases through the Diamond release gate. Use after final audit and documentation update when the user asks to build, package, create installers, validate release artifacts, generate update manifests, publish GitHub releases, verify published assets, or rehearse a release build.
---

# Janus Build Release

## Purpose

Use this skill only for Janus build, packaging, release artifact verification, and GitHub release publishing.

This is a release gate, not an implementation skill. It may run build and verification commands, generate release notes, generate manifests, and publish only after explicit approval.

## Hard Rules

- Do not implement features, fixes, architecture changes, or refactors in this skill.
- Do not bump versions. Version bump belongs to `janus-documentation-update`.
- Do not publish unless Final Audit is `PASS` or `PASS WITH FIXES`, documentation update is complete, and Git checkpoint is complete.
- Do not publish from `develop`; production publish must go through the release branch/`master` protocol in `janus-git-governance`.
- Do not publish from a dirty working tree.
- Do not publish without showing target repository, version, installer path, manifest path, SHA256, and validation summary.
- Do not publish without the exact user approval phrase: `Publish: YES`.
- Do not push to `origin`, create tags, merge branches, or publish GitHub releases without explicit user approval.
- Do not run Vision test suites by default. For Vision-relevant releases, stop and ask approval for the exact Vision command.
- Stop on the first blocking release failure and report the failed gate.

## Modes

| User intent | Mode | Allowed branch |
| --- | --- | --- |
| "Can we release?" | `RELEASE_READINESS` | `develop` or `master` |
| "Build only / dry run" | `BUILD_REHEARSAL` | usually `develop` |
| "Prepare production release" | `PRODUCTION_PREP` | `develop` then `master` via git governance |
| "Publish release" | `PUBLISH` | `master` only |
| "Verify published release" | `POST_PUBLISH_VERIFY` | `master` preferred |

## Required Inputs

Bind or infer:

- Final Audit result and path.
- Documentation update result and path.
- Git checkpoint evidence after documentation update.
- Current version from root `package.json`.
- Release intent: dry-run/build-only or real production publish.
- Whether the release is Vision-related.

If any production publish input is missing, stop with `RELEASE BLOCKED`.

## Low-Cost Failure Lookup

Do not read `WHAT_I_LEARNED.md` during the normal successful path. If a build, manifest, publish, or verification step fails, search only targeted keys from the failure output, such as:

- `electron-builder`
- `manifest`
- `package-lock`
- `version`
- `PyInstaller`
- `GH_TOKEN`
- `release asset`
- exact error text

Apply a learned fix only when it directly matches the current failure.

## Gate 1: Preconditions

For production publishing, verify:

- Final Audit: `PASS` or `PASS WITH FIXES`.
- `janus-documentation-update`: complete.
- Git checkpoint after documentation update: complete and pushed to `backup`.
- `CHANGELOG.md` or release notes source updated.
- Current branch and dirty state are compatible with the requested mode.

Run the helper script for local metadata checks:

```powershell
python C:\Users\pruve\.codex\skills\janus-build-release\scripts\validate_release_readiness.py --repo C:\KI\Janus-Projekt --mode rehearsal
```

Use `--mode publish` only during production publish preparation.

## Gate 2: Version And Metadata

Verify root release metadata:

```powershell
node -e "const fs=require('fs'); const pkg=JSON.parse(fs.readFileSync('package.json','utf8')); const lock=JSON.parse(fs.readFileSync('package-lock.json','utf8')); const backend=fs.readFileSync('backend/version.py','utf8'); console.log({root:pkg.version, lock:lock.version, lockRoot:lock.packages[''].version, backend}); if(lock.version!==pkg.version || lock.packages[''].version!==pkg.version || !backend.includes(pkg.version)) process.exit(1);"
```

If versions are inconsistent, stop and route to `janus-documentation-update`.

## Gate 3: Pre-Build Verification

Run:

```powershell
python tools/pre_build_check.py
```

For Electron/update releases, also consider:

```powershell
node --test tests/electron/update-state.test.cjs tests/electron/update-security.test.cjs tests/electron/update-manager.test.cjs
npx playwright test tests/e2e/auto-update.spec.js
```

Run Vision tests only after explicit approval with the exact command, duration/cost expectation, and reason.

## Gate 4: Build Rehearsal

Build in this order:

```powershell
npm run build
python -m PyInstaller janus_backend.spec --clean --noconfirm
npm run build-installer -- --publish never
```

The current `package.json` also provides:

```powershell
npm run build-all
```

Prefer the stepwise commands when diagnosing failures. Use the aggregate command only when prior gates are clean and the user wants a compact run.

## Gate 5: Manifest Validation

Generate and verify the auto-update manifest:

```powershell
npm run generate:update-manifest
npm run verify:update-artifacts
```

Validate manually if needed:

```powershell
node -e "const fs=require('fs'); const path=require('path'); const pkg=JSON.parse(fs.readFileSync('package.json','utf8')); const m=JSON.parse(fs.readFileSync('release/janus-update-manifest.json','utf8')); if(m.version!==pkg.version) throw new Error('manifest version mismatch'); if(!fs.existsSync(path.join('release',m.assetName))) throw new Error('manifest asset missing'); if(!/^[a-f0-9]{64}$/.test(m.sha256)) throw new Error('invalid sha256'); if(typeof m.critical!=='boolean') throw new Error('critical must be boolean'); if(Number.isNaN(Date.parse(m.createdAt))) throw new Error('invalid createdAt'); console.log('manifest OK', m);"
```

Do not claim auto-update readiness unless the manifest and installer asset are both valid.

## Gate 6: Publish Approval

Before publishing, output:

```text
PUBLISH APPROVAL REQUIRED
- Repository:
- Version:
- Installer:
- Manifest:
- SHA256:
- Release notes:
- Validation summary:
- Required answer: Publish: YES
```

Stop and wait. Any other answer means `RELEASE NOT PUBLISHED`.

## Gate 7: Publish

After explicit approval, use the repository's publish path:

```powershell
npm run release:guard
node scripts/publish_to_github.cjs
```

If using `electron-builder` publish directly:

```powershell
npm run build-installer -- --publish always
```

Confirm whether `janus-update-manifest.json` was uploaded as a GitHub release asset. If not, report `RELEASE PUBLISHED WITH RISK`.

## Gate 8: Post-Publish Verification

Run:

```powershell
npm run release:verify-published
```

Verify:

- GitHub release/tag exists for the current version.
- Installer asset exists.
- Manifest asset exists.
- GitHub asset sizes and SHA256 match local release artifacts.
- Published release evidence exists under `documentation/release/`.

## Model And Context Guidance

- Use `5.4 mini`, low/medium, for readiness checks, metadata validation, and dry-run planning.
- Use `5.3 codex`, medium/high, for build failures and local script/package debugging.
- Use `5.4`, medium/high, for release readiness decisions and ambiguous artifact risk.
- Use `5.5`, high, for production publish approval review, security-sensitive updater risk, or rollback decisions.
- Prefer a new chat for `PUBLISH` and `POST_PUBLISH_VERIFY`; bind only release audit evidence, version, git status, manifest, installer, and release scripts.

## Output Format

```text
RELEASE RESULT: SUCCESS | RELEASE NOT PUBLISHED | RELEASE BLOCKED | RELEASE PUBLISHED WITH RISK
- Mode:
- Version:
- Branch:
- Final Audit:
- Documentation Update:
- Git Checkpoint:
- Version Consistency:
- Pre-Build:
- Build:
- Manifest:
- Publish Approval:
- Published Release:
- Artifacts:
- Remaining Risks:
- Next Skill:
- Model Recommendation:
```
