# Security Audit V1 — Janus Codebase
**Auditor:** Cascade (Diamond-Standard)  
**Datum:** 2026-07-09  
**Scope:** Hard security vulnerabilities only (RCE, Path Traversal, SSRF/CSRF, XSS, Keyring/Secret Leaks, Auth Bypass)  
**Ignored:** Code style, performance, typos, UI/UX

---

## Finding SEC-01 — XSS via unsanitized LLM output in `marked.parse()`
| Field       | Value |
|-------------|-------|
| **Severity** | **CRITICAL** |
| **Type**     | Stored XSS |
| **File**     | `frontend/js/chat.js` |
| **Lines**    | 517, 540, 766, 796, 805, 1362 |

**Description:**  
All LLM responses are rendered via `marked.parse(chatText)` and assigned directly to `innerHTML` without any sanitization (no DOMPurify, no `marked` sanitizer option). A malicious LLM response, injected prompt, or poisoned RAG document containing `<img onerror=...>` or `<script>` tags will execute arbitrary JavaScript in the Electron renderer context.

Line 796 is particularly dangerous: backend error messages are injected directly into `innerHTML` via template literal:
```js
loadingMessageElement.innerHTML = `<span style="color:red">[Stream Error] ${data.message}</span>`;
```

**Fix:**
```bash
npm install dompurify
```
```js
// In chat.js — wrap every marked.parse() call:
import DOMPurify from 'dompurify';
loadingMessageElement.innerHTML = DOMPurify.sanitize(marked.parse(chatText));
// For error messages:
loadingMessageElement.innerHTML = `<span style="color:red">[Stream Error] ${DOMPurify.sanitize(data.message)}</span>`;
```

---

## Finding SEC-02 — XSS via unsanitized `releaseNotes` in update modal
| Field       | Value |
|-------------|-------|
| **Severity** | **HIGH** |
| **Type**     | XSS |
| **File**     | `frontend/js/app.js` |
| **Lines**    | 1963, 2012-2018 |

**Description:**  
Release notes from `autoUpdater` are parsed via `marked.parse()` and injected into `innerHTML` without sanitization. An attacker who compromises the update feed (or via MITM on GitHub API) could inject arbitrary JS. Same issue with the error variable at line 2015 (`${error || 'Unbekannter Fehler'}`).

**Fix:**
```js
import DOMPurify from 'dompurify';
changelogContent.innerHTML = DOMPurify.sanitize(window.marked.parse(data.releaseNotes || '...'));
// Error display:
document.getElementById('update-modal-body').innerHTML = DOMPurify.sanitize(`<p>...</p><div>...</div>`);
```

---

## Finding SEC-03 — Arbitrary file write via `save-file-in-path` IPC handler (Path Traversal)
| Field       | Value |
|-------------|-------|
| **Severity** | **CRITICAL** |
| **Type**     | Path Traversal / Arbitrary File Write |
| **File**     | `main.electron.cjs` |
| **Lines**    | 796-805 |

**Description:**  
The `save-file-in-path` IPC handler accepts a `fullPath` parameter directly from the renderer and writes arbitrary `data` to it without any path validation or sandboxing:
```js
ipcMain.handle('save-file-in-path', async (event, { fullPath, data }) => {
  await fs.promises.writeFile(fullPath, Buffer.from(data));
});
```
A compromised renderer (e.g. via SEC-01 XSS) can write to any file on the filesystem, including overwriting system files, dropping executables, or modifying startup scripts. This is a direct RCE primitive.

**Fix:**
```js
ipcMain.handle('save-file-in-path', async (event, { fullPath, data }) => {
  const resolved = path.resolve(fullPath);
  const allowedRoots = [
    app.getPath('pictures'),
    app.getPath('downloads'),
    app.getPath('documents'),
  ];
  const isAllowed = allowedRoots.some(root => resolved.startsWith(root + path.sep) || resolved === root);
  if (!isAllowed) {
    return { success: false, error: 'Path outside allowed directories' };
  }
  if (path.basename(resolved).startsWith('.')) {
    return { success: false, error: 'Hidden files not allowed' };
  }
  await fs.promises.writeFile(resolved, Buffer.from(data));
  return { success: true };
});
```

---

## Finding SEC-04 — SSRF via `save-image-dialog` (no URL validation)
| Field       | Value |
|-------------|-------|
| **Severity** | **MEDIUM** |
| **Type**     | SSRF |
| **File**     | `main.electron.cjs` |
| **Lines**    | 272-315 |

**Description:**  
The `save-image-dialog` handler uses `imageUrl` from the renderer directly in `http.get(imageUrl)` / `https.get(imageUrl)` without URL validation. Unlike `save-image` (which validates protocol), this handler allows requests to internal network resources (e.g. `http://169.254.169.254/latest/meta-data/`, `http://localhost:8001/api/...`).

**Fix:**
```js
// Add same URL validation as save-image handler:
try {
  const parsed = new URL(imageUrl);
  if (parsed.protocol !== 'http:' && parsed.protocol !== 'https:') {
    return { success: false, message: 'Unsupported protocol' };
  }
  // Block private IPs
  const hostname = parsed.hostname;
  if (hostname === 'localhost' || hostname === '127.0.0.1' || hostname.startsWith('192.168.') || hostname.startsWith('10.') || hostname.startsWith('169.254.')) {
    return { success: false, message: 'Internal addresses not allowed' };
  }
} catch (e) {
  return { success: false, message: 'Invalid URL' };
}
```

---

## Finding SEC-05 — Hardcoded JWT secret key
| Field       | Value |
|-------------|-------|
| **Severity** | **HIGH** |
| **Type**     | Auth Bypass / Secret Leak |
| **File**     | `backend/dependencies.py` |
| **Line**     | 39 |

**Description:**  
The JWT secret key defaults to a hardcoded value `"your-secret-key-here"` when `JWT_SECRET_KEY` environment variable is not set:
```python
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-here")
```
Any attacker knowing this (it's in source code) can forge valid JWT tokens with arbitrary scopes (`settings:write`, `me`) and bypass all `Security(get_current_user, ...)` guards.

**Fix:**
```python
SECRET_KEY = os.getenv("JWT_SECRET_KEY")
if not SECRET_KEY:
    SECRET_KEY = secrets.token_hex(32)
    # Persist to config or log a warning
    logging.getLogger("janus_backend").warning(
        "JWT_SECRET_KEY not set — generated ephemeral key. Tokens will not survive restarts."
    )
```

---

## Finding SEC-06 — Sentry DSN hardcoded + `send_default_pii=True`
| Field       | Value |
|-------------|-------|
| **Severity** | **MEDIUM** |
| **Type**     | Secret Leak / Privacy |
| **File**     | `backend/main.py` |
| **Lines**    | 170, 186 |

**Description:**  
The Sentry DSN is hardcoded in source code. While DSNs are semi-public, this combined with `send_default_pii=True` and `traces_sample_rate=1.0` means every user's IP address, request headers, and potentially query parameters are sent to Sentry at 100% rate. For a desktop app this is a privacy concern.

**Fix:**
- Move DSN to environment variable: `dsn=os.getenv("SENTRY_DSN", "")`
- Set `send_default_pii=False` unless explicitly opted in by user
- Reduce `traces_sample_rate` to `0.1` in production

---

## Finding SEC-07 — Unauthenticated debug endpoints expose filesystem info
| Field       | Value |
|-------------|-------|
| **Severity** | **MEDIUM** |
| **Type**     | Information Disclosure |
| **File**     | `backend/main.py` |
| **Lines**    | 532-557, 610-646 |

**Description:**  
Two debug endpoints are exposed without authentication:
- `GET /debug/images` — leaks absolute filesystem paths, directory listing, permission info
- `GET /api/debug/memory` — leaks memory cache stats, circuit breaker state, internal system state

While the server binds to `127.0.0.1`, any local process or browser tab can query these. Combined with CORS `allow_origins` including many localhost ports, cross-origin scripts on any listed port can read this data.

**Fix:**
```python
# Add auth dependency to debug endpoints:
@app.get("/debug/images", dependencies=[Depends(api_key_auth)])
@app.get("/api/debug/memory", dependencies=[Depends(api_key_auth)])
```
Or gate behind `NODE_ENV == "development"` check.

---

## Finding SEC-08 — Unauthenticated routers: system, local_llm, styles, image_engine
| Field       | Value |
|-------------|-------|
| **Severity** | **MEDIUM** |
| **Type**     | Auth Bypass |
| **File**     | `backend/main.py` |
| **Lines**    | 660-663 |

**Description:**  
Four routers are mounted without `api_key_auth`:
```python
app.include_router(system.router, prefix="/api", tags=["System"])
app.include_router(local_llm.router, prefix="/api", tags=["Local LLM"])
app.include_router(styles.router, prefix="/api", tags=["Styles"])
app.include_router(image_engine.router, prefix="/api/local-image-gen", tags=["Local Image Engine"])
```
Any local process can call these endpoints to modify system settings, manage local LLM models, or trigger image generation without authentication.

**Fix:**  
Add `dependencies=[Depends(api_key_auth)]` to all four routers. For config-loading during startup, use a dedicated internal-only bootstrap route instead.

---

## Finding SEC-09 — `executeJavaScript` injection in splash screen
| Field       | Value |
|-------------|-------|
| **Severity** | **LOW** |
| **Type**     | Code Injection |
| **File**     | `main.electron.cjs` |
| **Lines**    | 607-609 |

**Description:**  
The `status` variable is interpolated into an `executeJavaScript` call via template literal:
```js
splashWindow.webContents.executeJavaScript(`
  document.querySelector('.status').textContent = '${status}';
`);
```
Currently `status` is constructed locally and not user-controlled, but this pattern is fragile. If `status` ever contains a single quote (e.g. from a backend message), it breaks out of the string and enables code injection in the splash window context.

**Fix:**
```js
splashWindow.webContents.executeJavaScript(
  `document.querySelector('.status').textContent = ${JSON.stringify(status)};`
);
```

---

## Finding SEC-10 — `_resolve_markdown_image_path` allows reading arbitrary local files
| Field       | Value |
|-------------|-------|
| **Severity** | **MEDIUM** |
| **Type**     | Path Traversal (Read) |
| **File**     | `backend/tools/pdf_generator.py` |
| **Lines**    | 1226-1234 |

**Description:**  
The function `_resolve_markdown_image_path` resolves markdown image references. While URL-based paths are restricted to `/user_images/`, the fallback at line 1233 accepts *any* absolute path:
```python
if os.path.exists(candidate):
    return candidate
```
An LLM-crafted markdown image reference like `![x](C:\Windows\System32\config\SAM)` would pass validation and the image bytes would be embedded into the PDF. This enables exfiltration of arbitrary local files if the PDF is later shared.

**Fix:**
```python
# Replace the bare os.path.exists fallback with a root check:
candidate_abs = os.path.abspath(candidate)
allowed_roots = [get_images_dir(), str(get_app_data_dir())]
if any(_is_path_inside_root(candidate_abs, root) for root in allowed_roots):
    if os.path.exists(candidate_abs):
        return candidate_abs
return None
```

---

## Finding SEC-11 — `stopBackend` command injection via `exec`
| Field       | Value |
|-------------|-------|
| **Severity** | **LOW** |
| **Type**     | Command Injection (latent) |
| **File**     | `main.electron.cjs` |
| **Lines**    | 164-181 |

**Description:**  
The `stopBackend` function uses `exec` with string interpolation:
```js
exec(`timeout /t 1 & taskkill /F /IM ${imageName} /T`);
```
Currently `imageName` is a hardcoded constant (`'janus_backend.exe'`), so this is not exploitable. However, the pattern is dangerous — if `imageName` ever becomes dynamic (e.g. from config), it enables arbitrary command execution.

**Fix:**
Use `spawn` with argument array instead of `exec` with string interpolation:
```js
// Replace exec line with:
setTimeout(() => {
  spawn('taskkill', ['/F', '/IM', imageName, '/T']);
}, 1000);
```

---

## Finding SEC-12 — Hardcoded bcrypt hash for `local_user`
| Field       | Value |
|-------------|-------|
| **Severity** | **LOW** |
| **Type**     | Credential Leak |
| **File**     | `backend/dependencies.py` |
| **Lines**    | 46-51 |

**Description:**  
`VALID_USERS` contains a hardcoded bcrypt hash for password `'secret'`. While the auth flow primarily uses API keys and JWT tokens (not password validation), having known credentials in source code is a security smell.

**Fix:**  
Remove the `VALID_USERS` dict if password auth is not used. If needed, generate credentials at bootstrap time and store in the secure config.

---

# Summary Matrix

| ID     | Severity   | Type               | File                       | Exploitable? |
|--------|------------|--------------------|-----------------------------|-------------|
| SEC-01 | CRITICAL   | Stored XSS         | `frontend/js/chat.js`       | Yes — via LLM/RAG injection |
| SEC-02 | HIGH       | XSS                | `frontend/js/app.js`        | Yes — via update feed MITM |
| SEC-03 | CRITICAL   | Arbitrary File Write| `main.electron.cjs`         | Yes — via XSS chain |
| SEC-04 | MEDIUM     | SSRF               | `main.electron.cjs`         | Yes — via renderer |
| SEC-05 | HIGH       | Auth Bypass         | `backend/dependencies.py`   | Yes — hardcoded secret |
| SEC-06 | MEDIUM     | Privacy/Secret Leak | `backend/main.py`           | Passive |
| SEC-07 | MEDIUM     | Info Disclosure     | `backend/main.py`           | Yes — unauthenticated |
| SEC-08 | MEDIUM     | Auth Bypass         | `backend/main.py`           | Yes — unauthenticated |
| SEC-09 | LOW        | Code Injection      | `main.electron.cjs`         | No (currently safe) |
| SEC-10 | MEDIUM     | Path Traversal Read | `backend/tools/pdf_generator.py` | Yes — via LLM |
| SEC-11 | LOW        | Command Injection   | `main.electron.cjs`         | No (currently safe) |
| SEC-12 | LOW        | Credential Leak     | `backend/dependencies.py`   | Low risk |

**Priority fix order:** SEC-01 → SEC-03 → SEC-05 → SEC-02 → SEC-10 → SEC-04 → SEC-07 → SEC-08 → SEC-06 → SEC-09 → SEC-11 → SEC-12
