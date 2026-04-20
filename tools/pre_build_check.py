#!/usr/bin/env python3
"""
Pre-Build Verification for Janus Production Releases.
Run BEFORE PyInstaller to catch common issues early.

Usage:  python tools/pre_build_check.py
Exit 0 = all checks passed, Exit 1 = at least one FAIL.
"""
import ast
import json
import os
import re
import subprocess
import sys
from pathlib import Path

# ─── CONFIG ──────────────────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent.parent
BACKEND_DIR = PROJECT_ROOT / "backend"
REQUIREMENTS_FILE = PROJECT_ROOT / "requirements.txt"
PACKAGE_JSON = PROJECT_ROOT / "package.json"
VERSION_PY = BACKEND_ROOT = BACKEND_DIR / "version.py"
SPEC_FILE = PROJECT_ROOT / "janus_backend.spec"

# Packages that are stdlib or aliased (import name != pip name)
IMPORT_TO_PIP = {
    "cv2": "opencv-python",
    "PIL": "pillow",
    "yaml": "pyyaml",
    "bs4": "beautifulsoup4",
    "sklearn": "scikit-learn",
    "jwt": "pyjwt",
    "yt_dlp": "yt-dlp",
    "rapidfuzz": "rapidfuzz",
    "thefuzz": "thefuzz",
    "dotenv": "python-dotenv",
    "dateutil": "python-dateutil",
    "google": "google-api-python-client",
    "googleapiclient": "google-api-python-client",
    "sentry_sdk": "sentry-sdk",
    "face_recognition": "face_recognition",
    "dlib": "dlib",
    "num2words": "num2words",
    "wikipedia": "wikipedia-api",
    "wikipediaapi": "wikipedia-api",
    "Crypto": "cryptography",
    "geopy": "geopy",
    "feedparser": "feedparser",
    "ebooklib": "ebooklib",
    "fpdf": "fpdf2",
    "pypdf": "pypdf",
    "pydub": "pydub",
    "soundfile": "soundfile",
    "fitz": "pymupdf",
    "diffusers": "diffusers",
    "clip": "git+https://github.com/openai/CLIP.git",
    "psutil": "psutil",
}

# Known stdlib modules (subset of common ones to avoid false positives)
STDLIB_MODULES = {
    "abc", "argparse", "ast", "asyncio", "base64", "binascii", "builtins",
    "calendar", "cgi", "codecs", "collections", "concurrent", "configparser",
    "contextlib", "copy", "csv", "ctypes", "dataclasses", "datetime",
    "decimal", "difflib", "dis", "email", "enum", "errno", "fnmatch",
    "fractions", "ftplib", "functools", "gc", "getpass", "glob", "gzip",
    "hashlib", "heapq", "hmac", "html", "http", "importlib", "inspect",
    "io", "itertools", "json", "keyword", "linecache", "locale", "logging",
    "lzma", "math", "mimetypes", "multiprocessing", "numbers", "operator",
    "os", "pathlib", "pickle", "platform", "pprint", "queue", "random",
    "re", "secrets", "select", "shelve", "shlex", "shutil", "signal",
    "site", "smtplib", "socket", "sqlite3", "ssl", "stat", "statistics",
    "string", "struct", "subprocess", "sys", "sysconfig", "tempfile", "textwrap",
    "threading", "time", "timeit", "token", "tokenize", "tomllib", "trace",
    "traceback", "tracemalloc", "types", "typing", "unicodedata", "unittest",
    "urllib", "uuid", "venv", "warnings", "wave", "weakref", "webbrowser",
    "xml", "xmlrpc", "zipfile", "zipimport", "zlib",
    # Windows-specific
    "msvcrt", "winreg", "winsound", "ctypes",
    # Internal / test / common local names
    "_thread", "__future__",
    "data", "services", "utils", "tests", "config", "assets", "static", "skills",
    "tools", "models", "schemas", "handlers", "routes", "database",
    "pyfakefs",  # Test-only
}

# ─── RESULT TRACKING ─────────────────────────────────────────────────────────
results = []

def check(name: str, passed: bool, detail: str = ""):
    status = "PASS" if passed else "FAIL"
    icon = "✅" if passed else "❌"
    results.append((name, passed, detail))
    msg = f"  {icon} {name}"
    if detail:
        msg += f"  — {detail}"
    print(msg)

def section(title: str):
    print(f"\n{'─'*60}")
    print(f"  {title}")
    print(f"{'─'*60}")


# ═══════════════════════════════════════════════════════════════════════════════
# CHECK 1: Environment
# ═══════════════════════════════════════════════════════════════════════════════
def check_environment():
    section("1. ENVIRONMENT CHECKS")

    # GH_TOKEN
    gh_token = os.environ.get("GH_TOKEN", "")
    check("GH_TOKEN is set", bool(gh_token),
          f"starts with {gh_token[:4]}****" if gh_token else "NOT SET — publish will fail")

    # Node.js
    try:
        node_v = subprocess.check_output(["node", "--version"], text=True).strip()
        check("Node.js available", True, node_v)
    except Exception:
        check("Node.js available", False, "node not found in PATH")

    # Python venv
    venv_python = BACKEND_DIR / "venv" / "Scripts" / "python.exe"
    check("Backend venv exists", venv_python.exists(),
          str(venv_python) if venv_python.exists() else "venv/Scripts/python.exe missing")

    # UPX (referenced in spec)
    upx_dir = Path(r"C:\tools\upx-5.1.0-win64")
    check("UPX directory exists", upx_dir.exists(),
          str(upx_dir) if upx_dir.exists() else "UPX missing — build will be larger but won't fail")


# ═══════════════════════════════════════════════════════════════════════════════
# CHECK 2: Version Sync
# ═══════════════════════════════════════════════════════════════════════════════
def check_version_sync():
    section("2. VERSION SYNC")

    pkg = json.loads(PACKAGE_JSON.read_text(encoding="utf-8"))
    pkg_version = pkg.get("version", "UNKNOWN")

    if VERSION_PY.exists():
        version_py_content = VERSION_PY.read_text(encoding="utf-8")
        match = re.search(r'APP_VERSION\s*=\s*"([^"]+)"', version_py_content)
        py_version = match.group(1) if match else "PARSE_ERROR"
    else:
        py_version = "FILE_MISSING"

    synced = pkg_version == py_version
    check("package.json ↔ version.py sync", synced,
          f"package.json={pkg_version}, version.py={py_version}" +
          ("" if synced else " → run 'npm run write-version'"))


# ═══════════════════════════════════════════════════════════════════════════════
# CHECK 3: PyInstaller Spec Paths
# ═══════════════════════════════════════════════════════════════════════════════
def check_spec_paths():
    section("3. PYINSTALLER SPEC DATA PATHS")

    required_paths = [
        ("backend/config", "Style profiles, schemas"),
        ("backend/assets", "Preview images"),
        ("backend/static", "Generated images dir"),
        ("frontend/dist", "Frontend build (run 'npm run build' first)"),
        ("frontend/assets", "Frontend static assets"),
    ]
    for rel_path, desc in required_paths:
        full = PROJECT_ROOT / rel_path
        check(f"Spec data: {rel_path}", full.exists(),
              desc if full.exists() else f"MISSING — {desc}")


# ═══════════════════════════════════════════════════════════════════════════════
# CHECK 4: Python Syntax (compile all .py files)
# ═══════════════════════════════════════════════════════════════════════════════
def check_python_syntax():
    section("4. PYTHON SYNTAX CHECK (backend/**/*.py)")

    errors = []
    py_files = list(BACKEND_DIR.rglob("*.py"))
    # Exclude venv
    py_files = [f for f in py_files if "venv" not in f.parts and "__pycache__" not in f.parts]

    for f in py_files:
        try:
            with open(f, "r", encoding="utf-8") as fh:
                source = fh.read()
            compile(source, str(f), "exec")
        except SyntaxError as e:
            errors.append(f"{f.relative_to(PROJECT_ROOT)}:{e.lineno} — {e.msg}")

    check(f"Syntax OK ({len(py_files)} files)", len(errors) == 0,
          f"{len(errors)} error(s)" if errors else "all clean")
    for err in errors[:10]:  # Show max 10
        print(f"      ⚠ {err}")


# ═══════════════════════════════════════════════════════════════════════════════
# CHECK 5: Critical Import Test
# ═══════════════════════════════════════════════════════════════════════════════
def check_critical_imports():
    section("5. CRITICAL IMPORT TEST")

    # Test importing backend.main without actually starting the server
    result = subprocess.run(
        [sys.executable, "-c", "import backend.main; print('OK')"],
        capture_output=True, text=True, cwd=str(PROJECT_ROOT), timeout=30
    )
    passed = result.returncode == 0 and "OK" in result.stdout
    detail = "backend.main imports cleanly" if passed else result.stderr.strip().split("\n")[-1][:120]
    check("import backend.main", passed, detail)


# ═══════════════════════════════════════════════════════════════════════════════
# CHECK 6: Requirements Drift Detection
# ═══════════════════════════════════════════════════════════════════════════════
def check_requirements_drift():
    section("6. REQUIREMENTS DRIFT CHECK")

    # Parse requirements.txt into set of known package names (lowercase, normalized)
    req_text = REQUIREMENTS_FILE.read_text(encoding="utf-8")
    known_packages = set()
    for line in req_text.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or line.startswith("-"):
            continue
        # Extract package name (before ==, >=, etc.)
        pkg_name = re.split(r"[>=<!=~\[]", line)[0].strip().lower()
        # Normalize: underscores ↔ hyphens
        known_packages.add(pkg_name.replace("-", "_"))
        known_packages.add(pkg_name.replace("_", "-"))
        known_packages.add(pkg_name)

    # Scan all backend .py files for imports
    py_files = list(BACKEND_DIR.rglob("*.py"))
    py_files = [f for f in py_files if "venv" not in f.parts and "__pycache__" not in f.parts]

    all_imports = set()
    for f in py_files:
        try:
            tree = ast.parse(f.read_text(encoding="utf-8"), filename=str(f))
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    all_imports.add(alias.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom):
                if node.module and node.level == 0:  # absolute imports only
                    all_imports.add(node.module.split(".")[0])

    # Filter: remove stdlib, internal (backend.*), and known aliases
    missing = []
    for imp in sorted(all_imports):
        if imp in STDLIB_MODULES:
            continue
        if imp.startswith("backend") or imp.startswith("_"):
            continue

        # Check direct match
        imp_lower = imp.lower().replace("-", "_")
        if imp_lower in known_packages:
            continue
        # Check alias mapping
        pip_name = IMPORT_TO_PIP.get(imp, "").lower().replace("-", "_")
        if pip_name and (pip_name in known_packages or pip_name.replace("_", "-") in known_packages):
            continue

        missing.append(imp)

    check(f"Requirements coverage ({len(all_imports)} imports scanned)",
          len(missing) == 0,
          f"{len(missing)} potentially missing" if missing else "all imports covered")
    for m in missing[:15]:
        pip_hint = IMPORT_TO_PIP.get(m, m)
        print(f"      ⚠ import '{m}' → pip install {pip_hint}?")


# ═══════════════════════════════════════════════════════════════════════════════
# CHECK 7: Frontend Build Freshness
# ═══════════════════════════════════════════════════════════════════════════════
def check_frontend_build():
    section("7. FRONTEND BUILD FRESHNESS")

    dist_dir = PROJECT_ROOT / "frontend" / "dist"
    index_html = dist_dir / "index.html"

    if not index_html.exists():
        check("frontend/dist/index.html exists", False,
              "Frontend not built — run 'npm run build' first")
        return

    # Check if any source file is newer than the build
    dist_mtime = index_html.stat().st_mtime
    src_dir = PROJECT_ROOT / "frontend" / "src"
    stale_files = []
    if src_dir.exists():
        for f in src_dir.rglob("*"):
            if f.is_file() and f.stat().st_mtime > dist_mtime:
                stale_files.append(f.relative_to(PROJECT_ROOT))

    if stale_files:
        check("Frontend build is fresh", False,
              f"{len(stale_files)} source file(s) newer than dist — rebuild recommended")
        for sf in stale_files[:5]:
            print(f"      ⚠ {sf}")
    else:
        check("Frontend build is fresh", True, "dist is up-to-date")


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════
def main():
    print("=" * 60)
    print("  JANUS PRE-BUILD VERIFICATION")
    print(f"  Project: {PROJECT_ROOT}")
    print("=" * 60)

    check_environment()
    check_version_sync()
    check_spec_paths()
    check_python_syntax()
    check_critical_imports()
    check_requirements_drift()
    check_frontend_build()

    # ─── SUMMARY ──────────────────────────────────────────────────────────
    total = len(results)
    passed = sum(1 for _, p, _ in results if p)
    failed = total - passed

    print(f"\n{'='*60}")
    print(f"  SUMMARY: {passed}/{total} passed, {failed} failed")
    print(f"{'='*60}")

    if failed > 0:
        print("\n  ❌ BUILD NOT RECOMMENDED — fix the issues above first.\n")
        sys.exit(1)
    else:
        print("\n  ✅ ALL CHECKS PASSED — safe to build.\n")
        sys.exit(0)


if __name__ == "__main__":
    main()
