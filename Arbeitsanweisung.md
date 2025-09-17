Windows PowerShell
Copyright (C) Microsoft Corporation. Alle Rechte vorbehalten.

Installieren Sie die neueste PowerShell für neue Funktionen und Verbesserungen! https://aka.ms/PSWindows

PS C:\KI\Janus-Projekt> npm run start-dev

> janus-projekt@1.1.0 start-dev
> concurrently "npm:start-backend" "npm:start-frontend"

[start-backend]
[start-backend] > janus-projekt@1.1.0 start-backend
[start-backend] > C:\KI\Janus-Projekt\backend\venv\Scripts\python.exe -m uvicorn backend.main:app --reload --port 8001 --host localhost
[start-backend]
[start-frontend]
[start-frontend] > janus-projekt@1.1.0 start-frontend
[start-frontend] > concurrently "npm run start-electron" "npm run start-vite"
[start-frontend]
[start-backend] INFO:     Will watch for changes in these directories: ['C:\\KI\\Janus-Projekt']
[start-backend] INFO:     Uvicorn running on http://localhost:8001 (Press CTRL+C to quit)
[start-backend] INFO:     Started reloader process [21344] using WatchFiles
[start-frontend] [0]
[start-frontend] [0] > janus-projekt@1.1.0 start-electron
[start-frontend] [0] > wait-on tcp:8001 && cross-env NODE_ENV=development electron .
[start-frontend] [0]
[start-backend] 2025-09-17 18:26:54 - janus_backend - [INFO] - Logger wurde initialisiert.
[start-frontend] [1]
[start-frontend] [1] > janus-projekt@1.1.0 start-vite
[start-frontend] [1] > vite
[start-frontend] [1]
[start-backend] 2025-09-17 18:26:54 - keyring.backend - [DEBUG] - Loading KWallet
[start-backend] 2025-09-17 18:26:54 - keyring.backend - [DEBUG] - Loading SecretService
[start-backend] 2025-09-17 18:26:54 - keyring.backend - [DEBUG] - Loading Windows
[start-backend] 2025-09-17 18:26:54 - win32ctypes.core.ctypes - [DEBUG] - Loaded ctypes backend
[start-backend] 2025-09-17 18:26:54 - keyring.backend - [DEBUG] - Loading chainer
[start-backend] 2025-09-17 18:26:54 - keyring.backend - [DEBUG] - Loading libsecret
[start-backend] 2025-09-17 18:26:54 - keyring.backend - [DEBUG] - Loading macOS
[start-backend] 2025-09-17 18:26:54 - janus_backend - [INFO] - OpenAI API key loaded from keyring and set as environment variable.
[start-frontend] [1] The CJS build of Vite's Node API is deprecated. See https://vite.dev/guide/troubleshooting.html#vite-cjs-node-api-deprecated for more details.
[start-frontend] [1]
[start-frontend] [1]   VITE v5.4.19  ready in 315 ms
[start-frontend] [1]
[start-frontend] [1]   ➜  Local:   http://localhost:5173/
[start-frontend] [1]   ➜  Network: use --host to expose
[start-backend] 2025-09-17 18:26:57 - janus_backend - [INFO] - Logger wurde initialisiert.
[start-backend] 2025-09-17 18:26:57 - janus_backend - [INFO] - Logger wurde initialisiert.
[start-backend] 2025-09-17 18:27:03 - sentence_transformers.SentenceTransformer - [INFO] - Use pytorch device_name: cpu
[start-backend] 2025-09-17 18:27:03 - sentence_transformers.SentenceTransformer - [INFO] - Load pretrained SentenceTransformer: C:\KI\Janus-Projekt\backend/model_cache/all-MiniLM-L6-v2
[start-backend] 2025-09-17 18:27:03 - janus_backend - [INFO] - Application Data Directory: C:\Users\pruve\AppData\Local\JanusDev\Janus Projekt
[start-backend] INFO:     Started server process [10624]
[start-backend] INFO:     Waiting for application startup.
[start-backend] 2025-09-17 18:27:03 - janus_backend - [INFO] - Scheduling initial memory maintenance tasks on startup.
[start-backend] 2025-09-17 18:27:03 - janus_backend - [INFO] - Background memory archival task starting.
[start-backend] 2025-09-17 18:27:03 - janus_backend - [INFO] - STM size (0) is within limit (250). No archival needed.
[start-backend] 2025-09-17 18:27:03 - janus_backend - [INFO] - Background memory archival task finished successfully.
[start-backend] 2025-09-17 18:27:03 - janus_backend - [INFO] - Background memory pruning task starting.
[start-backend] 2025-09-17 18:27:03 - janus_backend - [INFO] - No expired memories to prune.
[start-backend] INFO:     Application startup complete.
[start-backend] 2025-09-17 18:27:03 - janus_backend - [INFO] - Background memory pruning task finished successfully.
[start-frontend] [0]
[start-frontend] [0] Main process: Script started (Root main.electron.js)
[start-frontend] [0] Main process: ipcMain.handle registered for save-image
[start-frontend] [0] Main process: createWindow called
[start-frontend] [0] [Main Process] Attempting to load preload script from: C:\KI\Janus-Projekt\frontend\preload.js
[start-backend] INFO:     127.0.0.1:51736 - "GET /api/models/catalog HTTP/1.1" 200 OK
[start-frontend] [0] [Electron Main] Backend is ready!
[start-backend] INFO:     127.0.0.1:51744 - "GET /api/models/catalog HTTP/1.1" 200 OK
[start-backend] INFO:     127.0.0.1:51745 - "GET /api/personalities HTTP/1.1" 200 OK
[start-backend] INFO:     127.0.0.1:51744 - "GET /api/models/catalog HTTP/1.1" 200 OK
[start-backend] 2025-09-17 18:27:04 - janus_backend - [INFO] - Attempting to retrieve API keys.
[start-backend] 2025-09-17 18:27:04 - janus_backend - [INFO] - Successfully retrieved API key for provider: openai
[start-backend] 2025-09-17 18:27:04 - janus_backend - [INFO] - Successfully retrieved API key for provider: gemini
[start-backend] 2025-09-17 18:27:04 - janus_backend - [INFO] - No API key found for provider: anthropic
[start-backend] 2025-09-17 18:27:04 - janus_backend - [INFO] - No API key found for provider: cohere
[start-backend] INFO:     127.0.0.1:51745 - "GET /api/keys HTTP/1.1" 200 OK
[start-backend] INFO:     127.0.0.1:51744 - "GET /api/personalities/active HTTP/1.1" 200 OK
[start-backend] INFO:     127.0.0.1:51746 - "GET /api/last-used-model HTTP/1.1" 200 OK
[start-backend] INFO:     127.0.0.1:51744 - "GET /api/personalities/active HTTP/1.1" 200 OK
[start-backend] 2025-09-17 18:27:04 - janus_backend - [INFO] - Attempting to retrieve API keys.
[start-backend] 2025-09-17 18:27:04 - janus_backend - [INFO] - Successfully retrieved API key for provider: openai
[start-backend] 2025-09-17 18:27:04 - janus_backend - [INFO] - Successfully retrieved API key for provider: gemini
[start-backend] 2025-09-17 18:27:04 - janus_backend - [INFO] - No API key found for provider: anthropic
[start-backend] 2025-09-17 18:27:04 - janus_backend - [INFO] - No API key found for provider: cohere
[start-backend] INFO:     127.0.0.1:51745 - "GET /api/keys HTTP/1.1" 200 OK
[start-backend] INFO:     127.0.0.1:51744 - "GET /api/personalities HTTP/1.1" 200 OK
[start-backend] INFO:     127.0.0.1:51746 - "GET /api/models/selection/openai HTTP/1.1" 200 OK
[start-backend] INFO:     127.0.0.1:51746 - "GET /api/models/selection/gemini HTTP/1.1" 200 OK
[start-frontend] [0] [2764:0917/182704.697:ERROR:CONSOLE(1)] "Request Autofill.enable failed. {"code":-32601,"message":"'Autofill.enable' wasn't found"}", source: devtools://devtools/bundled/core/protocol_client/protocol_client.js (1)
[start-frontend] [0] [2764:0917/182704.697:ERROR:CONSOLE(1)] "Request Autofill.setAddresses failed. {"code":-32601,"message":"'Autofill.setAddresses' wasn't found"}", source: devtools://devtools/bundled/core/protocol_client/protocol_client.js (1)
[start-backend] INFO:     127.0.0.1:51744 - "GET /api/costs/dashboard HTTP/1.1" 200 OK
[start-backend] INFO:     127.0.0.1:51746 - "GET /api/chats?include_archived=false HTTP/1.1" 200 OK
[start-backend] INFO:     127.0.0.1:51746 - "OPTIONS /api/chats HTTP/1.1" 200 OK
[start-backend] INFO:     127.0.0.1:51744 - "POST /api/chats HTTP/1.1" 200 OK
[start-backend] INFO:     127.0.0.1:51744 - "GET /api/chats?include_archived=false HTTP/1.1" 200 OK
[start-backend] INFO:     127.0.0.1:51744 - "GET /api/chats/1 HTTP/1.1" 200 OK
[start-backend] INFO:     127.0.0.1:51744 - "GET /api/chats/1 HTTP/1.1" 200 OK
[start-backend] INFO:     127.0.0.1:51746 - "GET /api/chats/1/messages HTTP/1.1" 200 OK
[start-backend] INFO:     127.0.0.1:51746 - "GET /api/chats/1/messages HTTP/1.1" 200 OK
[start-backend] INFO:     127.0.0.1:51867 - "OPTIONS /api/chats/1/title HTTP/1.1" 200 OK
[start-backend] INFO:     127.0.0.1:51867 - "PUT /api/chats/1/title HTTP/1.1" 200 OK
[start-backend] INFO:     127.0.0.1:51867 - "GET /api/chats?include_archived=false HTTP/1.1" 200 OK
[start-backend] INFO:     127.0.0.1:51867 - "OPTIONS /api/chat HTTP/1.1" 200 OK
[start-backend] 2025-09-17 18:27:37 - janus_backend - [INFO] - Explizite Werkzeug-Direktive wurde auf den System-Prompt angewendet.
[start-backend] 2025-09-17 18:27:37 - janus_backend - [INFO] - Using persona prompt for 'ai_assistant'
[start-backend] 2025-09-17 18:27:37 - grpc._cython.cygrpc - [DEBUG] - Using AsyncIOEngine.POLLER as I/O engine
[start-backend] 2025-09-17 18:27:39 - janus_backend - [INFO] -
[start-backend] --- USAGE TRACKING ---
[start-backend] Model: gemini-2.5-flash
[start-backend] Input Tokens: 0
[start-backend] Output Tokens: 0
[start-backend] Image Quality: N/A
[start-backend] Image Size: N/A
[start-backend] Total Cost: 0.00000000 �
[start-backend] ----------------------
[start-backend] 2025-09-17 18:27:39 - janus_backend - [INFO] - Final answer before check: 'Hallo! Wie kann ich Ihnen heute behilflich sein?'
[start-backend] INFO:     127.0.0.1:51867 - "POST /api/chat HTTP/1.1" 200 OK
[start-backend] INFO:     127.0.0.1:51867 - "GET /api/costs/dashboard HTTP/1.1" 200 OK
[start-backend] 2025-09-17 18:27:49 - janus_backend - [INFO] - Explizite Werkzeug-Direktive wurde auf den System-Prompt angewendet.
[start-backend] 2025-09-17 18:27:49 - janus_backend - [INFO] - Using persona prompt for 'ai_assistant'
[start-backend] 2025-09-17 18:27:49 - janus_backend - [INFO] - [DEBUG] FINAL HYBRID Memory Context Generated (length: 0):
[start-backend] 2025-09-17 18:27:49 - janus_backend - [INFO] - Touched 0 memory snippets to update their relevance.
[start-backend] 2025-09-17 18:27:49 - grpc._cython.cygrpc - [DEBUG] - Using AsyncIOEngine.POLLER as I/O engine
[start-backend] 2025-09-17 18:27:51 - janus_backend - [INFO] - Gemini requested tool call: perform_websearch with args: {'query': 'Preis Nintendo Switch 2'}
[start-backend] 2025-09-17 18:27:51 - janus_backend - [INFO] -
[start-backend] --- USAGE TRACKING ---
[start-backend] Model: gemini-2.5-flash
[start-backend] Input Tokens: 0
[start-backend] Output Tokens: 0
[start-backend] Image Quality: N/A
[start-backend] Image Size: N/A
[start-backend] Total Cost: 0.00000000 �
[start-backend] ----------------------
[start-backend] 2025-09-17 18:27:51 - janus_backend - [WARNING] - Unknown tool call: perform_websearch for provider: gemini
[start-backend] 2025-09-17 18:27:51 - janus_backend - [INFO] - Executing tool 'perform_websearch' with args: {'query': 'Preis Nintendo Switch 2'}
[start-backend] 2025-09-17 18:27:52 - openai._base_client - [DEBUG] - Request options: {'method': 'post', 'url': '/responses', 'files': None, 'idempotency_key': 'stainless-python-retry-620c1033-a1f8-4c33-8ba1-77d5333b60ff', 'json_data': {'input': 'F�hre eine Websuche durch und gib eine detaillierte, faktenbasierte Antwort auf die folgende Frage: Preis Nintendo Switch 2', 'model': 'gpt-4o-mini', 'tools': [{'type': 'web_search'}]}}
[start-backend] 2025-09-17 18:27:52 - openai._base_client - [DEBUG] - Sending HTTP Request: POST https://api.openai.com/v1/responses
[start-backend] 2025-09-17 18:27:52 - httpcore.connection - [DEBUG] - connect_tcp.started host='api.openai.com' port=443 local_address=None timeout=5.0 socket_options=None
[start-backend] 2025-09-17 18:27:52 - httpcore.connection - [DEBUG] - connect_tcp.complete return_value=<httpcore._backends.anyio.AnyIOStream object at 0x000001FFB6137750>
[start-backend] 2025-09-17 18:27:52 - httpcore.connection - [DEBUG] - start_tls.started ssl_context=<ssl.SSLContext object at 0x000001FF891489E0> server_hostname='api.openai.com' timeout=5.0
[start-backend] 2025-09-17 18:27:52 - httpcore.connection - [DEBUG] - start_tls.complete return_value=<httpcore._backends.anyio.AnyIOStream object at 0x000001FFB6786E90>
[start-backend] 2025-09-17 18:27:52 - httpcore.http11 - [DEBUG] - send_request_headers.started request=<Request [b'POST']>
[start-backend] 2025-09-17 18:27:52 - httpcore.http11 - [DEBUG] - send_request_headers.complete
[start-backend] 2025-09-17 18:27:52 - httpcore.http11 - [DEBUG] - send_request_body.started request=<Request [b'POST']>
[start-backend] 2025-09-17 18:27:52 - httpcore.http11 - [DEBUG] - send_request_body.complete
[start-backend] 2025-09-17 18:27:52 - httpcore.http11 - [DEBUG] - receive_response_headers.started request=<Request [b'POST']>
[start-backend] 2025-09-17 18:27:59 - httpcore.http11 - [DEBUG] - receive_response_headers.complete return_value=(b'HTTP/1.1', 429, b'Too Many Requests', [(b'Date', b'Wed, 17 Sep 2025 16:28:00 GMT'), (b'Content-Type', b'application/json'), (b'Content-Length', b'316'), (b'Connection', b'keep-alive'), (b'openai-version', b'2020-10-01'), (b'openai-organization', b'user-9rymi7trhkh9wx0cjpzb4txg'), (b'openai-project', b'proj_xZDNucsxSbdjkba6PitMv58d'), (b'x-request-id', b'req_988dd548cd28c801ed3413dfb5a0a808'), (b'openai-processing-ms', b'6992'), (b'x-envoy-upstream-service-time', b'6998'), (b'strict-transport-security', b'max-age=31536000; includeSubDomains; preload'), (b'cf-cache-status', b'DYNAMIC'), (b'Set-Cookie', b'__cf_bm=oScvENzDw4sVut_yxSz8UCzwN4p.Op7mrnQT8WtZgpA-1758126480-1.0.1.1-GUJa7PUumk539UuFdsjrkBdLkPvT9rmSAJUjzCm4Kum9WypK1Gnm_Kar75JE_PpNNkvl1B7k_7xoNgpz0wO2nbURUeerj7EifSObS9moQ8Q; path=/; expires=Wed, 17-Sep-25 16:58:00 GMT; domain=.api.openai.com; HttpOnly; Secure; SameSite=None'), (b'X-Content-Type-Options', b'nosniff'), (b'Set-Cookie', b'_cfuvid=24QwwdIQHXuzYGlt.DJUjJd6lkYMlfb5jTBc2KKuDVQ-1758126480800-0.0.1.1-604800000; path=/; domain=.api.openai.com; HttpOnly; Secure; SameSite=None'), (b'Server', b'cloudflare'), (b'CF-RAY', b'9809f939fe1fc7dd-DUS'), (b'alt-svc', b'h3=":443"; ma=86400')])
[start-backend] 2025-09-17 18:27:59 - httpx - [INFO] - HTTP Request: POST https://api.openai.com/v1/responses "HTTP/1.1 429 Too Many Requests"
[start-backend] 2025-09-17 18:27:59 - httpcore.http11 - [DEBUG] - receive_response_body.started request=<Request [b'POST']>
[start-backend] 2025-09-17 18:27:59 - httpcore.http11 - [DEBUG] - receive_response_body.complete
[start-backend] 2025-09-17 18:27:59 - httpcore.http11 - [DEBUG] - response_closed.started
[start-backend] 2025-09-17 18:27:59 - httpcore.http11 - [DEBUG] - response_closed.complete
[start-backend] 2025-09-17 18:27:59 - openai._base_client - [DEBUG] - HTTP Response: POST https://api.openai.com/v1/responses "429 Too Many Requests" Headers([('date', 'Wed, 17 Sep 2025 16:28:00 GMT'), ('content-type', 'application/json'), ('content-length', '316'), ('connection', 'keep-alive'), ('openai-version', '2020-10-01'), ('openai-organization', 'user-9rymi7trhkh9wx0cjpzb4txg'), ('openai-project', 'proj_xZDNucsxSbdjkba6PitMv58d'), ('x-request-id', 'req_988dd548cd28c801ed3413dfb5a0a808'), ('openai-processing-ms', '6992'), ('x-envoy-upstream-service-time', '6998'), ('strict-transport-security', 'max-age=31536000; includeSubDomains; preload'), ('cf-cache-status', 'DYNAMIC'), ('set-cookie', '__cf_bm=oScvENzDw4sVut_yxSz8UCzwN4p.Op7mrnQT8WtZgpA-1758126480-1.0.1.1-GUJa7PUumk539UuFdsjrkBdLkPvT9rmSAJUjzCm4Kum9WypK1Gnm_Kar75JE_PpNNkvl1B7k_7xoNgpz0wO2nbURUeerj7EifSObS9moQ8Q; path=/; expires=Wed, 17-Sep-25 16:58:00 GMT; domain=.api.openai.com; HttpOnly; Secure; SameSite=None'), ('x-content-type-options', 'nosniff'), ('set-cookie', '_cfuvid=24QwwdIQHXuzYGlt.DJUjJd6lkYMlfb5jTBc2KKuDVQ-1758126480800-0.0.1.1-604800000; path=/; domain=.api.openai.com; HttpOnly; Secure; SameSite=None'), ('server', 'cloudflare'), ('cf-ray', '9809f939fe1fc7dd-DUS'), ('alt-svc', 'h3=":443"; ma=86400')])
[start-backend] 2025-09-17 18:27:59 - openai._base_client - [DEBUG] - request_id: req_988dd548cd28c801ed3413dfb5a0a808
[start-backend] 2025-09-17 18:27:59 - openai._base_client - [DEBUG] - Encountered httpx.HTTPStatusError
[start-backend] Traceback (most recent call last):
[start-backend]   File "C:\KI\Janus-Projekt\backend\venv\Lib\site-packages\openai\_base_client.py", line 1574, in request
[start-backend]     response.raise_for_status()
[start-backend]   File "C:\KI\Janus-Projekt\backend\venv\Lib\site-packages\httpx\_models.py", line 829, in raise_for_status
[start-backend]     raise HTTPStatusError(message, request=request, response=self)
[start-backend] httpx.HTTPStatusError: Client error '429 Too Many Requests' for url 'https://api.openai.com/v1/responses'
[start-backend] For more information check: https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/429
[start-backend] 2025-09-17 18:27:59 - openai._base_client - [DEBUG] - Retrying due to status code 429
[start-backend] 2025-09-17 18:27:59 - openai._base_client - [DEBUG] - 2 retries left
[start-backend] 2025-09-17 18:27:59 - openai._base_client - [INFO] - Retrying request to /responses in 0.379645 seconds
[start-backend] 2025-09-17 18:28:00 - openai._base_client - [DEBUG] - Request options: {'method': 'post', 'url': '/responses', 'files': None, 'idempotency_key': 'stainless-python-retry-620c1033-a1f8-4c33-8ba1-77d5333b60ff', 'json_data': {'input': 'F�hre eine Websuche durch und gib eine detaillierte, faktenbasierte Antwort auf die folgende Frage: Preis Nintendo Switch 2', 'model': 'gpt-4o-mini', 'tools': [{'type': 'web_search'}]}}
[start-backend] 2025-09-17 18:28:00 - openai._base_client - [DEBUG] - Sending HTTP Request: POST https://api.openai.com/v1/responses
[start-backend] 2025-09-17 18:28:00 - httpcore.http11 - [DEBUG] - send_request_headers.started request=<Request [b'POST']>
[start-backend] 2025-09-17 18:28:00 - httpcore.http11 - [DEBUG] - send_request_headers.complete
[start-backend] 2025-09-17 18:28:00 - httpcore.http11 - [DEBUG] - send_request_body.started request=<Request [b'POST']>
[start-backend] 2025-09-17 18:28:00 - httpcore.http11 - [DEBUG] - send_request_body.complete
[start-backend] 2025-09-17 18:28:00 - httpcore.http11 - [DEBUG] - receive_response_headers.started request=<Request [b'POST']>
[start-backend] 2025-09-17 18:28:06 - httpcore.http11 - [DEBUG] - receive_response_headers.complete return_value=(b'HTTP/1.1', 429, b'Too Many Requests', [(b'Date', b'Wed, 17 Sep 2025 16:28:07 GMT'), (b'Content-Type', b'application/json'), (b'Content-Length', b'316'), (b'Connection', b'keep-alive'), (b'openai-version', b'2020-10-01'), (b'openai-organization', b'user-9rymi7trhkh9wx0cjpzb4txg'), (b'openai-project', b'proj_xZDNucsxSbdjkba6PitMv58d'), (b'x-request-id', b'req_dd83062500330dab368b291241fd8174'), (b'openai-processing-ms', b'6105'), (b'x-envoy-upstream-service-time', b'6109'), (b'strict-transport-security', b'max-age=31536000; includeSubDomains; preload'), (b'cf-cache-status', b'DYNAMIC'), (b'X-Content-Type-Options', b'nosniff'), (b'Server', b'cloudflare'), (b'CF-RAY', b'9809f96b8df4c7dd-DUS'), (b'alt-svc', b'h3=":443"; ma=86400')])
[start-backend] 2025-09-17 18:28:06 - httpx - [INFO] - HTTP Request: POST https://api.openai.com/v1/responses "HTTP/1.1 429 Too Many Requests"
[start-backend] 2025-09-17 18:28:06 - httpcore.http11 - [DEBUG] - receive_response_body.started request=<Request [b'POST']>
[start-backend] 2025-09-17 18:28:06 - httpcore.http11 - [DEBUG] - receive_response_body.complete
[start-backend] 2025-09-17 18:28:06 - httpcore.http11 - [DEBUG] - response_closed.started
[start-backend] 2025-09-17 18:28:06 - httpcore.http11 - [DEBUG] - response_closed.complete
[start-backend] 2025-09-17 18:28:06 - openai._base_client - [DEBUG] - HTTP Response: POST https://api.openai.com/v1/responses "429 Too Many Requests" Headers({'date': 'Wed, 17 Sep 2025 16:28:07 GMT', 'content-type': 'application/json', 'content-length': '316', 'connection': 'keep-alive', 'openai-version': '2020-10-01', 'openai-organization': 'user-9rymi7trhkh9wx0cjpzb4txg', 'openai-project': 'proj_xZDNucsxSbdjkba6PitMv58d', 'x-request-id': 'req_dd83062500330dab368b291241fd8174', 'openai-processing-ms': '6105', 'x-envoy-upstream-service-time': '6109', 'strict-transport-security': 'max-age=31536000; includeSubDomains; preload', 'cf-cache-status': 'DYNAMIC', 'x-content-type-options': 'nosniff', 'server': 'cloudflare', 'cf-ray': '9809f96b8df4c7dd-DUS', 'alt-svc': 'h3=":443"; ma=86400'})
[start-backend] 2025-09-17 18:28:06 - openai._base_client - [DEBUG] - request_id: req_dd83062500330dab368b291241fd8174
[start-backend] 2025-09-17 18:28:06 - openai._base_client - [DEBUG] - Encountered httpx.HTTPStatusError
[start-backend] Traceback (most recent call last):
[start-backend]   File "C:\KI\Janus-Projekt\backend\venv\Lib\site-packages\openai\_base_client.py", line 1574, in request
[start-backend]     response.raise_for_status()
[start-backend]   File "C:\KI\Janus-Projekt\backend\venv\Lib\site-packages\httpx\_models.py", line 829, in raise_for_status
[start-backend]     raise HTTPStatusError(message, request=request, response=self)
[start-backend] httpx.HTTPStatusError: Client error '429 Too Many Requests' for url 'https://api.openai.com/v1/responses'
[start-backend] For more information check: https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/429
[start-backend] 2025-09-17 18:28:06 - openai._base_client - [DEBUG] - Retrying due to status code 429
[start-backend] 2025-09-17 18:28:06 - openai._base_client - [DEBUG] - 1 retry left
[start-backend] 2025-09-17 18:28:06 - openai._base_client - [INFO] - Retrying request to /responses in 0.822013 seconds
[start-backend] 2025-09-17 18:28:07 - openai._base_client - [DEBUG] - Request options: {'method': 'post', 'url': '/responses', 'files': None, 'idempotency_key': 'stainless-python-retry-620c1033-a1f8-4c33-8ba1-77d5333b60ff', 'json_data': {'input': 'F�hre eine Websuche durch und gib eine detaillierte, faktenbasierte Antwort auf die folgende Frage: Preis Nintendo Switch 2', 'model': 'gpt-4o-mini', 'tools': [{'type': 'web_search'}]}}
[start-backend] 2025-09-17 18:28:07 - openai._base_client - [DEBUG] - Sending HTTP Request: POST https://api.openai.com/v1/responses
[start-backend] 2025-09-17 18:28:07 - httpcore.http11 - [DEBUG] - send_request_headers.started request=<Request [b'POST']>
[start-backend] 2025-09-17 18:28:07 - httpcore.http11 - [DEBUG] - send_request_headers.complete
[start-backend] 2025-09-17 18:28:07 - httpcore.http11 - [DEBUG] - send_request_body.started request=<Request [b'POST']>
[start-backend] 2025-09-17 18:28:07 - httpcore.http11 - [DEBUG] - send_request_body.complete
[start-backend] 2025-09-17 18:28:07 - httpcore.http11 - [DEBUG] - receive_response_headers.started request=<Request [b'POST']>
[start-backend] 2025-09-17 18:28:12 - httpcore.http11 - [DEBUG] - receive_response_headers.complete return_value=(b'HTTP/1.1', 429, b'Too Many Requests', [(b'Date', b'Wed, 17 Sep 2025 16:28:13 GMT'), (b'Content-Type', b'application/json'), (b'Content-Length', b'316'), (b'Connection', b'keep-alive'), (b'openai-version', b'2020-10-01'), (b'openai-organization', b'user-9rymi7trhkh9wx0cjpzb4txg'), (b'openai-project', b'proj_xZDNucsxSbdjkba6PitMv58d'), (b'x-request-id', b'req_d4448b158093f84b97d691e6838d35a3'), (b'openai-processing-ms', b'4574'), (b'x-envoy-upstream-service-time', b'4577'), (b'strict-transport-security', b'max-age=31536000; includeSubDomains; preload'), (b'cf-cache-status', b'DYNAMIC'), (b'X-Content-Type-Options', b'nosniff'), (b'Server', b'cloudflare'), (b'CF-RAY', b'9809f997e959c7dd-DUS'), (b'alt-svc', b'h3=":443"; ma=86400')])
[start-backend] 2025-09-17 18:28:12 - httpx - [INFO] - HTTP Request: POST https://api.openai.com/v1/responses "HTTP/1.1 429 Too Many Requests"
[start-backend] 2025-09-17 18:28:12 - httpcore.http11 - [DEBUG] - receive_response_body.started request=<Request [b'POST']>
[start-backend] 2025-09-17 18:28:12 - httpcore.http11 - [DEBUG] - receive_response_body.complete
[start-backend] 2025-09-17 18:28:12 - httpcore.http11 - [DEBUG] - response_closed.started
[start-backend] 2025-09-17 18:28:12 - httpcore.http11 - [DEBUG] - response_closed.complete
[start-backend] 2025-09-17 18:28:12 - openai._base_client - [DEBUG] - HTTP Response: POST https://api.openai.com/v1/responses "429 Too Many Requests" Headers({'date': 'Wed, 17 Sep 2025 16:28:13 GMT', 'content-type': 'application/json', 'content-length': '316', 'connection': 'keep-alive', 'openai-version': '2020-10-01', 'openai-organization': 'user-9rymi7trhkh9wx0cjpzb4txg', 'openai-project': 'proj_xZDNucsxSbdjkba6PitMv58d', 'x-request-id': 'req_d4448b158093f84b97d691e6838d35a3', 'openai-processing-ms': '4574', 'x-envoy-upstream-service-time': '4577', 'strict-transport-security': 'max-age=31536000; includeSubDomains; preload', 'cf-cache-status': 'DYNAMIC', 'x-content-type-options': 'nosniff', 'server': 'cloudflare', 'cf-ray': '9809f997e959c7dd-DUS', 'alt-svc': 'h3=":443"; ma=86400'})
[start-backend] 2025-09-17 18:28:12 - openai._base_client - [DEBUG] - request_id: req_d4448b158093f84b97d691e6838d35a3
[start-backend] 2025-09-17 18:28:12 - openai._base_client - [DEBUG] - Encountered httpx.HTTPStatusError
[start-backend] Traceback (most recent call last):
[start-backend]   File "C:\KI\Janus-Projekt\backend\venv\Lib\site-packages\openai\_base_client.py", line 1574, in request
[start-backend]     response.raise_for_status()
[start-backend]   File "C:\KI\Janus-Projekt\backend\venv\Lib\site-packages\httpx\_models.py", line 829, in raise_for_status
[start-backend]     raise HTTPStatusError(message, request=request, response=self)
[start-backend] httpx.HTTPStatusError: Client error '429 Too Many Requests' for url 'https://api.openai.com/v1/responses'
[start-backend] For more information check: https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/429
[start-backend] 2025-09-17 18:28:12 - openai._base_client - [DEBUG] - Re-raising status error
[start-backend] 2025-09-17 18:28:12 - janus_backend - [ERROR] - Error during OpenAI web search: Error code: 429 - {'error': {'message': 'You exceeded your current quota, please check your plan and billing details. For more information on this error, read the docs: https://platform.openai.com/docs/guides/error-codes/api-errors.', 'type': 'insufficient_quota', 'param': None, 'code': 'insufficient_quota'}}
[start-backend] Traceback (most recent call last):
[start-backend]   File "C:\KI\Janus-Projekt\backend\websearch.py", line 20, in perform_websearch
[start-backend]     response = await openai_client.responses.create(
[start-backend]                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
[start-backend]   File "C:\KI\Janus-Projekt\backend\venv\Lib\site-packages\openai\resources\responses\responses.py", line 2161, in create
[start-backend]     return await self._post(
[start-backend]            ^^^^^^^^^^^^^^^^^
[start-backend]   File "C:\KI\Janus-Projekt\backend\venv\Lib\site-packages\openai\_base_client.py", line 1794, in post
[start-backend]     return await self.request(cast_to, opts, stream=stream, stream_cls=stream_cls)
[start-backend]            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
[start-backend]   File "C:\KI\Janus-Projekt\backend\venv\Lib\site-packages\openai\_base_client.py", line 1594, in request
[start-backend]     raise self._make_status_error_from_response(err.response) from None
[start-backend] openai.RateLimitError: Error code: 429 - {'error': {'message': 'You exceeded your current quota, please check your plan and billing details. For more information on this error, read the docs: https://platform.openai.com/docs/guides/error-codes/api-errors.', 'type': 'insufficient_quota', 'param': None, 'code': 'insufficient_quota'}}
[start-backend] 2025-09-17 18:28:12 - janus_backend - [INFO] - Web search completed. Sending results back to the original LLM for final response.
[start-backend] 2025-09-17 18:28:12 - grpc._cython.cygrpc - [DEBUG] - Using AsyncIOEngine.POLLER as I/O engine
[start-backend] 2025-09-17 18:28:13 - janus_backend - [INFO] -
[start-backend] --- USAGE TRACKING ---
[start-backend] Model: gemini-2.5-flash
[start-backend] Input Tokens: 0
[start-backend] Output Tokens: 0
[start-backend] Image Quality: N/A
[start-backend] Image Size: N/A
[start-backend] Total Cost: 0.00000000 �
[start-backend] ----------------------
[start-backend] 2025-09-17 18:28:13 - janus_backend - [INFO] - Final answer before check: 'Ich habe leider keine URLs gefunden.'
[start-backend] INFO:     127.0.0.1:51868 - "POST /api/chat HTTP/1.1" 200 OK
[start-backend] INFO:     127.0.0.1:51868 - "GET /api/costs/dashboard HTTP/1.1" 200 OK
[start-backend] 2025-09-17 18:29:19 - janus_backend - [INFO] - Explizite Werkzeug-Direktive wurde auf den System-Prompt angewendet.
[start-backend] 2025-09-17 18:29:19 - janus_backend - [INFO] - Using persona prompt for 'ai_assistant'
[start-backend] 2025-09-17 18:29:19 - janus_backend - [INFO] - Image generation intent detected by keyword.
[start-backend] 2025-09-17 18:29:19 - janus_backend - [INFO] - Calling Gemini image model 'gemini-2.5-flash-image-preview' with prompt: 'erstelle mir ein bild einer katze' and reference image: False
[start-backend] 2025-09-17 18:29:19 - grpc._cython.cygrpc - [DEBUG] - Using AsyncIOEngine.POLLER as I/O engine
[start-backend] 2025-09-17 18:29:26 - janus_backend - [INFO] - Image saved from bytes to C:\Users\pruve\AppData\Local\JanusDev\Janus Projekt\images\mir-ein-bild-einer-katze-17-09-25.png
[start-backend] 2025-09-17 18:29:26 - janus_backend - [INFO] -
[start-backend] --- USAGE TRACKING ---
[start-backend] Model: gemini-2.5-flash-image-preview
[start-backend] Input Tokens: N/A
[start-backend] Output Tokens: N/A
[start-backend] Image Quality: standard
[start-backend] Image Size: 1024x1024
[start-backend] Total Cost: 0.02000000 �
[start-backend] ----------------------
[start-backend] INFO:     127.0.0.1:52231 - "POST /api/chat HTTP/1.1" 200 OK
[start-backend] INFO:     127.0.0.1:52231 - "GET /api/costs/dashboard HTTP/1.1" 200 OK
[start-backend] INFO:     127.0.0.1:52260 - "GET /user_images/mir-ein-bild-einer-katze-17-09-25.png HTTP/1.1" 200 OK
[start-backend] 2025-09-17 18:29:35 - janus_backend - [INFO] - Image saved from bytes to C:\Users\pruve\AppData\Local\JanusDev\Janus Projekt\images\user-upload-15-17-09-25.png
[start-backend] 2025-09-17 18:29:35 - janus_backend - [INFO] - User-uploaded image saved to: /user_images/user-upload-15-17-09-25.png
[start-backend] 2025-09-17 18:29:35 - janus_backend - [INFO] - Explizite Werkzeug-Direktive wurde auf den System-Prompt angewendet.
[start-backend] 2025-09-17 18:29:35 - janus_backend - [INFO] - Using persona prompt for 'ai_assistant'
[start-backend] 2025-09-17 18:29:35 - janus_backend - [INFO] - [DEBUG] FINAL HYBRID Memory Context Generated (length: 0):
[start-backend] 2025-09-17 18:29:35 - janus_backend - [INFO] - Touched 0 memory snippets to update their relevance.
[start-backend] 2025-09-17 18:29:35 - janus_backend - [INFO] - Image data detected for Gemini. Processing as a multi-modal request.
[start-backend] 2025-09-17 18:29:35 - grpc._cython.cygrpc - [DEBUG] - Using AsyncIOEngine.POLLER as I/O engine
[start-backend] 2025-09-17 18:29:47 - janus_backend - [INFO] -
[start-backend] --- USAGE TRACKING ---
[start-backend] Model: gemini-2.5-flash
[start-backend] Input Tokens: 373
[start-backend] Output Tokens: 49
[start-backend] Total Cost: 0.00012415 �
[start-backend] ----------------------
[start-backend] 2025-09-17 18:29:47 - janus_backend - [INFO] - Final answer before check: 'Ja, das Bild zeigt eine l�chelnde Frau mit langen, welligen, r�tlich-braunen Haaren und hellen Augen, die freundlich in die Kamera blickt; es wurden keine weiteren Fakten zur Verf�gung gestellt.'
[start-backend] 2025-09-17 18:29:47 - janus_backend - [INFO] - [FACT EXTRACTION] Starte Extraktion f�r Chat 1 mit Text: 'User: Gib eine kurze Best�tigung und die wichtigsten Merkmale des Bildes in einem Satz.
[start-backend] Assistant: Ja, das Bild zeigt eine l�chelnde Frau mit langen, welligen, r�tlich-braunen Haaren und hellen Augen, die freundlich in die Kamera blickt; es wurden keine weiteren Fakten zur Verf�gung gestellt.'
[start-backend] INFO:     127.0.0.1:52290 - "POST /api/chat HTTP/1.1" 200 OK
[start-backend] INFO:     127.0.0.1:52290 - "GET /api/costs/dashboard HTTP/1.1" 200 OK
[start-backend] 2025-09-17 18:29:50 - janus_backend - [INFO] -
[start-backend] --- USAGE TRACKING ---
[start-backend] Model: gemini-2.5-flash
[start-backend] Input Tokens: 0
[start-backend] Output Tokens: 0
[start-backend] Image Quality: N/A
[start-backend] Image Size: N/A
[start-backend] Total Cost: 0.00000000 �
[start-backend] ----------------------
[start-backend] 2025-09-17 18:29:50 - janus_backend - [INFO] - Extracted text: 'Keine.'
[start-backend] 2025-09-17 18:29:50 - janus_backend - [INFO] - Kein relevanter Fakt im Textblock gefunden.
[start-backend] 2025-09-17 18:30:17 - janus_backend - [INFO] - Explizite Werkzeug-Direktive wurde auf den System-Prompt angewendet.
[start-backend] 2025-09-17 18:30:17 - janus_backend - [INFO] - Using persona prompt for 'ai_assistant'
[start-backend] 2025-09-17 18:30:17 - janus_backend - [INFO] - [DEBUG] FINAL HYBRID Memory Context Generated (length: 0):
[start-backend] 2025-09-17 18:30:17 - janus_backend - [INFO] - Touched 0 memory snippets to update their relevance.
[start-backend] 2025-09-17 18:30:20 - janus_backend - [INFO] - Gemini requested tool call: create_file_tool with args: {'content': 'Ja, das Bild zeigt eine l�chelnde Frau mit langen, welligen, r�tlich-braunen Haaren und hellen Augen, die freundlich in die Kamera blickt; es wurden keine weiteren Fakten zur Verf�gung gestellt.', 'path': 'C:\\Users\\pruve\\Desktop\\bildbeschreibung.txt'}
[start-backend] 2025-09-17 18:30:20 - janus_backend - [INFO] -
[start-backend] --- USAGE TRACKING ---
[start-backend] Model: gemini-2.5-flash
[start-backend] Input Tokens: 0
[start-backend] Output Tokens: 0
[start-backend] Image Quality: N/A
[start-backend] Image Size: N/A
[start-backend] Total Cost: 0.00000000 �
[start-backend] ----------------------
[start-backend] 2025-09-17 18:30:20 - janus_backend - [WARNING] - Unknown tool call: create_file_tool for provider: gemini
[start-backend] 2025-09-17 18:30:20 - janus_backend - [INFO] - Executing tool 'create_file_tool' with args: {'content': 'Ja, das Bild zeigt eine l�chelnde Frau mit langen, welligen, r�tlich-braunen Haaren und hellen Augen, die freundlich in die Kamera blickt; es wurden keine weiteren Fakten zur Verf�gung gestellt.', 'path': 'C:\\Users\\pruve\\Desktop\\bildbeschreibung.txt'}
[start-backend] 2025-09-17 18:30:20 - janus_backend - [INFO] - Datei erstellt: C:\Users\pruve\Desktop\bildbeschreibung.txt
[start-backend] 2025-09-17 18:30:20 - janus_backend - [INFO] - Final answer before check: 'Ergebnis von Tool 'create_file_tool': {
[start-backend]   "output": "Datei 'C:\\Users\\pruve\\Desktop\\bildbeschreibung.txt' wurde erfolgreich erstellt."
[start-backend] }'
[start-backend] INFO:     127.0.0.1:52441 - "POST /api/chat HTTP/1.1" 200 OK
[start-backend] INFO:     127.0.0.1:52441 - "GET /api/costs/dashboard HTTP/1.1" 200 OK