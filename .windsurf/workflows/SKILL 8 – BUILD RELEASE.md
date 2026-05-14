---
description: SWE 1.6 Finaler Build und Release auf Github.
---

# Skill 8 â€“ Build Release (JANUS â€“ AFTER SKILL 7 AND /save)

Use this workflow only after:

```text
/1_Feature-erstellen
â†’ implementation of generated tasks
â†’ SKILL 6 â€“ DIAMANTSTANDARD FINAL AUDIT
â†’ Skill 7 /SKILL 7 â€“ DOKUMENTATIONSUPDATE with automatic version bump
â†’ /save
â†’ /SKILL 8 â€“ BUILD RELEASE
```

Goal:
- Build frontend and backend release artifacts.
- Build the Electron installer.
- Generate and validate the auto-update manifest.
- Publish the release only after explicit user approval.
- Verify the published GitHub release and release assets.

This workflow mutates external state only in the publish phase. Do not publish without explicit approval.

---

## Hard Rules

STRICT PROVIDER ISOLATION: Janus ist ein BYOK-Tool. Implementiere oder erlaube NIEMALS automatische Provider-Fallbacks (z.B. Gemini zu GPT) im Produktcode. Wenn ein Provider-spezifischer Test (z.B. Gemini) fehlschlägt, muss er als Fehler dieses Providers behandelt werden. Ein Ausweichen auf einen anderen Provider zur Fehlerumgehung ist STRENG VERBOTEN.

- Do not run production publish if SKILL 6 was not `PASS` or `PASS WITH FIXES`.
- Do not run production publish if Skill 7 `/SKILL 7 â€“ DOKUMENTATIONSUPDATE` was not completed.
- Do not run production publish if `/save` was not completed after Skill 7.
- Do not publish with a missing or inconsistent version.
- Do not publish with a missing installer artifact.
- Do not publish with a missing or invalid `janus-update-manifest.json`.
- Do not publish without explicit user approval after showing version, artifact, manifest hash, and target repository.
- Do not bump versions in this workflow. Version bump belongs to Skill 7.
- Do not silently ignore build or validation failures.
- Stop on first blocking failure and report the exact failed phase.
- Do not run Vision tests, Vision evaluation matrices, Vision KPI gates, or OpenWorld/Stresstest Vision suites as part of this workflow by default.
- Treat Vision validation as out of scope for build/release unless the current release explicitly changes Vision behavior and the user explicitly approves the Vision test command before it is run.

Allowed safe actions:
- Run pre-build verification.
- Run builds.
- Generate release notes.
- Generate update manifest.
- Validate local artifacts.
- Publish only after explicit user approval.
- Open GitHub release page for manual verification.

Forbidden actions:
- Feature implementation changes.
- Architecture changes.
- Version bump.
- Vision test execution without explicit user approval for a Vision-relevant release.
- Publishing with failed validation.
- Publishing to a different repository than configured without explicit user approval.

---

## Required Inputs

Ask for or infer:

1. Final SKILL 6 result.
2. Skill 7 `/SKILL 7 â€“ DOKUMENTATIONSUPDATE` completion result including version bump report.
3. Target version from root `package.json`.
4. `/save` completion evidence after Skill 7.
5. Whether this is a real production publish or a dry-run/build-only release rehearsal.

If the audit/Skill-7/save evidence is unavailable, stop and ask for it.

---

## Phase 0.5: WHAT_I_LEARNED Lookup on Failure Only (LOW-COST)

Purpose: keep release runs cheap while still reusing known release/build fixes when needed.

Rules:
- Do not read `WHAT_I_LEARNED.md` during a normal successful release path.
- Do not read `WHAT_I_LEARNED.md` fully by default.
- If a gate/build/publish/manifest step fails, extract targeted lookup keys from the failure output.
- Search `WHAT_I_LEARNED.md` only for those keys/tags.
- Read only directly matching pattern blocks.
- Apply a learning only if it directly explains the current failure.

Typical release lookup keys:
- `electron-builder`
- `manifest`
- `package-lock`
- `version`
- `PyInstaller`
- `GH_TOKEN`
- `release asset`
- exact error text from the failed command

---

## Phase 0: Release Preconditions Gate

Verify:

- SKILL 6: `PASS` or `PASS WITH FIXES`
- Skill 7 `/SKILL 7 â€“ DOKUMENTATIONSUPDATE`: complete
- `/save`: complete after Skill 7
- Skill 7 automatic version bump: complete and validated
- `CHANGELOG.md`: updated for the feature/release
- Task file: contains post-implementation audit trail or equivalent

If any required precondition is missing, stop:

```markdown
# RELEASE BLOCKED

## Failed Gate
- [gate name]

## Required Action
- [what to do before rerunning /SKILL 8 â€“ BUILD RELEASE]
```

---

## Phase 1: Version & Metadata Consistency Gate

Inspect:

- Root `package.json`
- Root `package-lock.json`
- `backend/version.py`
- `frontend/package.json` only if it is explicitly part of release versioning
- `CHANGELOG.md`
- `release_notes.md` / generated release notes output, if present

Required checks:

- Root `package.json.version` exists.
- Root `package-lock.json.version` matches root version.
- Root package entry inside `package-lock.json.packages[\"\"].version` matches root version.
- `backend/version.py` matches root version.
- `frontend/package.json` may have independent version if documented; do not force-sync unless project convention says so.
- `CHANGELOG.md` contains a relevant `[Unreleased]` entry.

Recommended command:

```powershell
node -e \"const fs=require('fs'); const pkg=JSON.parse(fs.readFileSync('package.json','utf8')); const lock=JSON.parse(fs.readFileSync('package-lock.json','utf8')); const backend=fs.readFileSync('backend/version.py','utf8'); console.log({root:pkg.version, lock:lock.version, lockRoot:lock.packages[''].version, backend}); if(lock.version!==pkg.version || lock.packages[''].version!==pkg.version || !backend.includes(pkg.version)) process.exit(1);\"
```

Stop if versions are inconsistent.

---

## Phase 2: Pre-Build Verification

// turbo
1. Run pre-build verification suite:

```powershell
python tools/pre_build_check.py
```

If this fails, stop. This check catches syntax errors, missing dependencies, version mismatches, and path issues before the expensive build starts.

Also run targeted validations from `/2_final-audit` or Skill 6 only if they are cheap, release-critical, and directly required for the release being built.

Vision test exclusion:
- Do not run `npm run test:vision:*`, `backend/tests/tools/vision_evaluator.py`, Vision matrix tests, OpenWorld Vision tests, Stresstest Vision tests, or Vision KPI gates during normal Skill 8 release builds.
- Do not infer Vision tests from broad phrases like "targeted validations", "non-regression", "quality gate", or "pre-build verification".
- If Skill 6 mentions Vision tests but the release is not Vision-related, record `Vision validation: skipped as out of scope for Skill 8`.
- If the release is Vision-related, stop before running any Vision command and ask for explicit approval with the exact command, estimated duration/cost, and reason.
- If the user does not explicitly approve, skip Vision tests and continue only with the build/release gates that are actually required for packaging and publishing.

For Electron/update features, recommended:

```powershell
node --test tests/electron/update-state.test.cjs tests/electron/update-security.test.cjs tests/electron/update-manager.test.cjs
npx playwright test tests/e2e/auto-update.spec.js
```

---

## Phase 3: Release Notes Generation

// turbo
2. Generate release notes from `CHANGELOG.md`:

```powershell
python tools/generate_release_notes.py
```

Confirm generated release notes include the current feature/release summary.

---

## Phase 4: Build Pipeline

// turbo
3. Build frontend + sync version:

```powershell
npm run build
```

If this fails, stop and report frontend/build output.

// turbo
4. Package backend executable:

```powershell
python -m PyInstaller janus_backend.spec --clean --noconfirm
```

If this fails, stop and report PyInstaller output.

5. Build Electron installer without publishing first if supported:

```powershell
npm run build-installer -- --publish never
```

If the project cannot build without publishing, stop and ask the user whether to continue with direct publish mode.

---

## Phase 5: Auto-Update Manifest Generation & Validation

6. Generate update manifest:

```powershell
npm run generate:update-manifest
```

Validate `release/janus-update-manifest.json`.

Required manifest checks:

- File exists.
- `version` matches root `package.json.version`.
- `assetName` exists in `release/`.
- `sha256` is exactly 64 lowercase hex characters.
- `critical` is a boolean.
- `createdAt` is a valid ISO timestamp.

Recommended command:

```powershell
node -e \"const fs=require('fs'); const path=require('path'); const pkg=JSON.parse(fs.readFileSync('package.json','utf8')); const m=JSON.parse(fs.readFileSync('release/janus-update-manifest.json','utf8')); if(m.version!==pkg.version) throw new Error('manifest version mismatch'); if(!fs.existsSync(path.join('release',m.assetName))) throw new Error('manifest asset missing'); if(!/^[a-f0-9]{64}$/.test(m.sha256)) throw new Error('invalid sha256'); if(typeof m.critical!=='boolean') throw new Error('critical must be boolean'); if(Number.isNaN(Date.parse(m.createdAt))) throw new Error('invalid createdAt'); console.log('manifest OK', m);\"
```

If manifest validation fails, stop.

---

## Phase 6: Publish Approval Gate

Before publishing, present:

```markdown
# PUBLISH APPROVAL REQUIRED

## Target
- **Repository:** [configured GitHub repo]
- **Version:** [package.json version]

## Artifacts
- **Installer:** [release/*.exe]
- **Manifest:** release/janus-update-manifest.json
- **SHA256:** [manifest sha256]
- **Release notes:** [release_notes.md or generated output]

## Validation Summary
- **Pre-build:** PASS
- **Build frontend:** PASS
- **PyInstaller:** PASS
- **Installer build:** PASS
- **Manifest validation:** PASS

## Required Answer
- `Publish: YES`
- or `Publish: NO`
```

Stop and wait for the user.

If the user answers `Publish: NO`, stop with `RELEASE NOT PUBLISHED`.

---

## Phase 7: Publish Release

After explicit approval, publish.

Preferred publish command if artifacts were already built:

```powershell
npm run build-installer -- --publish always
```

Important:
- Confirm whether `janus-update-manifest.json` is included as a release asset by `electron-builder`.
- If not included automatically, upload it manually or report a blocking release risk.
- Do not claim auto-update readiness unless the manifest is available as a release asset.

If publish fails, stop and report likely causes:

- missing `GH_TOKEN`
- GitHub repo access
- duplicate version/tag
- network failure
- electron-builder config issue

---

## Phase 8: Post-Publish Verification

// turbo
Open GitHub releases page:

```powershell
start https://github.com/pruvex/janus-update/releases
```

Verify:

- Release/tag exists for current version.
- Installer asset exists.
- Manifest asset exists.
- Release notes are correct.
- Manifest `assetName` matches uploaded installer.
- Manifest SHA256 matches local installer hash.

If any item is missing, report `RELEASE PUBLISHED WITH RISK`.

---

## Final Report

Return:

```markdown
# RELEASE RESULT: SUCCESS | RELEASE NOT PUBLISHED | RELEASE BLOCKED | RELEASE PUBLISHED WITH RISK

## Version
- **Version:** [version]

## Gates
- **/2_final-audit or Skill 6:** PASS | PASS WITH FIXES | missing
- **Skill 7 /SKILL 7 â€“ DOKUMENTATIONSUPDATE:** complete | missing
- **Skill 7 automatic version bump:** PASS | FAIL
- **/save after Skill 7:** complete | missing
- **Version consistency:** PASS | FAIL
- **Pre-build:** PASS | FAIL
- **Vision validation:** skipped | explicitly approved | not applicable
- **Build:** PASS | FAIL
- **Manifest:** PASS | FAIL
- **Publish approval:** YES | NO

## Artifacts
- **Installer:** [path]
- **Manifest:** [path]
- **SHA256:** [hash]

## Published
- **GitHub release:** [url or not published]
- **Manifest asset:** present | missing | unknown

## Remaining Risks
- **[risk]:** [impact]
- None

## Next Step
- **Recommended:** [manual verification / rollback / announce release / fix issue]
```

## Expected Outcome

- `SUCCESS`: All gates pass, artifacts are built, manifest is valid, release is published and verified.
- `RELEASE NOT PUBLISHED`: User declined publish approval.
- `RELEASE BLOCKED`: A pre-publish gate failed.
- `RELEASE PUBLISHED WITH RISK`: Publish happened but post-publish verification found missing or uncertain release assets.

