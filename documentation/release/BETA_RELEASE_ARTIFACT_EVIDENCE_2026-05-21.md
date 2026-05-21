# Beta Release Artifact Evidence - 2026-05-21

## Decision

PRE-PUBLISH PASS.

The local build, installer, update manifest and packaged smoke test are complete for `0.4.17-beta.37`. GitHub publishing has not been executed in this evidence record because Skill 8 requires an explicit publish approval after presenting the target, version, artifact and hashes.

## Scope

- Release workflow: `.windsurf/workflows/SKILL 8 - BUILD RELEASE.md`
- Source commit before release-evidence commit: `c69b0f7`
- Version: `0.4.17-beta.37`
- Target repository: `pruvex/janus-update`
- Target release type: GitHub prerelease
- Distribution mechanism: Electron auto-update through GitHub release assets

## Preconditions

| Gate | Result | Evidence |
|---|---:|---|
| Security final beta launch gate | PASS WITH WATCHPOINTS | `documentation/test-results/TEST-RUN-2026-05-21-013_results.json` |
| Category 2 Security & Safety dashboard | PASS | 19/19 validated, 100% pass rate |
| Git working tree before build | PASS | Clean before release notes/evidence changes |
| Version sync | PASS | `package.json`, `package-lock.json`, `backend/version.py` all `0.4.17-beta.37` |
| Release notes content | PASS | `CHANGELOG.md` and `release_notes.md` include Security 09-19 launch-gate summary |

## Build Commands

| Phase | Command | Result |
|---|---|---:|
| Pre-build check | `$env:PYTHONIOENCODING='UTF-8'; python tools\pre_build_check.py` | PASS, 14/14 |
| Release notes | `$env:PYTHONIOENCODING='UTF-8'; python tools\generate_release_notes.py` | PASS |
| Frontend build | `$env:PYTHONIOENCODING='UTF-8'; npm run build` | PASS |
| Backend executable | `$env:PYTHONIOENCODING='UTF-8'; python -m PyInstaller janus_backend.spec --clean --noconfirm` | PASS |
| Electron installer and manifest | `$env:PYTHONIOENCODING='UTF-8'; npm run build-installer` | PASS |
| Independent manifest validation | `node -e "...manifest/latest.yml validation..."` | PASS |
| Packaged smoke test | Start `release\win-unpacked\Janus Projekt.exe`, poll `/api/health`, stop started processes | PASS |

## Artifact Inventory

| Artifact | Path | Size | SHA256 |
|---|---|---:|---|
| Installer | `release/janus-setup-0.4.17-beta.37.exe` | 688266935 bytes | `c7e096ed0cac179ac57bd632f0becc88d4070cdee5db31acb040884c09190b77` |
| Electron latest metadata | `release/latest.yml` | 20328 bytes | `cfe90095a4841a7a9665519ef000b6ba4366661a4201db9f3fb151ae500c7a48` |
| Janus update manifest | `release/janus-update-manifest.json` | 250 bytes | `6e2fcdf98dae028f3ff5a38a4377df7817659a7fa4b70fb35c3968f0323b7104` |

No `.blockmap` artifact was produced for this build because the project configuration has `differentialPackage: false`.

## Update Manifest Validation

| Field | Value |
|---|---|
| Manifest version | `0.4.17-beta.37` |
| Manifest asset | `janus-setup-0.4.17-beta.37.exe` |
| Manifest SHA512 | `0Oa94Ir1oRvJWCTO5ZhLycwuZvp3WmNapK58RiQHFd0j+jbzv4Sv775H8Jb6KhMYLw9p6Fk3XtLNloCc0iOg4Q==` |
| `latest.yml` path | `janus-setup-0.4.17-beta.37.exe` |
| `latest.yml` SHA512 | `0Oa94Ir1oRvJWCTO5ZhLycwuZvp3WmNapK58RiQHFd0j+jbzv4Sv775H8Jb6KhMYLw9p6Fk3XtLNloCc0iOg4Q==` |
| `critical` | `false` |
| `createdAt` | `2026-05-21T14:08:56.589Z` |

Validation result: manifest version matches `package.json`, manifest asset exists, manifest and `latest.yml` agree on asset and SHA512, `critical` is boolean and `createdAt` is a valid timestamp.

## Packaged Smoke Test

| Check | Result |
|---|---:|
| `release\win-unpacked\Janus Projekt.exe` starts | PASS |
| Packaged backend starts from `release\win-unpacked\resources\backend\janus_backend.exe` | PASS |
| `http://127.0.0.1:8001/api/health` reachable | PASS |
| Health status | `ready` |
| Health audio flag | `audio_ready: true` |
| Smoke-test processes cleaned up | PASS |

## Publish Approval Gate

Publishing is intentionally pending.

Required explicit approval before external mutation:

```text
Publish: YES
```

Without that exact approval, do not upload assets or create/update the GitHub release.

## Publish Plan After Approval

Preferred publish command for the already built assets:

```powershell
node scripts/publish_to_github.cjs
```

Expected assets in GitHub release `v0.4.17-beta.37`:

- `janus-setup-0.4.17-beta.37.exe`
- `latest.yml`
- `janus-update-manifest.json`

Post-publish verification must confirm that the published asset names and hashes match this evidence file.

## Remaining Risks

- GitHub publish is not yet executed.
- Formal legal/privacy review remains outside this technical beta release gate.
- Hosted SaaS or public/commercial production release still requires a deployment-bound rerun of the security launch gate.
