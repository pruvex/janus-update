---
description: Production release workflow - build, package and publish installer (Diamond-Release-Guard)
---

## Production Release Steps (Diamond-Release-Guard)

This workflow runs all steps automatically. If any step fails, it stops and reports the error.

### Phase 0: Git Integration & Versioning (CRITICAL GATE)

// turbo
0.1 Switch to master branch:
   ```bash
   git checkout master
   ```
   ❌ **If this fails:** STOP. Cannot proceed with release from wrong branch.

// turbo
0.2 Merge develop with --no-ff:
   ```bash
   git merge --no-ff develop -m 'Release update'
   ```
   ❌ **If this fails (merge conflict):** STOP. Resolve conflicts manually before retrying.

// turbo
0.3 Bump version (patch):
   ```bash
   npm version patch
   ```
   ❌ **If this fails:** STOP. Version bump failed.

// turbo
0.4 Sync backend version:
   ```bash
   npm run write-version
   ```
   ❌ **If this fails:** STOP. Backend version sync failed.

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

### Phase 5: Post-Release Cleanup

// turbo
7. Switch back to develop branch:
   ```bash
   git checkout develop
   ```
   ❌ **If this fails:** Manual intervention required to restore workflow state.

## Expected Outcome

- ✅ **Success:** All checks pass, build completes, installer is uploaded to GitHub releases with proper title and release notes.
- ❌ **Failure:** Workflow stops at the first failing step with clear error message. Fix the issue and retry.
