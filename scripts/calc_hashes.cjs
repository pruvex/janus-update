const crypto = require('crypto');
const fs = require('fs');

const filePath = 'C:/KI/Janus-Projekt/release/janus-setup-0.4.17-beta.5.exe';
const data = fs.readFileSync(filePath);

const sha256 = crypto.createHash('sha256').update(data).digest('hex');
const sha512 = crypto.createHash('sha512').update(data).digest('base64');

console.log('SHA256:');
console.log(sha256);
console.log('SHA512-Base64:');
console.log(sha512);
