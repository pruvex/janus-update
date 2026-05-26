# Auto Update Manifest Contract

## Purpose

Defines the JSON schema for the Janus auto-update manifest. This manifest is generated after every installer build from Electron Builder's `latest.yml` and consumed by the update system for artifact validation.

## JSON Schema

```json
{
  "version": "string",
  "assetName": "string",
  "sha512": "string",
  "critical": "boolean",
  "createdAt": "string (ISO 8601)"
}
```

## Field Definitions

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `version` | string | yes | SemVer of the release, matching `package.json` |
| `assetName` | string | yes | Filename of the installer (e.g. `janus-setup-0.4.17-beta.1.exe`) |
| `sha512` | string | yes | Base64 SHA512 hash copied from Electron Builder `latest.yml` |
| `critical` | boolean | yes | If `true`, the update is treated as critical (blocking modal). Default: `false` |
| `createdAt` | string | yes | ISO 8601 timestamp of manifest generation |

## Validation Rules

- `sha512` must match the root `sha512` value in `release/latest.yml`.
- `version` must match the release tag without leading `v`.
- `assetName` must exist in the `release/` directory at generation time.
- `critical` must be explicitly set to `true` for critical releases. Absence or `false` means normal update.
- Post-publish verification additionally compares GitHub asset SHA256 digests against local artifact SHA256 hashes.

## Example

```json
{
  "version": "0.4.17-beta.1",
  "assetName": "janus-setup-0.4.17-beta.1.exe",
  "sha512": "base64-encoded-electron-builder-sha512",
  "critical": false,
  "createdAt": "2026-05-04T17:30:00.000Z"
}
```

## Output Location

- Generated to: `release/janus-update-manifest.json`

## Generation

Run `npm run generate:update-manifest` after `electron-builder` completes.

Run `npm run verify:update-artifacts` before publishing.

Run `npm run release:verify-published` after publishing to verify GitHub asset size and SHA256 digest parity and write evidence under `documentation/release/`.
