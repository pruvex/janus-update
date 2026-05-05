const test = require('node:test');
const assert = require('node:assert');
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

const {
  calculateSha256,
  validateDownloadedAsset,
} = require('../../electron/update-security.cjs');

const tempDir = '.';
const validContent = 'Hello, Janus Update!';
const realValidHash = crypto.createHash('sha256').update(validContent).digest('hex');
const realValidSha512Base64 = crypto.createHash('sha512').update(validContent).digest('base64');
const fakeHash = '0000000000000000000000000000000000000000000000000000000000000000';

function createTempFile(content) {
  const fileName = `test-asset-${crypto.randomUUID()}.txt`;
  const filePath = path.join(tempDir, fileName);
  fs.writeFileSync(filePath, content);
  return filePath;
}

function removeFile(filePath) {
  try {
    fs.unlinkSync(filePath);
  } catch {
    // Ignore if file doesn't exist
  }
}

test('calculateSha256 returns correct hex hash', async () => {
  const filePath = createTempFile(validContent);
  try {
    const hash = await calculateSha256(filePath);
    assert.strictEqual(hash, realValidHash);
    assert.strictEqual(hash.length, 64);
  } finally {
    removeFile(filePath);
  }
});

test('validateDownloadedAsset returns valid:true for matching hash', async () => {
  const filePath = createTempFile(validContent);
  try {
    const result = await validateDownloadedAsset({
      assetPath: filePath,
      expectedHash: realValidHash,
    });
    assert.strictEqual(result.valid, true);
    assert.strictEqual(result.actualSha256, realValidHash);
    assert.strictEqual(result.errorCode, undefined);
  } finally {
    removeFile(filePath);
  }
});

test('validateDownloadedAsset returns valid:false with HASH_MISMATCH for wrong hash', async () => {
  const filePath = createTempFile(validContent);
  try {
    const result = await validateDownloadedAsset({
      assetPath: filePath,
      expectedHash: fakeHash,
    });
    assert.strictEqual(result.valid, false);
    assert.strictEqual(result.actualSha256, realValidHash);
    assert.strictEqual(result.errorCode, 'HASH_MISMATCH');
  } finally {
    removeFile(filePath);
  }
});

test('validateDownloadedAsset returns valid:false with ASSET_MISSING for missing file', async () => {
  const missingFilePath = path.join(tempDir, `test-missing-${crypto.randomUUID()}.txt`);
  const result = await validateDownloadedAsset({
    assetPath: missingFilePath,
    expectedHash: realValidHash,
  });
  assert.strictEqual(result.valid, false);
  assert.strictEqual(result.actualSha256, null);
  assert.strictEqual(result.errorCode, 'ASSET_MISSING');
});

test('hash comparison is case-insensitive', async () => {
  const filePath = createTempFile(validContent);
  try {
    const upperCaseHash = realValidHash.toUpperCase();
    const result = await validateDownloadedAsset({
      assetPath: filePath,
      expectedHash: upperCaseHash,
    });
    assert.strictEqual(result.valid, true);
    assert.strictEqual(result.actualSha256, realValidHash);
  } finally {
    removeFile(filePath);
  }
});

test('validateDownloadedAsset returns valid:true for matching sha512 base64 hash', async () => {
  const filePath = createTempFile(validContent);
  try {
    const result = await validateDownloadedAsset({
      assetPath: filePath,
      expectedHash: realValidSha512Base64,
    });
    assert.strictEqual(result.valid, true);
    assert.strictEqual(result.errorCode, undefined);
  } finally {
    removeFile(filePath);
  }
});
