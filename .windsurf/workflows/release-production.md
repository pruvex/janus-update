---
description: Production release workflow - build, package and publish installer
---

## Production Release Steps

This workflow runs all steps automatically. If any step fails, it stops and reports the error.

### Phase 1: Pre-Build Verification (GATE)

// turbo
1. Run pre-build verification suite:
   ```bash
   python tools/pre_build_check.py
   ```
   ❌ **If this fails:** STOP. Fix the reported issues before proceeding. The check catches syntax errors, missing dependencies, version mismatches, and path issues before the expensive build starts.

### Phase 2: Release Notes Generation

// turbo
2. Generate release notes from CHANGELOG.md:
   ```bash
   python tools/generate_release_notes.py
   ```
   Creates `RELEASE_NOTES.md` with formatted release notes for GitHub release from CHANGELOG.md.

### Phase 3: Build Pipeline

// turbo
3. Build frontend + sync version:
   ```bash
   npm run build
   ```
   ❌ **If this fails:** Frontend build error. Check Vite output for details.

// turbo
4. Package backend executable:
   ```bash
   python -m PyInstaller janus_backend.spec --clean --noconfirm
   ```
   ❌ **If this fails:** PyInstaller error. Check for missing imports or missing data files.

// turbo
5. Build and publish installer with release notes:
   ```bash
   npm run build-installer -- --publish always
   ```
   electron-builder automatically uses `release_notes.md` for the GitHub release.
   ❌ **If this fails:** Builder or GitHub publish error. Check GH_TOKEN and GitHub repo access.

### Phase 4: Post-Build Verification

// turbo
6. Verify release was published to GitHub releases page with proper title and notes:
   ```bash
   # Open browser to GitHub releases page
   start https://github.com/pruvex/janus-update/releases
   ```

## Expected Outcome

- ✅ **Success:** All checks pass, build completes, installer is uploaded to GitHub releases with proper title and release notes.
- ❌ **Failure:** Workflow stops at the first failing step with clear error message. Fix the issue and retry.
