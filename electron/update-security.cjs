const crypto = require('crypto');
const fs = require('fs');

function calculateFileHash(filePath, algorithm) {
  return new Promise((resolve, reject) => {
    const hash = crypto.createHash(algorithm);
    const stream = fs.createReadStream(filePath);

    stream.on('data', (chunk) => {
      hash.update(chunk);
    });

    stream.on('end', () => {
      resolve(hash.digest('hex'));
    });

    stream.on('error', (err) => {
      reject(err);
    });
  });
}

function detectHashEncoding(expectedHash) {
  if (!expectedHash || typeof expectedHash !== 'string') {
    return null;
  }
  const trimmed = expectedHash.trim();
  if (/^[a-f0-9]{64}$/i.test(trimmed)) {
    return { algorithm: 'sha256', encoding: 'hex' };
  }
  if (/^[a-f0-9]{128}$/i.test(trimmed)) {
    return { algorithm: 'sha512', encoding: 'hex' };
  }
  // latest.yml from electron-builder stores sha512 in base64.
  if (/^[A-Za-z0-9+/=]+$/.test(trimmed)) {
    return { algorithm: 'sha512', encoding: 'base64' };
  }
  return null;
}

function calculateSha256(filePath) {
  return calculateFileHash(filePath, 'sha256');
}

async function validateDownloadedAsset({ assetPath, expectedHash }) {
  try {
    fs.accessSync(assetPath);
  } catch {
    return { valid: false, actualSha256: null, errorCode: 'ASSET_MISSING' };
  }

  const expected = detectHashEncoding(expectedHash);
  if (!expected) {
    return { valid: false, actualSha256: null, errorCode: 'MISSING_EXPECTED_HASH' };
  }

  const generatedHash = (await calculateFileHash(assetPath, expected.algorithm)).toLowerCase();
  const generatedComparable =
    expected.encoding === 'base64'
      ? Buffer.from(generatedHash, 'hex').toString('base64')
      : generatedHash;
  const expectedComparable = expectedHash.trim().toLowerCase();

  if (generatedComparable.toLowerCase() === expectedComparable) {
    return { valid: true, actualSha256: generatedHash };
  }

  return { valid: false, actualSha256: generatedHash, errorCode: 'HASH_MISMATCH' };
}

module.exports = {
  calculateSha256,
  validateDownloadedAsset,
};
