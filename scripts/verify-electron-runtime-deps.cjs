const fs = require("fs");
const path = require("path");
const { builtinModules } = require("module");

const rootDir = path.resolve(__dirname, "..");
const packageJsonPath = path.join(rootDir, "package.json");
const packageJson = JSON.parse(fs.readFileSync(packageJsonPath, "utf8"));

const allowedRuntimeDeps = new Set(["axios", "electron-log", "electron-updater"]);
const ignoredRuntimeDeps = new Set(["electron"]);
const builtins = new Set(
  builtinModules.flatMap((name) => [name, name.replace(/^node:/, "")])
);

const runtimeFiles = [
  "main.electron.cjs",
  "frontend/preload.js",
  "electron/update-manager.cjs",
  "electron/update-security.cjs",
  "electron/update-state.cjs",
  "electron/startup-telemetry.cjs",
];

function packageNameFromSpecifier(specifier) {
  if (
    specifier.startsWith(".") ||
    specifier.startsWith("/") ||
    specifier.startsWith("node:") ||
    builtins.has(specifier)
  ) {
    return null;
  }

  if (specifier.startsWith("@")) {
    return specifier.split("/").slice(0, 2).join("/");
  }

  return specifier.split("/")[0];
}

const declaredRuntimeDeps = new Set(Object.keys(packageJson.dependencies || {}));
const unexpectedRuntimeDeps = [...declaredRuntimeDeps].filter(
  (name) => !allowedRuntimeDeps.has(name)
);

const missingAllowedDeps = [...allowedRuntimeDeps].filter(
  (name) => !declaredRuntimeDeps.has(name)
);

const runtimeRequires = new Map();
const requirePattern = /require\(\s*["']([^"']+)["']\s*\)/g;

for (const relativeFile of runtimeFiles) {
  const absoluteFile = path.join(rootDir, relativeFile);
  const content = fs.readFileSync(absoluteFile, "utf8");
  let match;

  while ((match = requirePattern.exec(content)) !== null) {
    const packageName = packageNameFromSpecifier(match[1]);
    if (packageName && !ignoredRuntimeDeps.has(packageName)) {
      const uses = runtimeRequires.get(packageName) || [];
      uses.push(relativeFile);
      runtimeRequires.set(packageName, uses);
    }
  }
}

const undeclaredRuntimeRequires = [...runtimeRequires.keys()].filter(
  (name) => !declaredRuntimeDeps.has(name)
);

const unusedRuntimeDeps = [...declaredRuntimeDeps].filter(
  (name) => !runtimeRequires.has(name)
);

const errors = [];

if (unexpectedRuntimeDeps.length > 0) {
  errors.push(
    `Unexpected production dependencies: ${unexpectedRuntimeDeps.join(", ")}. ` +
      "Move renderer/build-only packages to devDependencies."
  );
}

if (missingAllowedDeps.length > 0) {
  errors.push(`Missing expected runtime dependencies: ${missingAllowedDeps.join(", ")}.`);
}

if (undeclaredRuntimeRequires.length > 0) {
  errors.push(
    `Electron runtime requires undeclared packages: ${undeclaredRuntimeRequires.join(", ")}.`
  );
}

if (unusedRuntimeDeps.length > 0) {
  errors.push(`Production dependencies not used by Electron runtime: ${unusedRuntimeDeps.join(", ")}.`);
}

if (errors.length > 0) {
  console.error("verify:electron-runtime-deps FAILED");
  for (const error of errors) {
    console.error(`- ${error}`);
  }
  process.exit(1);
}

console.log(
  `verify:electron-runtime-deps PASS runtimeDeps=${[...declaredRuntimeDeps].join(", ")}`
);
