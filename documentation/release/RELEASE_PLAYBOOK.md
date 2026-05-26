# Janus Release Playbook (Diamantstandard)

Purpose: Repeatable, low-risk releases with auditable evidence.

## 1) Required Preconditions

- Final audit is `PASS` or `PASS WITH FIXES`.
- Documentation update is complete.
- Git checkpoint after docs exists.
- Version is synchronized:
  - `package.json`
  - `package-lock.json`
  - `backend/version.py`

Blocking rule:
- If any precondition fails, stop release flow.

## 2) Mandatory Two-Checkpoint Rule

1. Checkpoint A: `final audit + documentation sync`.
2. Checkpoint B: `release rehearsal evidence`.

Blocking rule:
- No publish workflow without both checkpoints.

## 3) Rehearsal-First Rule (Always)

Run in this order:

```powershell
python C:\Users\pruve\.codex\skills\janus-build-release\scripts\validate_release_readiness.py --repo C:\KI\Janus-Projekt --mode rehearsal
python C:\KI\Janus-Projekt\tools\pre_build_check.py
npm run build-installer -- --publish never
npm run verify:update-artifacts
```

If terminal encoding fails in pre-build:

```powershell
$env:PYTHONUTF8='1'; python C:\KI\Janus-Projekt\tools\pre_build_check.py
```

Blocking rule:
- Any failed gate stops progression to publish prep.

## 4) Artifact Integrity Rule

After rehearsal, verify:

- Installer exists for current version.
- `release/latest.yml` version equals `package.json` version.
- `release/janus-update-manifest.json` version equals `package.json` version.
- Manifest asset name equals `latest.yml` asset path.
- SHA values are present and consistent.

Blocking rule:
- Version drift or hash mismatch blocks publish prep.

## 5) Publish Safety Rule

Publish is allowed only when all are true:

- Branch policy is satisfied by governance flow.
- Working tree is clean.
- Required release assets are present.
- Explicit human approval phrase is provided:
  - `Publish: YES`

Blocking rule:
- No explicit approval phrase, no publish.

## 6) Evidence-First Rule

Each rehearsal/publish cycle must write a release evidence file under:

- `documentation/release/`

Minimum evidence fields:

- Mode (`BUILD_REHEARSAL`, `PUBLISH`, `POST_PUBLISH_VERIFY`)
- Branch
- Version
- Executed gates + result
- Installer path
- Manifest path
- SHA512
- SHA256
- Final release state (`SUCCESS`, `RELEASE NOT PUBLISHED`, `RELEASE BLOCKED`, `RELEASE PUBLISHED WITH RISK`)

## 7) Post-Publish Verification Rule

If publish occurred, run:

```powershell
npm run release:verify-published
```

Verify:

- Tag/release exists for current version.
- Installer asset exists.
- `latest.yml` exists.
- `janus-update-manifest.json` exists.
- Published asset hashes match local evidence.

Blocking rule:
- Missing or inconsistent published assets => `RELEASE PUBLISHED WITH RISK`.

## 8) Zero-Bypass Principle

- No silent skips.
- No manual "trust me" release.
- No publish from dirty tree.
- No release from incomplete evidence.

Default decision:
- If uncertain, stop and mark `RELEASE BLOCKED`.
