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
[start-backend] INFO:     Started reloader process [24236] using WatchFiles
[start-backend] 2025-09-17 21:14:51 - janus_backend - [INFO] - Logger wurde initialisiert.
[start-frontend] [0]
[start-frontend] [0] > janus-projekt@1.1.0 start-electron
[start-frontend] [0] > wait-on tcp:8001 && cross-env NODE_ENV=development electron .
[start-frontend] [0]
[start-frontend] [1]
[start-frontend] [1] > janus-projekt@1.1.0 start-vite
[start-frontend] [1] > vite
[start-frontend] [1]
[start-backend] 2025-09-17 21:14:51 - keyring.backend - [DEBUG] - Loading KWallet
[start-backend] 2025-09-17 21:14:51 - keyring.backend - [DEBUG] - Loading SecretService
[start-backend] 2025-09-17 21:14:51 - keyring.backend - [DEBUG] - Loading Windows
[start-backend] 2025-09-17 21:14:51 - win32ctypes.core.ctypes - [DEBUG] - Loaded ctypes backend
[start-backend] 2025-09-17 21:14:51 - keyring.backend - [DEBUG] - Loading chainer
[start-backend] 2025-09-17 21:14:51 - keyring.backend - [DEBUG] - Loading libsecret
[start-backend] 2025-09-17 21:14:51 - keyring.backend - [DEBUG] - Loading macOS
[start-backend] 2025-09-17 21:14:51 - janus_backend - [INFO] - OpenAI API key loaded from keyring and set as environment variable.
[start-frontend] [1] The CJS build of Vite's Node API is deprecated. See https://vite.dev/guide/troubleshooting.html#vite-cjs-node-api-deprecated for more details.
[start-frontend] [1]
[start-frontend] [1]   VITE v5.4.19  ready in 290 ms
[start-frontend] [1]
[start-frontend] [1]   ➜  Local:   http://localhost:5173/
[start-frontend] [1]   ➜  Network: use --host to expose
[start-backend] 2025-09-17 21:14:54 - janus_backend - [INFO] - Logger wurde initialisiert.
[start-backend] 2025-09-17 21:14:54 - janus_backend - [INFO] - Logger wurde initialisiert.
[start-backend] 2025-09-17 21:15:00 - sentence_transformers.SentenceTransformer - [INFO] - Use pytorch device_name: cpu
[start-backend] 2025-09-17 21:15:00 - sentence_transformers.SentenceTransformer - [INFO] - Load pretrained SentenceTransformer: C:\KI\Janus-Projekt\backend/model_cache/all-MiniLM-L6-v2
[start-backend] 2025-09-17 21:15:00 - janus_backend - [INFO] - Application Data Directory: C:\Users\pruve\AppData\Local\JanusDev\Janus Projekt
[start-backend] INFO:     Started server process [3708]
[start-backend] INFO:     Waiting for application startup.
[start-backend] 2025-09-17 21:15:00 - janus_backend - [INFO] - Scheduling initial memory maintenance tasks on startup.
[start-backend] 2025-09-17 21:15:00 - janus_backend - [INFO] - Background memory archival task starting.
[start-backend] 2025-09-17 21:15:00 - janus_backend - [INFO] - STM size (0) is within limit (250). No archival needed.
[start-backend] 2025-09-17 21:15:00 - janus_backend - [INFO] - Background memory archival task finished successfully.
[start-backend] 2025-09-17 21:15:00 - janus_backend - [INFO] - Background memory pruning task starting.
[start-backend] 2025-09-17 21:15:00 - janus_backend - [INFO] - No expired memories to prune.
[start-backend] INFO:     Application startup complete.
[start-backend] 2025-09-17 21:15:00 - janus_backend - [INFO] - Background memory pruning task finished successfully.
[start-frontend] [0]
[start-frontend] [0] Main process: Script started (Root main.electron.js)
[start-frontend] [0] Main process: ipcMain.handle registered for save-image
[start-frontend] [0] Main process: createWindow called
[start-frontend] [0] [Main Process] Attempting to load preload script from: C:\KI\Janus-Projekt\frontend\preload.js
[start-backend] INFO:     127.0.0.1:64981 - "GET /api/models/catalog HTTP/1.1" 200 OK
[start-frontend] [0] [Electron Main] Backend is ready!
[start-backend] INFO:     127.0.0.1:64989 - "GET /api/models/catalog HTTP/1.1" 200 OK
[start-backend] INFO:     127.0.0.1:64990 - "GET /api/personalities HTTP/1.1" 200 OK
[start-backend] INFO:     127.0.0.1:64989 - "GET /api/models/catalog HTTP/1.1" 200 OK
[start-backend] 2025-09-17 21:15:01 - janus_backend - [INFO] - Attempting to retrieve API keys.
[start-backend] 2025-09-17 21:15:01 - janus_backend - [INFO] - Successfully retrieved API key for provider: openai
[start-backend] 2025-09-17 21:15:01 - janus_backend - [INFO] - Successfully retrieved API key for provider: gemini
[start-backend] 2025-09-17 21:15:01 - janus_backend - [INFO] - No API key found for provider: anthropic
[start-backend] 2025-09-17 21:15:01 - janus_backend - [INFO] - No API key found for provider: cohere
[start-backend] INFO:     127.0.0.1:64990 - "GET /api/keys HTTP/1.1" 200 OK
[start-backend] INFO:     127.0.0.1:64989 - "GET /api/last-used-model HTTP/1.1" 200 OK
[start-backend] INFO:     127.0.0.1:64991 - "GET /api/personalities/active HTTP/1.1" 200 OK
[start-backend] 2025-09-17 21:15:01 - janus_backend - [INFO] - Attempting to retrieve API keys.
[start-backend] 2025-09-17 21:15:01 - janus_backend - [INFO] - Successfully retrieved API key for provider: openai
[start-backend] 2025-09-17 21:15:01 - janus_backend - [INFO] - Successfully retrieved API key for provider: gemini
[start-backend] 2025-09-17 21:15:01 - janus_backend - [INFO] - No API key found for provider: anthropic
[start-backend] 2025-09-17 21:15:01 - janus_backend - [INFO] - No API key found for provider: cohere
[start-backend] INFO:     127.0.0.1:64990 - "GET /api/keys HTTP/1.1" 200 OK
[start-backend] INFO:     127.0.0.1:64989 - "GET /api/models/selection/openai HTTP/1.1" 200 OK
[start-backend] INFO:     127.0.0.1:64991 - "GET /api/personalities/active HTTP/1.1" 200 OK
[start-backend] INFO:     127.0.0.1:64992 - "GET /api/personalities HTTP/1.1" 200 OK
[start-backend] INFO:     127.0.0.1:64991 - "GET /api/models/selection/gemini HTTP/1.1" 200 OK
[start-frontend] [0] [23880:0917/211501.951:ERROR:CONSOLE(1)] "Request Autofill.enable failed. {"code":-32601,"message":"'Autofill.enable' wasn't found"}", source: devtools://devtools/bundled/core/protocol_client/protocol_client.js (1)
[start-frontend] [0] [23880:0917/211501.952:ERROR:CONSOLE(1)] "Request Autofill.setAddresses failed. {"code":-32601,"message":"'Autofill.setAddresses' wasn't found"}", source: devtools://devtools/bundled/core/protocol_client/protocol_client.js (1)
[start-backend] INFO:     127.0.0.1:64992 - "GET /api/costs/dashboard HTTP/1.1" 200 OK
[start-backend] INFO:     127.0.0.1:64991 - "GET /api/chats?include_archived=false HTTP/1.1" 200 OK
[start-backend] INFO:     127.0.0.1:64991 - "OPTIONS /api/chats HTTP/1.1" 200 OK
[start-backend] INFO:     127.0.0.1:64992 - "POST /api/chats HTTP/1.1" 200 OK
[start-backend] INFO:     127.0.0.1:64992 - "GET /api/chats?include_archived=false HTTP/1.1" 200 OK
[start-backend] INFO:     127.0.0.1:64992 - "GET /api/chats/1 HTTP/1.1" 200 OK
[start-backend] INFO:     127.0.0.1:64992 - "GET /api/chats/1 HTTP/1.1" 200 OK
[start-backend] INFO:     127.0.0.1:64991 - "GET /api/chats/1/messages HTTP/1.1" 200 OK
[start-backend] INFO:     127.0.0.1:64991 - "GET /api/chats/1/messages HTTP/1.1" 200 OK
[start-backend] INFO:     127.0.0.1:65208 - "OPTIONS /api/chats/1/title HTTP/1.1" 200 OK
[start-backend] INFO:     127.0.0.1:65208 - "PUT /api/chats/1/title HTTP/1.1" 200 OK
[start-backend] INFO:     127.0.0.1:65208 - "GET /api/chats?include_archived=false HTTP/1.1" 200 OK
[start-backend] INFO:     127.0.0.1:65208 - "OPTIONS /api/chat HTTP/1.1" 200 OK
[start-backend] 2025-09-17 21:15:48 - janus_backend - [INFO] - No new image uploaded. Checking history for existing image context.
[start-backend] 2025-09-17 21:15:48 - janus_backend - [INFO] - Explizite Werkzeug-Direktive wurde auf den System-Prompt angewendet.
[start-backend] 2025-09-17 21:15:48 - janus_backend - [INFO] - Using persona prompt for 'ai_assistant'
[start-backend] 2025-09-17 21:15:48 - grpc._cython.cygrpc - [DEBUG] - Using AsyncIOEngine.POLLER as I/O engine
[start-backend] 2025-09-17 21:15:50 - janus_backend - [INFO] -
[start-backend] --- USAGE TRACKING ---
[start-backend] Model: gemini-2.5-flash
[start-backend] Input Tokens: 0
[start-backend] Output Tokens: 0
[start-backend] Image Quality: N/A
[start-backend] Image Size: N/A
[start-backend] Total Cost: 0.00000000 �
[start-backend] ----------------------
[start-backend] 2025-09-17 21:15:50 - janus_backend - [INFO] - Final answer before check: 'Hallo! Ich bin dein pers�nlicher KI-Assistent. Ich unterst�tze dich bei Aufgaben im Alltag � von Planung �ber Recherche bis Umsetzung. Womit starten wir?'
[start-backend] INFO:     127.0.0.1:65208 - "POST /api/chat HTTP/1.1" 200 OK
[start-backend] INFO:     127.0.0.1:65208 - "GET /api/costs/dashboard HTTP/1.1" 200 OK
[start-backend] 2025-09-17 21:16:00 - janus_backend - [INFO] - No new image uploaded. Checking history for existing image context.
[start-backend] 2025-09-17 21:16:00 - janus_backend - [INFO] - Task-oriented prompt detected (file ops/web search). Suppressing visual context to ensure tool usage.
[start-backend] 2025-09-17 21:16:00 - janus_backend - [INFO] - Explizite Werkzeug-Direktive wurde auf den System-Prompt angewendet.
[start-backend] 2025-09-17 21:16:00 - janus_backend - [INFO] - Using persona prompt for 'ai_assistant'
[start-backend] 2025-09-17 21:16:00 - janus_backend - [INFO] - [DEBUG] FINAL HYBRID Memory Context Generated (length: 0):
[start-backend] 2025-09-17 21:16:00 - janus_backend - [INFO] - Touched 0 memory snippets to update their relevance.
[start-backend] 2025-09-17 21:16:00 - grpc._cython.cygrpc - [DEBUG] - Using AsyncIOEngine.POLLER as I/O engine
[start-backend] 2025-09-17 21:16:01 - janus_backend - [INFO] - Gemini requested tool call: perform_websearch with args: {'query': 'Preis Nintendo Switch 2'}
[start-backend] 2025-09-17 21:16:01 - janus_backend - [INFO] -
[start-backend] --- USAGE TRACKING ---
[start-backend] Model: gemini-2.5-flash
[start-backend] Input Tokens: 0
[start-backend] Output Tokens: 0
[start-backend] Image Quality: N/A
[start-backend] Image Size: N/A
[start-backend] Total Cost: 0.00000000 �
[start-backend] ----------------------
[start-backend] 2025-09-17 21:16:01 - janus_backend - [INFO] - Gemini requested Google Search with query: Preis Nintendo Switch 2
[start-backend] 2025-09-17 21:16:01 - janus_backend - [INFO] - Web search requested for Gemini. Using direct REST API call.
[start-backend] 2025-09-17 21:16:01 - janus_backend - [INFO] - Gemini Web Search Payload: {
[start-backend]   "contents": [
[start-backend]     {
[start-backend]       "role": "user",
[start-backend]       "parts": [
[start-backend]         {
[start-backend]           "text": "weiviel kostet aktuell die switch 2?"
[start-backend]         }
[start-backend]       ]
[start-backend]     }
[start-backend]   ],
[start-backend]   "tools": [
[start-backend]     {
[start-backend]       "google_search": {}
[start-backend]     }
[start-backend]   ],
[start-backend]   "systemInstruction": {
[start-backend]     "parts": [
[start-backend]       {
[start-backend]         "text": "Du bist Janus, ein hilfreicher und freundlicher KI-Assistent. Du antwortest immer auf Deutsch. Integriere nahtlos dein umfangreiches Allgemeinwissen mit den spezifischen Informationen, die im Abschnitt 'GED\u00c4CHTNIS' bereitgestellt werden. **REGEL: Die Informationen im 'GED\u00c4CHTNIS'-Abschnitt haben immer Vorrang und sind die absolute Wahrheit \u00fcber den Benutzer und seine Welt. Beziehe dich bei jeder Antwort explizit darauf, wenn es relevant ist.**"
[start-backend]       }
[start-backend]     ]
[start-backend]   }
[start-backend] }
[start-backend] 2025-09-17 21:16:02 - httpcore.connection - [DEBUG] - connect_tcp.started host='generativelanguage.googleapis.com' port=443 local_address=None timeout=120.0 socket_options=None
[start-backend] 2025-09-17 21:16:02 - httpcore.connection - [DEBUG] - connect_tcp.complete return_value=<httpcore._backends.anyio.AnyIOStream object at 0x00000243D4954510>
[start-backend] 2025-09-17 21:16:02 - httpcore.connection - [DEBUG] - start_tls.started ssl_context=<ssl.SSLContext object at 0x00000243D48C7260> server_hostname='generativelanguage.googleapis.com' timeout=120.0
[start-backend] 2025-09-17 21:16:02 - httpcore.connection - [DEBUG] - start_tls.complete return_value=<httpcore._backends.anyio.AnyIOStream object at 0x00000243D345E8D0>
[start-backend] 2025-09-17 21:16:02 - httpcore.http11 - [DEBUG] - send_request_headers.started request=<Request [b'POST']>
[start-backend] 2025-09-17 21:16:02 - httpcore.http11 - [DEBUG] - send_request_headers.complete
[start-backend] 2025-09-17 21:16:02 - httpcore.http11 - [DEBUG] - send_request_body.started request=<Request [b'POST']>
[start-backend] 2025-09-17 21:16:02 - httpcore.http11 - [DEBUG] - send_request_body.complete
[start-backend] 2025-09-17 21:16:02 - httpcore.http11 - [DEBUG] - receive_response_headers.started request=<Request [b'POST']>
[start-backend] 2025-09-17 21:16:10 - httpcore.http11 - [DEBUG] - receive_response_headers.complete return_value=(b'HTTP/1.1', 200, b'OK', [(b'Content-Type', b'application/json; charset=UTF-8'), (b'Vary', b'Origin'), (b'Vary', b'X-Origin'), (b'Vary', b'Referer'), (b'Content-Encoding', b'gzip'), (b'Date', b'Wed, 17 Sep 2025 19:16:13 GMT'), (b'Server', b'scaffolding on HTTPServer2'), (b'X-XSS-Protection', b'0'), (b'X-Frame-Options', b'SAMEORIGIN'), (b'X-Content-Type-Options', b'nosniff'), (b'Server-Timing', b'gfet4t7; dur=8877'), (b'Alt-Svc', b'h3=":443"; ma=2592000,h3-29=":443"; ma=2592000'), (b'Transfer-Encoding', b'chunked')])
[start-backend] 2025-09-17 21:16:10 - httpx - [INFO] - HTTP Request: POST https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key=AIzaSyCj0ruf57e_IdxpnpoSq_0AhbGtRJq7_PE "HTTP/1.1 200 OK"
[start-backend] 2025-09-17 21:16:10 - httpcore.http11 - [DEBUG] - receive_response_body.started request=<Request [b'POST']>
[start-backend] 2025-09-17 21:16:10 - httpcore.http11 - [DEBUG] - receive_response_body.complete
[start-backend] 2025-09-17 21:16:10 - httpcore.http11 - [DEBUG] - response_closed.started
[start-backend] 2025-09-17 21:16:10 - httpcore.http11 - [DEBUG] - response_closed.complete
[start-backend] 2025-09-17 21:16:10 - httpcore.connection - [DEBUG] - close.started
[start-backend] 2025-09-17 21:16:10 - httpcore.connection - [DEBUG] - close.complete
[start-backend] 2025-09-17 21:16:11 - httpcore.connection - [DEBUG] - connect_tcp.started host='vertexaisearch.cloud.google.com' port=443 local_address=None timeout=10 socket_options=None
[start-backend] 2025-09-17 21:16:11 - httpcore.connection - [DEBUG] - connect_tcp.started host='vertexaisearch.cloud.google.com' port=443 local_address=None timeout=10 socket_options=None
[start-backend] 2025-09-17 21:16:11 - httpcore.connection - [DEBUG] - connect_tcp.started host='vertexaisearch.cloud.google.com' port=443 local_address=None timeout=10 socket_options=None
[start-backend] 2025-09-17 21:16:11 - httpcore.connection - [DEBUG] - connect_tcp.started host='vertexaisearch.cloud.google.com' port=443 local_address=None timeout=10 socket_options=None
[start-backend] 2025-09-17 21:16:11 - httpcore.connection - [DEBUG] - connect_tcp.started host='vertexaisearch.cloud.google.com' port=443 local_address=None timeout=10 socket_options=None
[start-backend] 2025-09-17 21:16:11 - httpcore.connection - [DEBUG] - connect_tcp.started host='vertexaisearch.cloud.google.com' port=443 local_address=None timeout=10 socket_options=None
[start-backend] 2025-09-17 21:16:11 - httpcore.connection - [DEBUG] - connect_tcp.started host='vertexaisearch.cloud.google.com' port=443 local_address=None timeout=10 socket_options=None
[start-backend] 2025-09-17 21:16:11 - httpcore.connection - [DEBUG] - connect_tcp.started host='vertexaisearch.cloud.google.com' port=443 local_address=None timeout=10 socket_options=None
[start-backend] 2025-09-17 21:16:11 - httpcore.connection - [DEBUG] - connect_tcp.complete return_value=<httpcore._backends.anyio.AnyIOStream object at 0x00000243D4AB0790>
[start-backend] 2025-09-17 21:16:11 - httpcore.connection - [DEBUG] - start_tls.started ssl_context=<ssl.SSLContext object at 0x00000243D48C7530> server_hostname='vertexaisearch.cloud.google.com' timeout=10
[start-backend] 2025-09-17 21:16:11 - httpcore.connection - [DEBUG] - connect_tcp.complete return_value=<httpcore._backends.anyio.AnyIOStream object at 0x00000243D4AA57D0>
[start-backend] 2025-09-17 21:16:11 - httpcore.connection - [DEBUG] - start_tls.started ssl_context=<ssl.SSLContext object at 0x00000243D48C7530> server_hostname='vertexaisearch.cloud.google.com' timeout=10
[start-backend] 2025-09-17 21:16:11 - httpcore.connection - [DEBUG] - connect_tcp.complete return_value=<httpcore._backends.anyio.AnyIOStream object at 0x00000243D4AA2A90>
[start-backend] 2025-09-17 21:16:11 - httpcore.connection - [DEBUG] - start_tls.started ssl_context=<ssl.SSLContext object at 0x00000243D48C7530> server_hostname='vertexaisearch.cloud.google.com' timeout=10
[start-backend] 2025-09-17 21:16:11 - httpcore.connection - [DEBUG] - connect_tcp.complete return_value=<httpcore._backends.anyio.AnyIOStream object at 0x00000243D4AA1090>
[start-backend] 2025-09-17 21:16:11 - httpcore.connection - [DEBUG] - start_tls.started ssl_context=<ssl.SSLContext object at 0x00000243D48C7530> server_hostname='vertexaisearch.cloud.google.com' timeout=10
[start-backend] 2025-09-17 21:16:11 - httpcore.connection - [DEBUG] - connect_tcp.complete return_value=<httpcore._backends.anyio.AnyIOStream object at 0x00000243D4AB17D0>
[start-backend] 2025-09-17 21:16:11 - httpcore.connection - [DEBUG] - start_tls.started ssl_context=<ssl.SSLContext object at 0x00000243D48C7530> server_hostname='vertexaisearch.cloud.google.com' timeout=10
[start-backend] 2025-09-17 21:16:11 - httpcore.connection - [DEBUG] - connect_tcp.complete return_value=<httpcore._backends.anyio.AnyIOStream object at 0x00000243D4AA2B90>
[start-backend] 2025-09-17 21:16:11 - httpcore.connection - [DEBUG] - start_tls.started ssl_context=<ssl.SSLContext object at 0x00000243D48C7530> server_hostname='vertexaisearch.cloud.google.com' timeout=10
[start-backend] 2025-09-17 21:16:11 - httpcore.connection - [DEBUG] - connect_tcp.complete return_value=<httpcore._backends.anyio.AnyIOStream object at 0x00000243D4AD5750>
[start-backend] 2025-09-17 21:16:11 - httpcore.connection - [DEBUG] - start_tls.started ssl_context=<ssl.SSLContext object at 0x00000243D48C7530> server_hostname='vertexaisearch.cloud.google.com' timeout=10
[start-backend] 2025-09-17 21:16:11 - httpcore.connection - [DEBUG] - connect_tcp.complete return_value=<httpcore._backends.anyio.AnyIOStream object at 0x00000243D4AA2650>
[start-backend] 2025-09-17 21:16:11 - httpcore.connection - [DEBUG] - start_tls.started ssl_context=<ssl.SSLContext object at 0x00000243D48C7530> server_hostname='vertexaisearch.cloud.google.com' timeout=10
[start-backend] 2025-09-17 21:16:11 - httpcore.connection - [DEBUG] - start_tls.complete return_value=<httpcore._backends.anyio.AnyIOStream object at 0x00000243D4AA1190>
[start-backend] 2025-09-17 21:16:11 - httpcore.http11 - [DEBUG] - send_request_headers.started request=<Request [b'HEAD']>
[start-backend] 2025-09-17 21:16:11 - httpcore.connection - [DEBUG] - start_tls.complete return_value=<httpcore._backends.anyio.AnyIOStream object at 0x00000243D4AB2AD0>
[start-backend] 2025-09-17 21:16:11 - httpcore.http11 - [DEBUG] - send_request_headers.complete
[start-backend] 2025-09-17 21:16:11 - httpcore.http11 - [DEBUG] - send_request_body.started request=<Request [b'HEAD']>
[start-backend] 2025-09-17 21:16:11 - httpcore.http11 - [DEBUG] - send_request_body.complete
[start-backend] 2025-09-17 21:16:11 - httpcore.http11 - [DEBUG] - receive_response_headers.started request=<Request [b'HEAD']>
[start-backend] 2025-09-17 21:16:11 - httpcore.http11 - [DEBUG] - send_request_headers.started request=<Request [b'HEAD']>
[start-backend] 2025-09-17 21:16:11 - httpcore.http11 - [DEBUG] - send_request_headers.complete
[start-backend] 2025-09-17 21:16:11 - httpcore.http11 - [DEBUG] - send_request_body.started request=<Request [b'HEAD']>
[start-backend] 2025-09-17 21:16:11 - httpcore.http11 - [DEBUG] - send_request_body.complete
[start-backend] 2025-09-17 21:16:11 - httpcore.http11 - [DEBUG] - receive_response_headers.started request=<Request [b'HEAD']>
[start-backend] 2025-09-17 21:16:11 - httpcore.connection - [DEBUG] - start_tls.complete return_value=<httpcore._backends.anyio.AnyIOStream object at 0x00000243D4AA2D50>
[start-backend] 2025-09-17 21:16:11 - httpcore.http11 - [DEBUG] - send_request_headers.started request=<Request [b'HEAD']>
[start-backend] 2025-09-17 21:16:11 - httpcore.connection - [DEBUG] - start_tls.complete return_value=<httpcore._backends.anyio.AnyIOStream object at 0x00000243D4AA5650>
[start-backend] 2025-09-17 21:16:11 - httpcore.http11 - [DEBUG] - send_request_headers.complete
[start-backend] 2025-09-17 21:16:11 - httpcore.http11 - [DEBUG] - send_request_body.started request=<Request [b'HEAD']>
[start-backend] 2025-09-17 21:16:11 - httpcore.http11 - [DEBUG] - send_request_body.complete
[start-backend] 2025-09-17 21:16:11 - httpcore.http11 - [DEBUG] - receive_response_headers.started request=<Request [b'HEAD']>
[start-backend] 2025-09-17 21:16:11 - httpcore.http11 - [DEBUG] - send_request_headers.started request=<Request [b'HEAD']>
[start-backend] 2025-09-17 21:16:11 - httpcore.http11 - [DEBUG] - send_request_headers.complete
[start-backend] 2025-09-17 21:16:11 - httpcore.http11 - [DEBUG] - send_request_body.started request=<Request [b'HEAD']>
[start-backend] 2025-09-17 21:16:11 - httpcore.http11 - [DEBUG] - send_request_body.complete
[start-backend] 2025-09-17 21:16:11 - httpcore.http11 - [DEBUG] - receive_response_headers.started request=<Request [b'HEAD']>
[start-backend] 2025-09-17 21:16:11 - httpcore.connection - [DEBUG] - start_tls.complete return_value=<httpcore._backends.anyio.AnyIOStream object at 0x00000243D4AA2750>
[start-backend] 2025-09-17 21:16:11 - httpcore.http11 - [DEBUG] - send_request_headers.started request=<Request [b'HEAD']>
[start-backend] 2025-09-17 21:16:11 - httpcore.connection - [DEBUG] - start_tls.complete return_value=<httpcore._backends.anyio.AnyIOStream object at 0x00000243D4AB18D0>
[start-backend] 2025-09-17 21:16:11 - httpcore.connection - [DEBUG] - start_tls.complete return_value=<httpcore._backends.anyio.AnyIOStream object at 0x00000243D4AA29D0>
[start-backend] 2025-09-17 21:16:11 - httpcore.connection - [DEBUG] - start_tls.complete return_value=<httpcore._backends.anyio.AnyIOStream object at 0x00000243D4AB2790>
[start-backend] 2025-09-17 21:16:11 - httpcore.http11 - [DEBUG] - send_request_headers.complete
[start-backend] 2025-09-17 21:16:11 - httpcore.http11 - [DEBUG] - send_request_body.started request=<Request [b'HEAD']>
[start-backend] 2025-09-17 21:16:11 - httpcore.http11 - [DEBUG] - send_request_body.complete
[start-backend] 2025-09-17 21:16:11 - httpcore.http11 - [DEBUG] - receive_response_headers.started request=<Request [b'HEAD']>
[start-backend] 2025-09-17 21:16:11 - httpcore.http11 - [DEBUG] - send_request_headers.started request=<Request [b'HEAD']>
[start-backend] 2025-09-17 21:16:11 - httpcore.http11 - [DEBUG] - send_request_headers.started request=<Request [b'HEAD']>
[start-backend] 2025-09-17 21:16:11 - httpcore.http11 - [DEBUG] - send_request_headers.started request=<Request [b'HEAD']>
[start-backend] 2025-09-17 21:16:11 - httpcore.http11 - [DEBUG] - send_request_headers.complete
[start-backend] 2025-09-17 21:16:11 - httpcore.http11 - [DEBUG] - send_request_body.started request=<Request [b'HEAD']>
[start-backend] 2025-09-17 21:16:11 - httpcore.http11 - [DEBUG] - send_request_body.complete
[start-backend] 2025-09-17 21:16:11 - httpcore.http11 - [DEBUG] - receive_response_headers.started request=<Request [b'HEAD']>
[start-backend] 2025-09-17 21:16:11 - httpcore.http11 - [DEBUG] - send_request_headers.complete
[start-backend] 2025-09-17 21:16:11 - httpcore.http11 - [DEBUG] - send_request_body.started request=<Request [b'HEAD']>
[start-backend] 2025-09-17 21:16:11 - httpcore.http11 - [DEBUG] - send_request_body.complete
[start-backend] 2025-09-17 21:16:11 - httpcore.http11 - [DEBUG] - receive_response_headers.started request=<Request [b'HEAD']>
[start-backend] 2025-09-17 21:16:11 - httpcore.http11 - [DEBUG] - send_request_headers.complete
[start-backend] 2025-09-17 21:16:11 - httpcore.http11 - [DEBUG] - send_request_body.started request=<Request [b'HEAD']>
[start-backend] 2025-09-17 21:16:11 - httpcore.http11 - [DEBUG] - send_request_body.complete
[start-backend] 2025-09-17 21:16:11 - httpcore.http11 - [DEBUG] - receive_response_headers.started request=<Request [b'HEAD']>
[start-backend] 2025-09-17 21:16:11 - httpcore.http11 - [DEBUG] - receive_response_headers.complete return_value=(b'HTTP/1.1', 302, b'Found', [(b'Location', b'https://www.gamestar.de/artikel/nintendo-switch-2-release-specs-preis-alle-infos-geruechte,3401147.html'), (b'X-Robots-Tag', b'noindex'), (b'Content-Security-Policy-Report-Only', b"script-src 'none'; form-action 'none'; frame-src 'none'; report-uri https://csp.withgoogle.com/csp/scaffolding/cdmldeutrc:183:0"), (b'Cross-Origin-Opener-Policy-Report-Only', b'same-origin; report-to=cdmldeutrc:183:0'), (b'Report-To', b'{"group":"cdmldeutrc:183:0","max_age":2592000,"endpoints":[{"url":"https://csp.withgoogle.com/csp/report-to/scaffolding/cdmldeutrc:183:0"}],}'), (b'Date', b'Wed, 17 Sep 2025 19:16:13 GMT'), (b'Content-Type', b'text/html; charset=UTF-8'), (b'Server', b'scaffolding on HTTPServer2'), (b'Content-Length', b'300'), (b'X-XSS-Protection', b'0'), (b'X-Frame-Options', b'SAMEORIGIN'), (b'Alt-Svc', b'h3=":443"; ma=2592000,h3-29=":443"; ma=2592000')])
[start-backend] 2025-09-17 21:16:11 - httpx - [INFO] - HTTP Request: HEAD https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQHCRTzV0BqYR7ugXU4xmPfIrjUWuKhhTyYcPDGzOhd6BX59ASquhppMtMFq_QspxOqy3Jok96FaoGzjUIXaB29l94KJ8AWEqbBUnW0uym_W7KkhZDif-1f0ZultO7VJDhlX9RK1MQhltHMi2cDQ1Cwca519oFxDSLr1XEzscCADMY7EcRZJBbSvBZ5qjmtvfhLlpo116o7L-kfpih0qHKxPrqc= "HTTP/1.1 302 Found"
[start-backend] 2025-09-17 21:16:11 - httpcore.http11 - [DEBUG] - receive_response_body.started request=<Request [b'HEAD']>
[start-backend] 2025-09-17 21:16:11 - httpcore.http11 - [DEBUG] - receive_response_body.complete
[start-backend] 2025-09-17 21:16:11 - httpcore.http11 - [DEBUG] - response_closed.started
[start-backend] 2025-09-17 21:16:11 - httpcore.http11 - [DEBUG] - response_closed.complete
[start-backend] 2025-09-17 21:16:11 - httpcore.connection - [DEBUG] - connect_tcp.started host='www.gamestar.de' port=443 local_address=None timeout=10 socket_options=None
[start-backend] 2025-09-17 21:16:11 - httpcore.http11 - [DEBUG] - receive_response_headers.complete return_value=(b'HTTP/1.1', 302, b'Found', [(b'Location', b'https://de.ign.com/nintendo/146166/page/nintendo-switch-2-release-preis-spiele-hardware'), (b'X-Robots-Tag', b'noindex'), (b'Content-Security-Policy-Report-Only', b"script-src 'none'; form-action 'none'; frame-src 'none'; report-uri https://csp.withgoogle.com/csp/scaffolding/cdmldeutrc:183:0"), (b'Cross-Origin-Opener-Policy-Report-Only', b'same-origin; report-to=cdmldeutrc:183:0'), (b'Report-To', b'{"group":"cdmldeutrc:183:0","max_age":2592000,"endpoints":[{"url":"https://csp.withgoogle.com/csp/report-to/scaffolding/cdmldeutrc:183:0"}],}'), (b'Date', b'Wed, 17 Sep 2025 19:16:13 GMT'), (b'Content-Type', b'text/html; charset=UTF-8'), (b'Server', b'scaffolding on HTTPServer2'), (b'Content-Length', b'284'), (b'X-XSS-Protection', b'0'), (b'X-Frame-Options', b'SAMEORIGIN'), (b'Alt-Svc', b'h3=":443"; ma=2592000,h3-29=":443"; ma=2592000')])
[start-backend] 2025-09-17 21:16:11 - httpx - [INFO] - HTTP Request: HEAD https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQFNDop7Tao01GGqmewXdgV2eX1NhR86KzCGXZ5bqfOhV7v29THKWwCgeh73sMwJynXPkSy1F487wwNc5EL1IHDYdB6xoMhRcfduBJETCl3qp-VeELn0ZpUFOY8vuEQkQAZH-hYnIuIMjlel1IlVlRgPi2jkhQ_61FxLzJuwMjgXFQvR0RkTWPMvBqPn5ci2_nrPnQ== "HTTP/1.1 302 Found"
[start-backend] 2025-09-17 21:16:11 - httpcore.http11 - [DEBUG] - receive_response_body.started request=<Request [b'HEAD']>
[start-backend] 2025-09-17 21:16:11 - httpcore.http11 - [DEBUG] - receive_response_body.complete
[start-backend] 2025-09-17 21:16:11 - httpcore.http11 - [DEBUG] - response_closed.started
[start-backend] 2025-09-17 21:16:11 - httpcore.http11 - [DEBUG] - response_closed.complete
[start-backend] 2025-09-17 21:16:11 - httpcore.connection - [DEBUG] - connect_tcp.started host='de.ign.com' port=443 local_address=None timeout=10 socket_options=None
[start-backend] 2025-09-17 21:16:11 - httpcore.http11 - [DEBUG] - receive_response_headers.complete return_value=(b'HTTP/1.1', 302, b'Found', [(b'Location', b'https://de.wikipedia.org/wiki/Nintendo_Switch_2'), (b'X-Robots-Tag', b'noindex'), (b'Content-Security-Policy-Report-Only', b"script-src 'none'; form-action 'none'; frame-src 'none'; report-uri https://csp.withgoogle.com/csp/scaffolding/cdmldeutrc:183:0"), (b'Cross-Origin-Opener-Policy-Report-Only', b'same-origin; report-to=cdmldeutrc:183:0'), (b'Report-To', b'{"group":"cdmldeutrc:183:0","max_age":2592000,"endpoints":[{"url":"https://csp.withgoogle.com/csp/report-to/scaffolding/cdmldeutrc:183:0"}],}'), (b'Date', b'Wed, 17 Sep 2025 19:16:13 GMT'), (b'Content-Type', b'text/html; charset=UTF-8'), (b'Server', b'scaffolding on HTTPServer2'), (b'Content-Length', b'244'), (b'X-XSS-Protection', b'0'), (b'X-Frame-Options', b'SAMEORIGIN'), (b'Alt-Svc', b'h3=":443"; ma=2592000,h3-29=":443"; ma=2592000')])
[start-backend] 2025-09-17 21:16:11 - httpx - [INFO] - HTTP Request: HEAD https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQGZAIg5eqSpNevzjIchJC3mlVsymyYYmTrrf4iRFh6Q6mmoosboCPILt7r6qffcgvOQFMqm3msOPfPFkMjkQBMSkQlCBl1jR6t1urrACjIMyb0jSV8P4D5gx_Nv3NTzTZWPE8EOE_jfbaox "HTTP/1.1 302 Found"
[start-backend] 2025-09-17 21:16:11 - httpcore.http11 - [DEBUG] - receive_response_body.started request=<Request [b'HEAD']>
[start-backend] 2025-09-17 21:16:11 - httpcore.http11 - [DEBUG] - receive_response_body.complete
[start-backend] 2025-09-17 21:16:11 - httpcore.http11 - [DEBUG] - response_closed.started
[start-backend] 2025-09-17 21:16:11 - httpcore.http11 - [DEBUG] - response_closed.complete
[start-backend] 2025-09-17 21:16:11 - httpcore.connection - [DEBUG] - connect_tcp.started host='de.wikipedia.org' port=443 local_address=None timeout=10 socket_options=None
[start-backend] 2025-09-17 21:16:11 - httpcore.http11 - [DEBUG] - receive_response_headers.complete return_value=(b'HTTP/1.1', 302, b'Found', [(b'Location', b'https://geizhals.de/nintendo-switch-2-v195471.html'), (b'X-Robots-Tag', b'noindex'), (b'Content-Security-Policy-Report-Only', b"script-src 'none'; form-action 'none'; frame-src 'none'; report-uri https://csp.withgoogle.com/csp/scaffolding/cdmldeutrc:183:0"), (b'Cross-Origin-Opener-Policy-Report-Only', b'same-origin; report-to=cdmldeutrc:183:0'), (b'Report-To', b'{"group":"cdmldeutrc:183:0","max_age":2592000,"endpoints":[{"url":"https://csp.withgoogle.com/csp/report-to/scaffolding/cdmldeutrc:183:0"}],}'), (b'Date', b'Wed, 17 Sep 2025 19:16:13 GMT'), (b'Content-Type', b'text/html; charset=UTF-8'), (b'Server', b'scaffolding on HTTPServer2'), (b'Content-Length', b'247'), (b'X-XSS-Protection', b'0'), (b'X-Frame-Options', b'SAMEORIGIN'), (b'Alt-Svc', b'h3=":443"; ma=2592000,h3-29=":443"; ma=2592000')])
[start-backend] 2025-09-17 21:16:11 - httpx - [INFO] - HTTP Request: HEAD https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQEgJxgBANdzv6P_9Tyq0takx8hHchNw9Y56e6WBPIsDcCy78FFvmyIUPCjla6YVJVuzIsabqrdLhbLLVJs7NeYx49dQlmz5gcUEVySRZw4uKMvPcgcB3RtudR_p7adyxrptFDkJ72ZA5DdtgEqE "HTTP/1.1 302 Found"
[start-backend] 2025-09-17 21:16:11 - httpcore.http11 - [DEBUG] - receive_response_body.started request=<Request [b'HEAD']>
[start-backend] 2025-09-17 21:16:11 - httpcore.http11 - [DEBUG] - receive_response_body.complete
[start-backend] 2025-09-17 21:16:11 - httpcore.http11 - [DEBUG] - response_closed.started
[start-backend] 2025-09-17 21:16:11 - httpcore.http11 - [DEBUG] - response_closed.complete
[start-backend] 2025-09-17 21:16:11 - httpcore.connection - [DEBUG] - connect_tcp.started host='geizhals.de' port=443 local_address=None timeout=10 socket_options=None
[start-backend] 2025-09-17 21:16:11 - httpcore.http11 - [DEBUG] - receive_response_headers.complete return_value=(b'HTTP/1.1', 302, b'Found', [(b'Location', b'https://www.idealo.de/preisvergleich/OffersOfProduct/206193300_-switch-2-nintendo.html'), (b'X-Robots-Tag', b'noindex'), (b'Content-Security-Policy-Report-Only', b"script-src 'none'; form-action 'none'; frame-src 'none'; report-uri https://csp.withgoogle.com/csp/scaffolding/cdmldeutrc:183:0"), (b'Cross-Origin-Opener-Policy-Report-Only', b'same-origin; report-to=cdmldeutrc:183:0'), (b'Report-To', b'{"group":"cdmldeutrc:183:0","max_age":2592000,"endpoints":[{"url":"https://csp.withgoogle.com/csp/report-to/scaffolding/cdmldeutrc:183:0"}],}'), (b'Date', b'Wed, 17 Sep 2025 19:16:13 GMT'), (b'Content-Type', b'text/html; charset=UTF-8'), (b'Server', b'scaffolding on HTTPServer2'), (b'Content-Length', b'283'), (b'X-XSS-Protection', b'0'), (b'X-Frame-Options', b'SAMEORIGIN'), (b'Alt-Svc', b'h3=":443"; ma=2592000,h3-29=":443"; ma=2592000')])
[start-backend] 2025-09-17 21:16:11 - httpx - [INFO] - HTTP Request: HEAD https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQGZpTC7uIN2CpfrGURQotvMfhF1ZptCLd05W4EuEatFH0wfOASJLv6fjZYsy_NOFweG8w4jZYjgWRrjDe9QpAo_eyhSuy-R7W5dUsJ_Hoj8HbAEjkiNnK1gL2KJHkPEUbmaU8iza_uyhH7zwqCwmTpynTlP_eqYtoJBMLtDvgJhNctB-Hm8pRQoy_RAhvtVPpMc "HTTP/1.1 302 Found"
[start-backend] 2025-09-17 21:16:11 - httpcore.http11 - [DEBUG] - receive_response_body.started request=<Request [b'HEAD']>
[start-backend] 2025-09-17 21:16:11 - httpcore.http11 - [DEBUG] - receive_response_body.complete
[start-backend] 2025-09-17 21:16:11 - httpcore.http11 - [DEBUG] - response_closed.started
[start-backend] 2025-09-17 21:16:11 - httpcore.http11 - [DEBUG] - response_closed.complete
[start-backend] 2025-09-17 21:16:11 - httpcore.connection - [DEBUG] - connect_tcp.started host='www.idealo.de' port=443 local_address=None timeout=10 socket_options=None
[start-backend] 2025-09-17 21:16:11 - httpcore.http11 - [DEBUG] - receive_response_headers.complete return_value=(b'HTTP/1.1', 302, b'Found', [(b'Location', b'https://www.spiegel.de/netzwelt/games/switch-2-nintendo-gibt-release-datum-und-preis-bekannt-a-2f01921b-cd3b-4676-9339-a573539fada1'), (b'X-Robots-Tag', b'noindex'), (b'Content-Security-Policy-Report-Only', b"script-src 'none'; form-action 'none'; frame-src 'none'; report-uri https://csp.withgoogle.com/csp/scaffolding/cdmldeutrc:183:0"), (b'Cross-Origin-Opener-Policy-Report-Only', b'same-origin; report-to=cdmldeutrc:183:0'), (b'Report-To', b'{"group":"cdmldeutrc:183:0","max_age":2592000,"endpoints":[{"url":"https://csp.withgoogle.com/csp/report-to/scaffolding/cdmldeutrc:183:0"}],}'), (b'Date', b'Wed, 17 Sep 2025 19:16:13 GMT'), (b'Content-Type', b'text/html; charset=UTF-8'), (b'Server', b'scaffolding on HTTPServer2'), (b'Content-Length', b'328'), (b'X-XSS-Protection', b'0'), (b'X-Frame-Options', b'SAMEORIGIN'), (b'Alt-Svc', b'h3=":443"; ma=2592000,h3-29=":443"; ma=2592000')])
[start-backend] 2025-09-17 21:16:11 - httpx - [INFO] - HTTP Request: HEAD https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQFbDUTk67YbKh5ZioWKf9zUvjIVoBZgEqY9cyA9jAs4IKVIGGCAym7mVXaK2WmmbcV9e7DDmpB_PHFCDpRjcjFISflLYZB9XBOWwsQHMZVEQcECjTQiO0ZisVDExdnTtmYfFEMIaexqZ5bW0Bm4a2SOt6PXZ35D8iFmRBiyt8MOaUyBs8Y2Y5eIMGrbaZuQEdjsR-ni3-iaClIc-6FWk3GD8gIYMKMDrle4sMP-4XgyBLaLfOBcAcvMtHaURUmU6g== "HTTP/1.1 302 Found"
[start-backend] 2025-09-17 21:16:11 - httpcore.http11 - [DEBUG] - receive_response_body.started request=<Request [b'HEAD']>
[start-backend] 2025-09-17 21:16:11 - httpcore.http11 - [DEBUG] - receive_response_body.complete
[start-backend] 2025-09-17 21:16:11 - httpcore.http11 - [DEBUG] - response_closed.started
[start-backend] 2025-09-17 21:16:11 - httpcore.http11 - [DEBUG] - response_closed.complete
[start-backend] 2025-09-17 21:16:11 - httpcore.http11 - [DEBUG] - receive_response_headers.complete return_value=(b'HTTP/1.1', 302, b'Found', [(b'Location', b'https://www.mediamarkt.de/de/product/_nintendo-switch-2-2989498.html'), (b'X-Robots-Tag', b'noindex'), (b'Content-Security-Policy-Report-Only', b"script-src 'none'; form-action 'none'; frame-src 'none'; report-uri https://csp.withgoogle.com/csp/scaffolding/cdmldeutrc:183:0"), (b'Cross-Origin-Opener-Policy-Report-Only', b'same-origin; report-to=cdmldeutrc:183:0'), (b'Report-To', b'{"group":"cdmldeutrc:183:0","max_age":2592000,"endpoints":[{"url":"https://csp.withgoogle.com/csp/report-to/scaffolding/cdmldeutrc:183:0"}],}'), (b'Date', b'Wed, 17 Sep 2025 19:16:13 GMT'), (b'Content-Type', b'text/html; charset=UTF-8'), (b'Server', b'scaffolding on HTTPServer2'), (b'Content-Length', b'265'), (b'X-XSS-Protection', b'0'), (b'X-Frame-Options', b'SAMEORIGIN'), (b'Alt-Svc', b'h3=":443"; ma=2592000,h3-29=":443"; ma=2592000')])
[start-backend] 2025-09-17 21:16:11 - httpx - [INFO] - HTTP Request: HEAD https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQFHxLzdMeHoMwbiKPDKyH1COAjk93rRHqm-jK1tUsk04tV9sdcyPF68qsclBD8RliZXuBh6yy9RMS91Oo_SISDf9r3Yxy_ZbszPtR27F7k8Rxp_WvjHkHQPpDhe02zgydUOx1WtD-8dJEq7i8N3oRhMiC_Iv8XxDK6JbjoOtxZJ "HTTP/1.1 302 Found"
[start-backend] 2025-09-17 21:16:11 - httpcore.http11 - [DEBUG] - receive_response_body.started request=<Request [b'HEAD']>
[start-backend] 2025-09-17 21:16:11 - httpcore.http11 - [DEBUG] - receive_response_body.complete
[start-backend] 2025-09-17 21:16:11 - httpcore.http11 - [DEBUG] - response_closed.started
[start-backend] 2025-09-17 21:16:11 - httpcore.connection - [DEBUG] - connect_tcp.started host='www.spiegel.de' port=443 local_address=None timeout=10 socket_options=None
[start-backend] 2025-09-17 21:16:11 - httpcore.http11 - [DEBUG] - response_closed.complete
[start-backend] 2025-09-17 21:16:11 - httpcore.connection - [DEBUG] - connect_tcp.started host='www.mediamarkt.de' port=443 local_address=None timeout=10 socket_options=None
[start-backend] 2025-09-17 21:16:11 - httpcore.http11 - [DEBUG] - receive_response_headers.complete return_value=(b'HTTP/1.1', 302, b'Found', [(b'Location', b'https://www.gamepro.de/artikel/nintendo-switch-2-preis-und-termin,3430550.html'), (b'X-Robots-Tag', b'noindex'), (b'Content-Security-Policy-Report-Only', b"script-src 'none'; form-action 'none'; frame-src 'none'; report-uri https://csp.withgoogle.com/csp/scaffolding/cdmldeutrc:183:0"), (b'Cross-Origin-Opener-Policy-Report-Only', b'same-origin; report-to=cdmldeutrc:183:0'), (b'Report-To', b'{"group":"cdmldeutrc:183:0","max_age":2592000,"endpoints":[{"url":"https://csp.withgoogle.com/csp/report-to/scaffolding/cdmldeutrc:183:0"}],}'), (b'Date', b'Wed, 17 Sep 2025 19:16:13 GMT'), (b'Content-Type', b'text/html; charset=UTF-8'), (b'Server', b'scaffolding on HTTPServer2'), (b'Content-Length', b'275'), (b'X-XSS-Protection', b'0'), (b'X-Frame-Options', b'SAMEORIGIN'), (b'Alt-Svc', b'h3=":443"; ma=2592000,h3-29=":443"; ma=2592000')])
[start-backend] 2025-09-17 21:16:11 - httpx - [INFO] - HTTP Request: HEAD https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQEzVDmZLxY3P59W_JhHGeLQ9sxYtphWQIzL72ulKRmG8nxkdDJXHug_8c9b6f5I7U4JGmfeYEN4JnXsiF8MIyYoQNPnORsWS-QZdz-oLJ4dYTEAcZM4L7c43NzvunG4iFFUB4q2pg0sPCaYOekRS9YnaMwKe2E4RMAVYSbGAqYRB1WnW-z4rTy3Qg== "HTTP/1.1 302 Found"
[start-backend] 2025-09-17 21:16:11 - httpcore.http11 - [DEBUG] - receive_response_body.started request=<Request [b'HEAD']>
[start-backend] 2025-09-17 21:16:11 - httpcore.http11 - [DEBUG] - receive_response_body.complete
[start-backend] 2025-09-17 21:16:11 - httpcore.http11 - [DEBUG] - response_closed.started
[start-backend] 2025-09-17 21:16:11 - httpcore.http11 - [DEBUG] - response_closed.complete
[start-backend] 2025-09-17 21:16:11 - httpcore.connection - [DEBUG] - connect_tcp.started host='www.gamepro.de' port=443 local_address=None timeout=10 socket_options=None
[start-backend] 2025-09-17 21:16:11 - httpcore.connection - [DEBUG] - connect_tcp.complete return_value=<httpcore._backends.anyio.AnyIOStream object at 0x00000243D4AF4B50>
[start-backend] 2025-09-17 21:16:11 - httpcore.connection - [DEBUG] - start_tls.started ssl_context=<ssl.SSLContext object at 0x00000243D48C7530> server_hostname='de.ign.com' timeout=10
[start-backend] 2025-09-17 21:16:11 - httpcore.connection - [DEBUG] - connect_tcp.complete return_value=<httpcore._backends.anyio.AnyIOStream object at 0x00000243D4AF5CD0>
[start-backend] 2025-09-17 21:16:11 - httpcore.connection - [DEBUG] - start_tls.started ssl_context=<ssl.SSLContext object at 0x00000243D48C7530> server_hostname='de.wikipedia.org' timeout=10
[start-backend] 2025-09-17 21:16:11 - httpcore.connection - [DEBUG] - connect_tcp.complete return_value=<httpcore._backends.anyio.AnyIOStream object at 0x00000243D4AF6E50>
[start-backend] 2025-09-17 21:16:11 - httpcore.connection - [DEBUG] - start_tls.started ssl_context=<ssl.SSLContext object at 0x00000243D48C7530> server_hostname='geizhals.de' timeout=10
[start-backend] 2025-09-17 21:16:11 - httpcore.connection - [DEBUG] - connect_tcp.complete return_value=<httpcore._backends.anyio.AnyIOStream object at 0x00000243D4AF7F10>
[start-backend] 2025-09-17 21:16:11 - httpcore.connection - [DEBUG] - start_tls.started ssl_context=<ssl.SSLContext object at 0x00000243D48C7530> server_hostname='www.idealo.de' timeout=10
[start-backend] 2025-09-17 21:16:11 - httpcore.connection - [DEBUG] - connect_tcp.complete return_value=<httpcore._backends.anyio.AnyIOStream object at 0x00000243D4AF4210>
[start-backend] 2025-09-17 21:16:11 - httpcore.connection - [DEBUG] - start_tls.started ssl_context=<ssl.SSLContext object at 0x00000243D48C7530> server_hostname='www.gamestar.de' timeout=10
[start-backend] 2025-09-17 21:16:11 - httpcore.connection - [DEBUG] - connect_tcp.complete return_value=<httpcore._backends.anyio.AnyIOStream object at 0x00000243D4B01D10>
[start-backend] 2025-09-17 21:16:11 - httpcore.connection - [DEBUG] - start_tls.started ssl_context=<ssl.SSLContext object at 0x00000243D48C7530> server_hostname='www.spiegel.de' timeout=10
[start-backend] 2025-09-17 21:16:11 - httpcore.connection - [DEBUG] - connect_tcp.complete return_value=<httpcore._backends.anyio.AnyIOStream object at 0x00000243D4B022D0>
[start-backend] 2025-09-17 21:16:11 - httpcore.connection - [DEBUG] - start_tls.started ssl_context=<ssl.SSLContext object at 0x00000243D48C7530> server_hostname='www.mediamarkt.de' timeout=10
[start-backend] 2025-09-17 21:16:11 - httpcore.connection - [DEBUG] - connect_tcp.complete return_value=<httpcore._backends.anyio.AnyIOStream object at 0x00000243D4B03490>
[start-backend] 2025-09-17 21:16:11 - httpcore.connection - [DEBUG] - start_tls.started ssl_context=<ssl.SSLContext object at 0x00000243D48C7530> server_hostname='www.gamepro.de' timeout=10
[start-backend] 2025-09-17 21:16:11 - httpcore.connection - [DEBUG] - start_tls.complete return_value=<httpcore._backends.anyio.AnyIOStream object at 0x00000243D4AF4C50>
[start-backend] 2025-09-17 21:16:11 - httpcore.http11 - [DEBUG] - send_request_headers.started request=<Request [b'HEAD']>
[start-backend] 2025-09-17 21:16:11 - httpcore.http11 - [DEBUG] - send_request_headers.complete
[start-backend] 2025-09-17 21:16:11 - httpcore.http11 - [DEBUG] - send_request_body.started request=<Request [b'HEAD']>
[start-backend] 2025-09-17 21:16:11 - httpcore.http11 - [DEBUG] - send_request_body.complete
[start-backend] 2025-09-17 21:16:11 - httpcore.http11 - [DEBUG] - receive_response_headers.started request=<Request [b'HEAD']>
[start-backend] 2025-09-17 21:16:11 - httpcore.connection - [DEBUG] - start_tls.complete return_value=<httpcore._backends.anyio.AnyIOStream object at 0x00000243D4AF7D90>
[start-backend] 2025-09-17 21:16:11 - httpcore.http11 - [DEBUG] - send_request_headers.started request=<Request [b'HEAD']>
[start-backend] 2025-09-17 21:16:11 - httpcore.http11 - [DEBUG] - send_request_headers.complete
[start-backend] 2025-09-17 21:16:11 - httpcore.http11 - [DEBUG] - send_request_body.started request=<Request [b'HEAD']>
[start-backend] 2025-09-17 21:16:11 - httpcore.http11 - [DEBUG] - send_request_body.complete
[start-backend] 2025-09-17 21:16:11 - httpcore.http11 - [DEBUG] - receive_response_headers.started request=<Request [b'HEAD']>
[start-backend] 2025-09-17 21:16:11 - httpcore.connection - [DEBUG] - start_tls.complete return_value=<httpcore._backends.anyio.AnyIOStream object at 0x00000243D4B03590>
[start-backend] 2025-09-17 21:16:11 - httpcore.connection - [DEBUG] - start_tls.complete return_value=<httpcore._backends.anyio.AnyIOStream object at 0x00000243D4AF6F50>
[start-backend] 2025-09-17 21:16:11 - httpcore.connection - [DEBUG] - start_tls.complete return_value=<httpcore._backends.anyio.AnyIOStream object at 0x00000243D4AF5B90>
[start-backend] 2025-09-17 21:16:11 - httpcore.http11 - [DEBUG] - send_request_headers.started request=<Request [b'HEAD']>
[start-backend] 2025-09-17 21:16:11 - httpcore.http11 - [DEBUG] - send_request_headers.started request=<Request [b'HEAD']>
[start-backend] 2025-09-17 21:16:11 - httpcore.http11 - [DEBUG] - send_request_headers.started request=<Request [b'HEAD']>
[start-backend] 2025-09-17 21:16:11 - httpcore.http11 - [DEBUG] - send_request_headers.complete
[start-backend] 2025-09-17 21:16:11 - httpcore.http11 - [DEBUG] - send_request_body.started request=<Request [b'HEAD']>
[start-backend] 2025-09-17 21:16:11 - httpcore.http11 - [DEBUG] - send_request_body.complete
[start-backend] 2025-09-17 21:16:11 - httpcore.http11 - [DEBUG] - receive_response_headers.started request=<Request [b'HEAD']>
[start-backend] 2025-09-17 21:16:11 - httpcore.http11 - [DEBUG] - send_request_headers.complete
[start-backend] 2025-09-17 21:16:11 - httpcore.http11 - [DEBUG] - send_request_body.started request=<Request [b'HEAD']>
[start-backend] 2025-09-17 21:16:11 - httpcore.http11 - [DEBUG] - send_request_body.complete
[start-backend] 2025-09-17 21:16:11 - httpcore.http11 - [DEBUG] - receive_response_headers.started request=<Request [b'HEAD']>
[start-backend] 2025-09-17 21:16:11 - httpcore.http11 - [DEBUG] - send_request_headers.complete
[start-backend] 2025-09-17 21:16:11 - httpcore.http11 - [DEBUG] - send_request_body.started request=<Request [b'HEAD']>
[start-backend] 2025-09-17 21:16:11 - httpcore.http11 - [DEBUG] - send_request_body.complete
[start-backend] 2025-09-17 21:16:11 - httpcore.http11 - [DEBUG] - receive_response_headers.started request=<Request [b'HEAD']>
[start-backend] 2025-09-17 21:16:11 - httpcore.connection - [DEBUG] - start_tls.complete return_value=<httpcore._backends.anyio.AnyIOStream object at 0x00000243D4AF4310>
[start-backend] 2025-09-17 21:16:11 - httpcore.connection - [DEBUG] - start_tls.complete return_value=<httpcore._backends.anyio.AnyIOStream object at 0x00000243D4B01110>
[start-backend] 2025-09-17 21:16:11 - httpcore.http11 - [DEBUG] - send_request_headers.started request=<Request [b'HEAD']>
[start-backend] 2025-09-17 21:16:11 - httpcore.http11 - [DEBUG] - send_request_headers.started request=<Request [b'HEAD']>
[start-backend] 2025-09-17 21:16:11 - httpcore.http11 - [DEBUG] - send_request_headers.complete
[start-backend] 2025-09-17 21:16:11 - httpcore.http11 - [DEBUG] - send_request_body.started request=<Request [b'HEAD']>
[start-backend] 2025-09-17 21:16:11 - httpcore.http11 - [DEBUG] - send_request_body.complete
[start-backend] 2025-09-17 21:16:11 - httpcore.http11 - [DEBUG] - receive_response_headers.started request=<Request [b'HEAD']>
[start-backend] 2025-09-17 21:16:11 - httpcore.http11 - [DEBUG] - send_request_headers.complete
[start-backend] 2025-09-17 21:16:11 - httpcore.http11 - [DEBUG] - send_request_body.started request=<Request [b'HEAD']>
[start-backend] 2025-09-17 21:16:11 - httpcore.http11 - [DEBUG] - send_request_body.complete
[start-backend] 2025-09-17 21:16:11 - httpcore.http11 - [DEBUG] - receive_response_headers.started request=<Request [b'HEAD']>
[start-backend] 2025-09-17 21:16:11 - httpcore.connection - [DEBUG] - start_tls.complete return_value=<httpcore._backends.anyio.AnyIOStream object at 0x00000243D4B020D0>
[start-backend] 2025-09-17 21:16:11 - httpcore.http11 - [DEBUG] - send_request_headers.started request=<Request [b'HEAD']>
[start-backend] 2025-09-17 21:16:11 - httpcore.http11 - [DEBUG] - send_request_headers.complete
[start-backend] 2025-09-17 21:16:11 - httpcore.http11 - [DEBUG] - send_request_body.started request=<Request [b'HEAD']>
[start-backend] 2025-09-17 21:16:11 - httpcore.http11 - [DEBUG] - send_request_body.complete
[start-backend] 2025-09-17 21:16:11 - httpcore.http11 - [DEBUG] - receive_response_headers.started request=<Request [b'HEAD']>
[start-backend] 2025-09-17 21:16:11 - httpcore.http11 - [DEBUG] - receive_response_headers.complete return_value=(b'HTTP/1.1', 200, b'OK', [(b'date', b'Wed, 17 Sep 2025 14:49:45 GMT'), (b'server', b'ATS/9.2.11'), (b'x-content-type-options', b'nosniff'), (b'content-language', b'de'), (b'accept-ch', b''), (b'last-modified', b'Fri, 12 Sep 2025 13:51:24 GMT'), (b'content-type', b'text/html; charset=UTF-8'), (b'content-encoding', b'gzip'), (b'age', b'15988'), (b'accept-ranges', b'bytes'), (b'vary', b'Accept-Encoding,X-Subdomain,Cookie,Authorization'), (b'x-cache', b'cp3067 hit, cp3067 hit/3'), (b'x-cache-status', b'hit-front'), (b'server-timing', b'cache;desc="hit-front", host;desc="cp3067"'), (b'strict-transport-security', b'max-age=106384710; includeSubDomains; preload'), (b'report-to', b'{ "group": "wm_nel", "max_age": 604800, "endpoints": [{ "url": "https://intake-logging.wikimedia.org/v1/events?stream=w3c.reportingapi.network_error&schema_uri=/w3c/reportingapi/network_error/1.0.0" }] }'), (b'nel', b'{ "report_to": "wm_nel", "max_age": 604800, "failure_fraction": 0.05, "success_fraction": 0.0}'), (b'set-cookie', b'WMF-Last-Access=17-Sep-2025;Path=/;HttpOnly;secure;Expires=Sun, 19 Oct 2025 12:00:00 GMT'), (b'set-cookie', b'WMF-Last-Access-Global=17-Sep-2025;Path=/;Domain=.wikipedia.org;HttpOnly;secure;Expires=Sun, 19 Oct 2025 12:00:00 GMT'), (b'set-cookie', b'WMF-DP=472;Path=/;HttpOnly;secure;Expires=Thu, 18 Sep 2025 00:00:00 GMT'), (b'x-client-ip', b'37.201.154.118'), (b'cache-control', b'private, s-maxage=0, max-age=0, must-revalidate, no-transform'), (b'set-cookie', b'GeoIP=DE:NW:Cologne:50.95:6.94:v4; Path=/; secure; Domain=.wikipedia.org'), (b'set-cookie', b'NetworkProbeLimit=0.001;Path=/;Secure;SameSite=None;Max-Age=3600'), (b'set-cookie', b'WMF-Uniq=kgX_nYvFgKpO_6tK9td0igJxAAAAAFvd08S_GqWvrw2Eg5zHWuOY23jfb3Xl9Ixm;Domain=.wikipedia.org;Path=/;HttpOnly;secure;SameSite=None;Expires=Thu, 17 Sep 2026 00:00:00 GMT'), (b'content-length', b'30942'), (b'x-analytics', b'')])
[start-backend] 2025-09-17 21:16:11 - httpx - [INFO] - HTTP Request: HEAD https://de.wikipedia.org/wiki/Nintendo_Switch_2 "HTTP/1.1 200 OK"
[start-backend] 2025-09-17 21:16:11 - httpcore.http11 - [DEBUG] - receive_response_body.started request=<Request [b'HEAD']>
[start-backend] 2025-09-17 21:16:11 - httpcore.http11 - [DEBUG] - receive_response_body.complete
[start-backend] 2025-09-17 21:16:11 - httpcore.http11 - [DEBUG] - response_closed.started
[start-backend] 2025-09-17 21:16:11 - httpcore.http11 - [DEBUG] - response_closed.complete
[start-backend] 2025-09-17 21:16:11 - httpcore.http11 - [DEBUG] - receive_response_headers.complete return_value=(b'HTTP/1.1', 200, b'OK', [(b'Accept-Ranges', b'bytes'), (b'Cache-Control', b'public,max-age=0,s-maxage=300'), (b'Content-Encoding', b'gzip'), (b'Content-Security-Policy', b"frame-ancestors 'self'"), (b'Content-Type', b'text/html; charset=utf-8'), (b'Date', b'Wed, 17 Sep 2025 18:27:28 GMT'), (b'Strict-Transport-Security', b'max-age=31536000;'), (b'Vary', b'X-Forwarded-Proto, X-Authorized-Sppur, X-Adbrain-Enabled, Accept-Encoding'), (b'X-Cache', b'HIT'), (b'X-Cache-Grace', b'3600.000'), (b'Transfer-Encoding', b'chunked'), (b'Alt-Svc', b'h3=":443"; ma=2592000,h3-29=":443"; ma=2592000'), (b'Via', b'1.1 google')])
[start-backend] 2025-09-17 21:16:11 - httpx - [INFO] - HTTP Request: HEAD https://www.spiegel.de/netzwelt/games/switch-2-nintendo-gibt-release-datum-und-preis-bekannt-a-2f01921b-cd3b-4676-9339-a573539fada1 "HTTP/1.1 200 OK"
[start-backend] 2025-09-17 21:16:11 - httpcore.http11 - [DEBUG] - receive_response_body.started request=<Request [b'HEAD']>
[start-backend] 2025-09-17 21:16:11 - httpcore.http11 - [DEBUG] - receive_response_body.complete
[start-backend] 2025-09-17 21:16:11 - httpcore.http11 - [DEBUG] - response_closed.started
[start-backend] 2025-09-17 21:16:11 - httpcore.http11 - [DEBUG] - response_closed.complete
[start-backend] 2025-09-17 21:16:11 - httpcore.http11 - [DEBUG] - receive_response_headers.complete return_value=(b'HTTP/1.1', 200, b'OK', [(b'Date', b'Wed, 17 Sep 2025 19:16:13 GMT'), (b'Content-Type', b'text/html;charset=UTF-8'), (b'Connection', b'keep-alive'), (b'Content-Encoding', b'gzip'), (b'vary', b'Accept-Encoding'), (b'Last-Modified', b'Wed, 17 Sep 2025 18:57:34 GMT'), (b'CF-Cache-Status', b'HIT'), (b'Expires', b'Wed, 17 Sep 2025 19:16:14 GMT'), (b'Cache-Control', b'public, max-age=1'), (b'Set-Cookie', b'__cf_bm=_oT9Pzo5Xtc2CdFhODl3IHlSVCO_qzwr1FF1cW9_7Vs-1758136573-1.0.1.1-dhn3zt8hBPDPNZl2b_8Ik7wysS4BaTz_rvhtEAPavtRY1QdKDtKFaYcklzvwEDT55hdKzeJ_JAxP2GHpUgDpymz_KawknA9od_JuIbiOLv4; path=/; expires=Wed, 17-Sep-25 19:46:13 GMT; domain=.gamepro.de; HttpOnly; Secure; SameSite=None'), (b'Server', b'cloudflare'), (b'CF-RAY', b'980aefd2384ff943-DUS')])
[start-backend] 2025-09-17 21:16:11 - httpx - [INFO] - HTTP Request: HEAD https://www.gamepro.de/artikel/nintendo-switch-2-preis-und-termin,3430550.html "HTTP/1.1 200 OK"
[start-backend] 2025-09-17 21:16:11 - httpcore.http11 - [DEBUG] - receive_response_body.started request=<Request [b'HEAD']>
[start-backend] 2025-09-17 21:16:11 - httpcore.http11 - [DEBUG] - receive_response_body.complete
[start-backend] 2025-09-17 21:16:11 - httpcore.http11 - [DEBUG] - response_closed.started
[start-backend] 2025-09-17 21:16:11 - httpcore.http11 - [DEBUG] - response_closed.complete
[start-backend] 2025-09-17 21:16:11 - httpcore.http11 - [DEBUG] - receive_response_headers.complete return_value=(b'HTTP/1.1', 200, b'OK', [(b'Date', b'Wed, 17 Sep 2025 19:16:13 GMT'), (b'Content-Type', b'text/html;charset=UTF-8'), (b'Connection', b'keep-alive'), (b'Content-Encoding', b'gzip'), (b'vary', b'Accept-Encoding'), (b'Last-Modified', b'Wed, 17 Sep 2025 19:12:22 GMT'), (b'CF-Cache-Status', b'HIT'), (b'Expires', b'Wed, 17 Sep 2025 19:16:14 GMT'), (b'Cache-Control', b'public, max-age=1'), (b'Set-Cookie', b'__cf_bm=tTOqvs2lxtgWhkPeroeHHmLr25_xUcMsCZk7jKnOju0-1758136573-1.0.1.1-QdSGqjTn13UGOVvYn7LPXn4pNcMdEH35cTuJlnRWMPFgPf8Hcycg4SCtYRyOLznerknORjFH9HZkiOCckT_C7v1cTRNQ5rkd68E2F5hk700; path=/; expires=Wed, 17-Sep-25 19:46:13 GMT; domain=.gamestar.de; HttpOnly; Secure; SameSite=None'), (b'Server', b'cloudflare'), (b'CF-RAY', b'980aefd2489c160f-DUS')])
[start-backend] 2025-09-17 21:16:11 - httpx - [INFO] - HTTP Request: HEAD https://www.gamestar.de/artikel/nintendo-switch-2-release-specs-preis-alle-infos-geruechte,3401147.html "HTTP/1.1 200 OK"
[start-backend] 2025-09-17 21:16:11 - httpcore.http11 - [DEBUG] - receive_response_body.started request=<Request [b'HEAD']>
[start-backend] 2025-09-17 21:16:11 - httpcore.http11 - [DEBUG] - receive_response_body.complete
[start-backend] 2025-09-17 21:16:11 - httpcore.http11 - [DEBUG] - response_closed.started
[start-backend] 2025-09-17 21:16:11 - httpcore.http11 - [DEBUG] - response_closed.complete
[start-backend] 2025-09-17 21:16:11 - httpcore.http11 - [DEBUG] - receive_response_headers.complete return_value=(b'HTTP/1.1', 200, b'OK', [(b'Date', b'Wed, 17 Sep 2025 19:16:13 GMT'), (b'Content-Type', b'text/html; charset=utf-8'), (b'Connection', b'keep-alive'), (b'Content-Encoding', b'gzip'), (b'x-frame-options', b'SAMEORIGIN'), (b'content-security-policy', b"frame-ancestors 'self' *.geizhals.de;"), (b'accept-ch', b'Sec-CH-UA-Model,Sec-CH-UA-Platform-Version,Sec-CH-UA-Full-Version-List'), (b'expires', b'Sun, 14 Sep 2025 19:16:13 GMT'), (b'Cache-Control', b'no-cache, no-store, private'), (b'Set-Cookie', b'csrf=C7004A7C-93FA-11F0-8D2E-8F7856B0D36F--63d9e8e6e9972b0986e2d6521732e10fc5c57395; path=/; secure; HttpOnly; SameSite=Lax'), (b'Set-Cookie', b'GHS=aFF8hqreYsdqzpwJm7U5P9DMuL4; path=/; secure; SameSite=Lax'), (b'Set-Cookie', b'__cf_bm=blpn29Q6MCbTfnUNZ96QBqmmftp6OIQ6rUOonMAhKeo-1758136573-1.0.1.1-tv3nRTwx_8V0XnLxJQHZl_sdj8tGkGSPqEP.PlX8U77RI9Rtg2LLELBq1pBOX.dSfXclnuyxekfF0dS1O7w_Rs5Y_KoTXhcn6HNu92OzsL8; path=/; expires=Wed, 17-Sep-25 19:46:13 GMT; domain=.geizhals.de; HttpOnly; Secure; SameSite=None'), (b'Set-Cookie', b'_cfuvid=Bo0FX5t9P_PNNvCaUCEYO9nW42YuctOXlKgEZ0CWxiA-1758136573842-0.0.1.1-604800000; path=/; domain=.geizhals.de; HttpOnly; Secure; SameSite=None'), (b'link', b'<https://gzhls.at>; rel="preconnect"'), (b'x-ua-device', b'pc'), (b'vary', b'User-Agent, Accept-Encoding'), (b'server-gh', b'GH61'), (b'strict-transport-security', b'max-age=15552000'), (b'cf-cache-status', b'DYNAMIC'), (b'Server', b'cloudflare'), (b'CF-RAY', b'980aefd24e4d7169-DUS')])
[start-backend] 2025-09-17 21:16:11 - httpx - [INFO] - HTTP Request: HEAD https://geizhals.de/nintendo-switch-2-v195471.html "HTTP/1.1 200 OK"
[start-backend] 2025-09-17 21:16:11 - httpcore.http11 - [DEBUG] - receive_response_body.started request=<Request [b'HEAD']>
[start-backend] 2025-09-17 21:16:11 - httpcore.http11 - [DEBUG] - receive_response_body.complete
[start-backend] 2025-09-17 21:16:11 - httpcore.http11 - [DEBUG] - response_closed.started
[start-backend] 2025-09-17 21:16:11 - httpcore.http11 - [DEBUG] - response_closed.complete
[start-backend] 2025-09-17 21:16:11 - httpcore.http11 - [DEBUG] - receive_response_headers.complete return_value=(b'HTTP/1.1', 200, b'OK', [(b'Content-Type', b'text/html; charset=utf-8'), (b'Last-Modified', b'Wed, 17 Sep 2025 19:16:12 GMT'), (b'Strict-Transport-Security', b'max-age=63072000; includeSubDomains; preload'), (b'X-Frame-Options', b'SAMEORIGIN'), (b'Content-Security-Policy', b"frame-ancestors 'self' *.ign.com *.ampproject.org *.zdbb.net *.disqus.com widgets.ign.com;"), (b'X-XSS-Protection', b'1; mode=block'), (b'Content-Encoding', b'gzip'), (b'Content-Length', b'0'), (b'Cache-Control', b'public, max-age=86400'), (b'Expires', b'Thu, 18 Sep 2025 19:16:14 GMT'), (b'Date', b'Wed, 17 Sep 2025 19:16:14 GMT'), (b'Alt-Svc', b'h3=":443"; ma=93600'), (b'Connection', b'keep-alive'), (b'Vary', b'Accept-Encoding'), (b'Set-Cookie', b'geoCC=DE; expires=Wed, 17-Sep-2025 23:16:14 GMT; path=/; domain=.ign.com')])
[start-backend] 2025-09-17 21:16:11 - httpx - [INFO] - HTTP Request: HEAD https://de.ign.com/nintendo/146166/page/nintendo-switch-2-release-preis-spiele-hardware "HTTP/1.1 200 OK"
[start-backend] 2025-09-17 21:16:11 - httpcore.http11 - [DEBUG] - receive_response_body.started request=<Request [b'HEAD']>
[start-backend] 2025-09-17 21:16:11 - httpcore.http11 - [DEBUG] - receive_response_body.complete
[start-backend] 2025-09-17 21:16:11 - httpcore.http11 - [DEBUG] - response_closed.started
[start-backend] 2025-09-17 21:16:11 - httpcore.http11 - [DEBUG] - response_closed.complete
[start-backend] 2025-09-17 21:16:12 - httpcore.http11 - [DEBUG] - receive_response_headers.complete return_value=(b'HTTP/1.1', 200, b'OK', [(b'Date', b'Wed, 17 Sep 2025 19:16:14 GMT'), (b'Content-Type', b'text/html; charset=utf-8'), (b'Connection', b'keep-alive'), (b'Content-Encoding', b'gzip'), (b'CF-Ray', b'980aefd239e9c7bb-DUS'), (b'CF-Cache-Status', b'EXPIRED'), (b'Cache-Control', b'public, max-age=120, stale-while-revalidate=600'), (b'Link', b'<https://www.mediamarkt.de/assets/fonts/noto-sans-display-v10-latin-400.woff2>; rel="preload"; as="font"; crossorigin; type="font/woff2"; nopush, <https://www.mediamarkt.de/assets/fonts/noto-sans-display-v10-latin-600.woff2>; rel="preload"; as="font"; crossorigin; type="font/woff2"; nopush, <https://www.mediamarkt.de/assets/fonts/noto-sans-display-v10-latin-700.woff2>; rel="preload"; as="font"; crossorigin; type="font/woff2"; nopush, <https://www.mediamarkt.de/assets/fonts/MMHeadlineProWebTT-Regular_subset.woff2>; rel="preload"; as="font"; crossorigin; type="font/woff2"; nopush, <https://www.mediamarkt.de/assets/fonts/MediaMarktPreise.woff2>; rel="preload"; as="font"; crossorigin; type="font/woff2"; nopush'), (b'Set-Cookie', b'optid=4c2b9bdd-3ce5-404f-9a73-ae9e4f2c63a3; Domain=.mediamarkt.de; Path=/'), (b'Set-Cookie', b'__cf_bm=uth34gXFnMVllQyP1FeQWXKO8DPqod8W8nEn9cu.LTg-1758136574-1.0.1.1-UOKU9d1mHKfgSjtoAcDeoHgwCCQFs4AS9xriPwh26hb4FmKZ6YTYliY7Gt24pvWOh7SgwSp1_lmGFqc58QLwxZgm3xs_i6YJzlxsrstbli2sqIBOiL.4BcqSGjk73Yow; path=/; expires=Wed, 17-Sep-25 19:46:14 GMT; domain=.mediamarkt.de; HttpOnly; Secure; SameSite=None'), (b'Set-Cookie', b'_cfuvid=LOuO5RiLfYgzlKOZAuUVLj1vcvWAdKOdOGHlVYtLfpk-1758136574852-0.0.1.1-604800000; path=/; domain=.mediamarkt.de; HttpOnly; Secure; SameSite=None'), (b'Vary', b'Accept-Encoding'), (b'Via', b'1.1 google, 1.1 google'), (b'server-timing', b'total;dur=967'), (b'x-frame-options', b'SAMEORIGIN'), (b'x-mms-cf-d', b''), (b'x-mms-variation', b'exp-999_-_pdp_-_pre-checkout_modal:precheckout_modal_with_scrollable_reco&exp-1083_-_pdp_-_onereco_-_similarity_product_recommendations:control'), (b'Strict-Transport-Security', b'max-age=31536000'), (b'x-we-are-hiring', b'We appreciate developers that love to explore what goes on under the hood of software. Apply now at https://careers.mediamarktsaturn.com/MediaMarktSaturn!'), (b'Server', b'cloudflare')])
[start-backend] 2025-09-17 21:16:12 - httpx - [INFO] - HTTP Request: HEAD https://www.mediamarkt.de/de/product/_nintendo-switch-2-2989498.html "HTTP/1.1 200 OK"
[start-backend] 2025-09-17 21:16:12 - httpcore.http11 - [DEBUG] - receive_response_body.started request=<Request [b'HEAD']>
[start-backend] 2025-09-17 21:16:12 - httpcore.http11 - [DEBUG] - receive_response_body.complete
[start-backend] 2025-09-17 21:16:12 - httpcore.http11 - [DEBUG] - response_closed.started
[start-backend] 2025-09-17 21:16:12 - httpcore.http11 - [DEBUG] - response_closed.complete
[start-backend] 2025-09-17 21:16:21 - httpcore.http11 - [DEBUG] - receive_response_headers.failed exception=ReadTimeout(TimeoutError())
[start-backend] 2025-09-17 21:16:21 - httpcore.http11 - [DEBUG] - response_closed.started
[start-backend] 2025-09-17 21:16:21 - httpcore.http11 - [DEBUG] - response_closed.complete
[start-backend] 2025-09-17 21:16:21 - httpcore.connection - [DEBUG] - close.started
[start-backend] 2025-09-17 21:16:21 - httpcore.connection - [DEBUG] - close.complete
[start-backend] 2025-09-17 21:16:21 - httpcore.connection - [DEBUG] - close.started
[start-backend] 2025-09-17 21:16:21 - httpcore.connection - [DEBUG] - close.complete
[start-backend] 2025-09-17 21:16:21 - httpcore.connection - [DEBUG] - close.started
[start-backend] 2025-09-17 21:16:21 - httpcore.connection - [DEBUG] - close.complete
[start-backend] 2025-09-17 21:16:21 - httpcore.connection - [DEBUG] - close.started
[start-backend] 2025-09-17 21:16:21 - httpcore.connection - [DEBUG] - close.complete
[start-backend] 2025-09-17 21:16:21 - httpcore.connection - [DEBUG] - close.started
[start-backend] 2025-09-17 21:16:21 - httpcore.connection - [DEBUG] - close.complete
[start-backend] 2025-09-17 21:16:21 - httpcore.connection - [DEBUG] - close.started
[start-backend] 2025-09-17 21:16:21 - httpcore.connection - [DEBUG] - close.complete
[start-backend] 2025-09-17 21:16:21 - httpcore.connection - [DEBUG] - close.started
[start-backend] 2025-09-17 21:16:21 - httpcore.connection - [DEBUG] - close.complete
[start-backend] 2025-09-17 21:16:21 - httpcore.connection - [DEBUG] - close.started
[start-backend] 2025-09-17 21:16:21 - httpcore.connection - [DEBUG] - close.complete
[start-backend] 2025-09-17 21:16:21 - httpcore.connection - [DEBUG] - close.started
[start-backend] 2025-09-17 21:16:21 - httpcore.connection - [DEBUG] - close.complete
[start-backend] 2025-09-17 21:16:21 - httpcore.connection - [DEBUG] - close.started
[start-backend] 2025-09-17 21:16:21 - httpcore.connection - [DEBUG] - close.complete
[start-backend] 2025-09-17 21:16:21 - httpcore.connection - [DEBUG] - close.started
[start-backend] 2025-09-17 21:16:21 - httpcore.connection - [DEBUG] - close.complete
[start-backend] 2025-09-17 21:16:21 - httpcore.connection - [DEBUG] - close.started
[start-backend] 2025-09-17 21:16:21 - httpcore.connection - [DEBUG] - close.complete
[start-backend] 2025-09-17 21:16:21 - httpcore.connection - [DEBUG] - close.started
[start-backend] 2025-09-17 21:16:21 - httpcore.connection - [DEBUG] - close.complete
[start-backend] 2025-09-17 21:16:21 - httpcore.connection - [DEBUG] - close.started
[start-backend] 2025-09-17 21:16:21 - httpcore.connection - [DEBUG] - close.complete
[start-backend] 2025-09-17 21:16:21 - httpcore.connection - [DEBUG] - close.started
[start-backend] 2025-09-17 21:16:21 - httpcore.connection - [DEBUG] - close.complete
[start-backend] 2025-09-17 21:16:21 - janus_backend - [WARNING] - Could not resolve redirect for https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQGZpTC7uIN2CpfrGURQotvMfhF1ZptCLd05W4EuEatFH0wfOASJLv6fjZYsy_NOFweG8w4jZYjgWRrjDe9QpAo_eyhSuy-R7W5dUsJ_Hoj8HbAEjkiNnK1gL2KJHkPEUbmaU8iza_uyhH7zwqCwmTpynTlP_eqYtoJBMLtDvgJhNctB-Hm8pRQoy_RAhvtVPpMc:
[start-backend] 2025-09-17 21:16:21 - janus_backend - [INFO] -
[start-backend] --- USAGE TRACKING ---
[start-backend] Model: gemini-2.5-flash
[start-backend] Input Tokens: 159
[start-backend] Output Tokens: 442
[start-backend] Total Cost: 0.00015820 �
[start-backend] ----------------------
[start-backend] 2025-09-17 21:16:21 - janus_backend - [INFO] - Final answer before check: 'Die Nintendo Switch 2, die am 5. Juni 2025 weltweit erschienen ist, kostet in der Standardvariante ohne Spiel 469,99 Euro.[1][2][3][4][5][6] Es gibt auch ein Bundle mit dem Spiel "Mario Kart World" (digital), das f�r 509,99 Euro erh�ltlich ist. Laut [1][3] Preisvergleichen ist die Konsole auch ab 461,98 Euro bei verschiedenen Anbietern zu finden, wobei Bundles mit "Mario Kart World" oder "Pok�mon-Legenden: Z-A" bei etwa 499,00 Euro bzw. 509,00 Euro liegen.
[start-backend]
[start-backend] Der [7] Pro-Controller f�r die Switch 2 kostet 89,99 Euro und bietet unter anderem einen Klinkenanschluss f�r Headsets.
[start-backend]
[start-backend] Die [1] Konsole verf�gt �ber ein 7,9 Zoll gro�es LCD-Display mit 1080p und 120 fps sowie 256 GB internen Speicher. Der Speicher [1][7][8] kann mit microSD-Express-Karten erweitert werden.[3][8]
[start-backend]
[start-backend] ---
[start-backend] **Quellen:**
[start-backend] 1. [gamepro.de](https://www.gamepro.de/artikel/nintendo-switch-2-preis-und-termin,3430550.html)
[start-backend] 2. [spiegel.de](https://www.spiegel.de/netzwelt/games/switch-2-nintendo-gibt-release-datum-und-preis-bekannt-a-2f01921b-cd3b-4676-9339-a573539fada1)
[start-backend] 3. [wikipedia.org](https://de.wikipedia.org/wiki/Nintendo_Switch_2)
[start-backend] 4. [gamestar.de](https://www.gamestar.de/artikel/nintendo-switch-2-release-specs-preis-alle-infos-geruechte,3401147.html)
[start-backend] 5. [geizhals.de](https://geizhals.de/nintendo-switch-2-v195471.html)
[start-backend] 6. [mediamarkt.de](https://www.mediamarkt.de/de/product/_nintendo-switch-2-2989498.html)
[start-backend] 7. [idealo.de](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQGZpTC7uIN2CpfrGURQotvMfhF1ZptCLd05W4EuEatFH0wfOASJLv6fjZYsy_NOFweG8w4jZYjgWRrjDe9QpAo_eyhSuy-R7W5dUsJ_Hoj8HbAEjkiNnK1gL2KJHkPEUbmaU8iza_uyhH7zwqCwmTpynTlP_eqYtoJBMLtDvgJhNctB-Hm8pRQoy_RAhvtVPpMc)
[start-backend] 8. [ign.com](https://de.ign.com/nintendo/146166/page/nintendo-switch-2-release-preis-spiele-hardware)
[start-backend] '
[start-backend] 2025-09-17 21:16:21 - janus_backend - [INFO] - [FACT EXTRACTION] Starte Extraktion f�r Chat 1 mit Text: 'User: weiviel kostet aktuell die switch 2?
[start-backend] Assistant: Die Nintendo Switch 2, die am 5. Juni 2025 weltweit erschienen ist, kostet in der Standardvariante ohne Spiel 469,99 Euro.[1][2][3][4][5][6] Es gibt auch ein Bundle mit dem Spiel "Mario Kart World" (digital), das f�r 509,99 Euro erh�ltlich ist. Laut [1][3] Preisvergleichen ist die Konsole auch ab 461,98 Euro bei verschiedenen Anbietern zu finden, wobei Bundles mit "Mario Kart World" oder "Pok�mon-Legenden: Z-A" bei etwa 499,00 Euro bzw. 509,00 Euro liegen.
[start-backend]
[start-backend] Der [7] Pro-Controller f�r die Switch 2 kostet 89,99 Euro und bietet unter anderem einen Klinkenanschluss f�r Headsets.
[start-backend]
[start-backend] Die [1] Konsole verf�gt �ber ein 7,9 Zoll gro�es LCD-Display mit 1080p und 120 fps sowie 256 GB internen Speicher. Der Speicher [1][7][8] kann mit microSD-Express-Karten erweitert werden.[3][8]
[start-backend]
[start-backend] ---
[start-backend] **Quellen:**
[start-backend] 1. [gamepro.de](https://www.gamepro.de/artikel/nintendo-switch-2-preis-und-termin,3430550.html)
[start-backend] 2. [spiegel.de](https://www.spiegel.de/netzwelt/games/switch-2-nintendo-gibt-release-datum-und-preis-bekannt-a-2f01921b-cd3b-4676-9339-a573539fada1)
[start-backend] 3. [wikipedia.org](https://de.wikipedia.org/wiki/Nintendo_Switch_2)
[start-backend] 4. [gamestar.de](https://www.gamestar.de/artikel/nintendo-switch-2-release-specs-preis-alle-infos-geruechte,3401147.html)
[start-backend] 5. [geizhals.de](https://geizhals.de/nintendo-switch-2-v195471.html)
[start-backend] 6. [mediamarkt.de](https://www.mediamarkt.de/de/product/_nintendo-switch-2-2989498.html)
[start-backend] 7. [idealo.de](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQGZpTC7uIN2CpfrGURQotvMfhF1ZptCLd05W4EuEatFH0wfOASJLv6fjZYsy_NOFweG8w4jZYjgWRrjDe9QpAo_eyhSuy-R7W5dUsJ_Hoj8HbAEjkiNnK1gL2KJHkPEUbmaU8iza_uyhH7zwqCwmTpynTlP_eqYtoJBMLtDvgJhNctB-Hm8pRQoy_RAhvtVPpMc)
[start-backend] 8. [ign.com](https://de.ign.com/nintendo/146166/page/nintendo-switch-2-release-preis-spiele-hardware)
[start-backend] '
[start-backend] 2025-09-17 21:16:21 - grpc._cython.cygrpc - [DEBUG] - Using AsyncIOEngine.POLLER as I/O engine
[start-backend] INFO:     127.0.0.1:65209 - "POST /api/chat HTTP/1.1" 200 OK
[start-backend] INFO:     127.0.0.1:65209 - "GET /api/costs/dashboard HTTP/1.1" 200 OK
[start-backend] 2025-09-17 21:16:23 - janus_backend - [INFO] -
[start-backend] --- USAGE TRACKING ---
[start-backend] Model: gemini-2.5-flash
[start-backend] Input Tokens: 0
[start-backend] Output Tokens: 0
[start-backend] Image Quality: N/A
[start-backend] Image Size: N/A
[start-backend] Total Cost: 0.00000000 �
[start-backend] ----------------------
[start-backend] 2025-09-17 21:16:23 - janus_backend - [INFO] - Extracted text: 'Keine'
[start-backend] 2025-09-17 21:16:23 - janus_backend - [INFO] - Kein relevanter Fakt im Textblock gefunden.
[start-backend] 2025-09-17 21:17:06 - janus_backend - [INFO] - No new image uploaded. Checking history for existing image context.
[start-backend] 2025-09-17 21:17:06 - janus_backend - [INFO] - Task-oriented prompt detected (file ops/web search). Suppressing visual context to ensure tool usage.
[start-backend] 2025-09-17 21:17:06 - janus_backend - [INFO] - Explizite Werkzeug-Direktive wurde auf den System-Prompt angewendet.
[start-backend] 2025-09-17 21:17:06 - janus_backend - [INFO] - Using persona prompt for 'ai_assistant'
[start-backend] 2025-09-17 21:17:06 - janus_backend - [INFO] - [DEBUG] FINAL HYBRID Memory Context Generated (length: 0):
[start-backend] 2025-09-17 21:17:06 - janus_backend - [INFO] - Touched 0 memory snippets to update their relevance.
[start-backend] 2025-09-17 21:17:06 - grpc._cython.cygrpc - [DEBUG] - Using AsyncIOEngine.POLLER as I/O engine
[start-backend] 2025-09-17 21:17:14 - janus_backend - [INFO] - Gemini requested tool call: create_file_tool with args: {'content': 'Die Nintendo Switch 2, die am 5. Juni 2025 weltweit erschienen ist, kostet in der Standardvariante ohne Spiel 469,99 Euro.[1][2][3][4][5][6] Es gibt auch ein Bundle mit dem Spiel "Mario Kart World" (digital), das f�r 509,99 Euro erh�ltlich ist. Laut [1][3] Preisvergleichen ist die Konsole auch ab 461,98 Euro bei verschiedenen Anbietern zu finden, wobei Bundles mit "Mario Kart World" oder "Pok�mon-Legenden: Z-A" bei etwa 499,00 Euro bzw. 509,00 Euro liegen.\n\nDer [7] Pro-Controller f�r die Switch 2 kostet 89,99 Euro und bietet unter anderem einen Klinkenanschluss f�r Headsets.\n\nDie [1] Konsole verf�gt �ber ein 7,9 Zoll gro�es LCD-Display mit 1080p und 120 fps sowie 256 GB internen Speicher. Der Speicher [1][7][8] kann mit microSD-Express-Karten erweitert werden.[3][8]\n\n---\n**Quellen:**\n1. [gamepro.de](https://www.gamepro.de/artikel/nintendo-switch-2-preis-und-termin,3430550.html)\n2. [spiegel.de](https://www.spiegel.de/netzwelt/games/switch-2-nintendo-gibt-release-datum-und-preis-bekannt-a-2f01921b-cd3b-4676-9339-a573539fada1)\n3. [wikipedia.org](https://de.wikipedia.org/wiki/Nintendo_Switch_2)\n4. [gamestar.de](https://www.gamestar.de/artikel/nintendo-switch-2-release-specs-preis-alle-infos-geruechte,3401147.html)\n5. [geizhals.de](https://geizhals.de/nintendo-switch-2-v195471.html)\n6. [mediamarkt.de](https://www.mediamarkt.de/de/product/_nintendo-switch-2-2989498.html)\n7. [idealo.de](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQGZpTC7uIN2CpfrGURQotvMfhF1ZptCLd05W4EuEatFH0wfOASJLv6fjZYsy_NOFweG8w4jZYjgWRrjDe9QpAo_eyhSuy-R7W5dUsJ_Hoj8HbAEjkiNnK1gL2KJHkPEUbmaU8iza_uyhH7zwqCwmTpynTlP_eqYtoJBMLtDvgJhNctB-Hm8pRQoy_RAhvtVPpMc)\n8. [ign.com](https://de.ign.com/nintendo/146166/page/nintendo-switch-2-release-preis-spiele-hardware)', 'path': 'C:\\Users\\pruve\\Desktop\\rolfistgut.txt'}
[start-backend] 2025-09-17 21:17:14 - janus_backend - [INFO] -
[start-backend] --- USAGE TRACKING ---
[start-backend] Model: gemini-2.5-flash
[start-backend] Input Tokens: 0
[start-backend] Output Tokens: 0
[start-backend] Image Quality: N/A
[start-backend] Image Size: N/A
[start-backend] Total Cost: 0.00000000 �
[start-backend] ----------------------
[start-backend] 2025-09-17 21:17:14 - janus_backend - [WARNING] - Unknown tool call: create_file_tool for provider: gemini
[start-backend] 2025-09-17 21:17:14 - janus_backend - [INFO] - Executing tool 'create_file_tool' with args: {'content': 'Die Nintendo Switch 2, die am 5. Juni 2025 weltweit erschienen ist, kostet in der Standardvariante ohne Spiel 469,99 Euro.[1][2][3][4][5][6] Es gibt auch ein Bundle mit dem Spiel "Mario Kart World" (digital), das f�r 509,99 Euro erh�ltlich ist. Laut [1][3] Preisvergleichen ist die Konsole auch ab 461,98 Euro bei verschiedenen Anbietern zu finden, wobei Bundles mit "Mario Kart World" oder "Pok�mon-Legenden: Z-A" bei etwa 499,00 Euro bzw. 509,00 Euro liegen.\n\nDer [7] Pro-Controller f�r die Switch 2 kostet 89,99 Euro und bietet unter anderem einen Klinkenanschluss f�r Headsets.\n\nDie [1] Konsole verf�gt �ber ein 7,9 Zoll gro�es LCD-Display mit 1080p und 120 fps sowie 256 GB internen Speicher. Der Speicher [1][7][8] kann mit microSD-Express-Karten erweitert werden.[3][8]\n\n---\n**Quellen:**\n1. [gamepro.de](https://www.gamepro.de/artikel/nintendo-switch-2-preis-und-termin,3430550.html)\n2. [spiegel.de](https://www.spiegel.de/netzwelt/games/switch-2-nintendo-gibt-release-datum-und-preis-bekannt-a-2f01921b-cd3b-4676-9339-a573539fada1)\n3. [wikipedia.org](https://de.wikipedia.org/wiki/Nintendo_Switch_2)\n4. [gamestar.de](https://www.gamestar.de/artikel/nintendo-switch-2-release-specs-preis-alle-infos-geruechte,3401147.html)\n5. [geizhals.de](https://geizhals.de/nintendo-switch-2-v195471.html)\n6. [mediamarkt.de](https://www.mediamarkt.de/de/product/_nintendo-switch-2-2989498.html)\n7. [idealo.de](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQGZpTC7uIN2CpfrGURQotvMfhF1ZptCLd05W4EuEatFH0wfOASJLv6fjZYsy_NOFweG8w4jZYjgWRrjDe9QpAo_eyhSuy-R7W5dUsJ_Hoj8HbAEjkiNnK1gL2KJHkPEUbmaU8iza_uyhH7zwqCwmTpynTlP_eqYtoJBMLtDvgJhNctB-Hm8pRQoy_RAhvtVPpMc)\n8. [ign.com](https://de.ign.com/nintendo/146166/page/nintendo-switch-2-release-preis-spiele-hardware)', 'path': 'C:\\Users\\pruve\\Desktop\\rolfistgut.txt'}
[start-backend] 2025-09-17 21:17:14 - janus_backend - [INFO] - Datei erstellt: C:\Users\pruve\Desktop\rolfistgut.txt
[start-backend] 2025-09-17 21:17:14 - janus_backend - [INFO] - Final answer before check: 'Ergebnis von Tool 'create_file_tool': {
[start-backend]   "output": "Datei 'C:\\Users\\pruve\\Desktop\\rolfistgut.txt' wurde erfolgreich erstellt."
[start-backend] }'
[start-backend] INFO:     127.0.0.1:49192 - "POST /api/chat HTTP/1.1" 200 OK
[start-backend] INFO:     127.0.0.1:49192 - "GET /api/costs/dashboard HTTP/1.1" 200 OK
[start-backend] 2025-09-17 21:17:26 - janus_backend - [INFO] - Image saved from bytes to C:\Users\pruve\AppData\Local\JanusDev\Janus Projekt\images\user-upload-23-17-09-25.png
[start-backend] 2025-09-17 21:17:26 - janus_backend - [INFO] - User-uploaded image saved to: /user_images/user-upload-23-17-09-25.png
[start-backend] 2025-09-17 21:17:26 - janus_backend - [INFO] - Explizite Werkzeug-Direktive wurde auf den System-Prompt angewendet.
[start-backend] 2025-09-17 21:17:26 - janus_backend - [INFO] - Using persona prompt for 'ai_assistant'
[start-backend] 2025-09-17 21:17:26 - janus_backend - [INFO] - [DEBUG] FINAL HYBRID Memory Context Generated (length: 0):
[start-backend] 2025-09-17 21:17:26 - janus_backend - [INFO] - Touched 0 memory snippets to update their relevance.
[start-backend] 2025-09-17 21:17:26 - janus_backend - [INFO] - Image data detected for Gemini. Processing as a multi-modal request.
[start-backend] 2025-09-17 21:17:35 - janus_backend - [INFO] -
[start-backend] --- USAGE TRACKING ---
[start-backend] Model: gemini-2.5-flash
[start-backend] Input Tokens: 1169
[start-backend] Output Tokens: 39
[start-backend] Total Cost: 0.00036045 �
[start-backend] ----------------------
[start-backend] 2025-09-17 21:17:35 - janus_backend - [INFO] - Final answer before check: 'Ja, das Bild wurde erfolgreich verarbeitet. Es zeigt eine Frau mit langen, r�tlich-braunen Locken und blauen Augen, die freundlich in die Kamera l�chelt.'
[start-backend] 2025-09-17 21:17:35 - janus_backend - [INFO] - [FACT EXTRACTION] Starte Extraktion f�r Chat 1 mit Text: 'User: Gib eine kurze Best�tigung und die wichtigsten Merkmale des Bildes in einem Satz.
[start-backend] Assistant: Ja, das Bild wurde erfolgreich verarbeitet. Es zeigt eine Frau mit langen, r�tlich-braunen Locken und blauen Augen, die freundlich in die Kamera l�chelt.'
[start-backend] INFO:     127.0.0.1:49292 - "POST /api/chat HTTP/1.1" 200 OK
[start-backend] INFO:     127.0.0.1:49292 - "GET /api/costs/dashboard HTTP/1.1" 200 OK
[start-backend] 2025-09-17 21:17:37 - janus_backend - [INFO] -
[start-backend] --- USAGE TRACKING ---
[start-backend] Model: gemini-2.5-flash
[start-backend] Input Tokens: 0
[start-backend] Output Tokens: 0
[start-backend] Image Quality: N/A
[start-backend] Image Size: N/A
[start-backend] Total Cost: 0.00000000 �
[start-backend] ----------------------
[start-backend] 2025-09-17 21:17:37 - janus_backend - [INFO] - Extracted text: 'Keine.'
[start-backend] 2025-09-17 21:17:37 - janus_backend - [INFO] - Kein relevanter Fakt im Textblock gefunden.
[start-backend] 2025-09-17 21:17:51 - janus_backend - [INFO] - No new image uploaded. Checking history for existing image context.
[start-backend] 2025-09-17 21:17:51 - janus_backend - [INFO] - Image context is relevant. Reloading previous image: C:\Users\pruve\AppData\Local\JanusDev\Janus Projekt\images\user-upload-23-17-09-25.png
[start-backend] 2025-09-17 21:17:51 - janus_backend - [INFO] - Explizite Werkzeug-Direktive wurde auf den System-Prompt angewendet.
[start-backend] 2025-09-17 21:17:51 - janus_backend - [INFO] - Using persona prompt for 'ai_assistant'
[start-backend] 2025-09-17 21:17:51 - janus_backend - [INFO] - [DEBUG] FINAL HYBRID Memory Context Generated (length: 0):
[start-backend] 2025-09-17 21:17:51 - janus_backend - [INFO] - Touched 0 memory snippets to update their relevance.
[start-backend] 2025-09-17 21:17:51 - janus_backend - [INFO] - Image data detected for Gemini. Processing as a multi-modal request.
[start-backend] 2025-09-17 21:18:23 - janus_backend - [INFO] -
[start-backend] --- USAGE TRACKING ---
[start-backend] Model: gemini-2.5-flash
[start-backend] Input Tokens: 1157
[start-backend] Output Tokens: 361
[start-backend] Total Cost: 0.00043735 �
[start-backend] ----------------------
[start-backend] 2025-09-17 21:18:23 - janus_backend - [INFO] - Final answer before check: 'Das Bild zeigt eine Frau mittleren Alters in einer Nahaufnahme, die von der Brust aufw�rts zu sehen ist. Sie hat langes, sehr volles und stark gelocktes bis welliges, r�tlich-braunes Haar, das beidseitig vom Gesicht zur�ckf�llt und �ber die Schultern reicht.
[start-backend]
[start-backend] Ihr Gesicht ist freundlich und leicht gerundet, mit einem sanften, geschlossenen L�cheln, das ihre Wangen leicht hebt und kleine Lachf�ltchen um die Augenwinkel erzeugt. Sie hat hellblaue oder graublaue Augen, die einen leicht gl�nzenden Lidschatten tragen. Ihre Lippen sind voll und nat�rlich rosa. Die Augenbrauen sind nat�rlich geformt und von mittlerer Dichte.
[start-backend]
[start-backend] Am linken Ohr (vom Betrachter aus gesehen) tr�gt sie einen silbernen H�ngeohrring mit mehreren kleinen, gl�nzenden Elementen. Um ihren Hals ist eine feine silberne Kette mit einem kleinen, dezenten Anh�nger zu erkennen.
[start-backend]
[start-backend] Sie tr�gt ein dunkles Oberteil, das an der rechten Schulter (von ihr aus gesehen) ein subtiles, m�glicherweise kariertes oder gewebtes Muster in dunklen T�nen aufweist.
[start-backend]
[start-backend] Der Hintergrund ist unscharf und verschwommen, deutet aber auf eine Umgebung mit gro�en Fenstern hin. Auf der linken Seite sind helle Vorh�nge oder Fensterrahmen erkennbar, dahinter scheinen warme Farben (orange, gelb) durch. Auf der rechten Seite sind im verschwommenen Hintergrund gr�ne Vegetation und helle, unklare Strukturen zu sehen, die an Geb�ude oder Zeltd�cher erinnern. Die Beleuchtung scheint nat�rlich und von vorne oder leicht seitlich zu kommen und beleuchtet ihr Gesicht gut.'
[start-backend] 2025-09-17 21:18:23 - janus_backend - [INFO] - [FACT EXTRACTION] Starte Extraktion f�r Chat 1 mit Text: 'User: beschreib das bild ganz genau
[start-backend] Assistant: Das Bild zeigt eine Frau mittleren Alters in einer Nahaufnahme, die von der Brust aufw�rts zu sehen ist. Sie hat langes, sehr volles und stark gelocktes bis welliges, r�tlich-braunes Haar, das beidseitig vom Gesicht zur�ckf�llt und �ber die Schultern reicht.
[start-backend]
[start-backend] Ihr Gesicht ist freundlich und leicht gerundet, mit einem sanften, geschlossenen L�cheln, das ihre Wangen leicht hebt und kleine Lachf�ltchen um die Augenwinkel erzeugt. Sie hat hellblaue oder graublaue Augen, die einen leicht gl�nzenden Lidschatten tragen. Ihre Lippen sind voll und nat�rlich rosa. Die Augenbrauen sind nat�rlich geformt und von mittlerer Dichte.
[start-backend]
[start-backend] Am linken Ohr (vom Betrachter aus gesehen) tr�gt sie einen silbernen H�ngeohrring mit mehreren kleinen, gl�nzenden Elementen. Um ihren Hals ist eine feine silberne Kette mit einem kleinen, dezenten Anh�nger zu erkennen.
[start-backend]
[start-backend] Sie tr�gt ein dunkles Oberteil, das an der rechten Schulter (von ihr aus gesehen) ein subtiles, m�glicherweise kariertes oder gewebtes Muster in dunklen T�nen aufweist.
[start-backend]
[start-backend] Der Hintergrund ist unscharf und verschwommen, deutet aber auf eine Umgebung mit gro�en Fenstern hin. Auf der linken Seite sind helle Vorh�nge oder Fensterrahmen erkennbar, dahinter scheinen warme Farben (orange, gelb) durch. Auf der rechten Seite sind im verschwommenen Hintergrund gr�ne Vegetation und helle, unklare Strukturen zu sehen, die an Geb�ude oder Zeltd�cher erinnern. Die Beleuchtung scheint nat�rlich und von vorne oder leicht seitlich zu kommen und beleuchtet ihr Gesicht gut.'
[start-backend] INFO:     127.0.0.1:49400 - "POST /api/chat HTTP/1.1" 200 OK
[start-backend] INFO:     127.0.0.1:49400 - "GET /api/costs/dashboard HTTP/1.1" 200 OK
[start-backend] 2025-09-17 21:18:25 - janus_backend - [INFO] -
[start-backend] --- USAGE TRACKING ---
[start-backend] Model: gemini-2.5-flash
[start-backend] Input Tokens: 0
[start-backend] Output Tokens: 0
[start-backend] Image Quality: N/A
[start-backend] Image Size: N/A
[start-backend] Total Cost: 0.00000000 �
[start-backend] ----------------------
[start-backend] 2025-09-17 21:18:25 - janus_backend - [INFO] - Extracted text: 'Keine.'
[start-backend] 2025-09-17 21:18:25 - janus_backend - [INFO] - Kein relevanter Fakt im Textblock gefunden.
[start-backend] 2025-09-17 21:18:57 - janus_backend - [INFO] - No new image uploaded. Checking history for existing image context.
[start-backend] 2025-09-17 21:18:57 - janus_backend - [INFO] - Task-oriented prompt detected (file ops/web search). Suppressing visual context to ensure tool usage.
[start-backend] 2025-09-17 21:18:57 - janus_backend - [INFO] - Explizite Werkzeug-Direktive wurde auf den System-Prompt angewendet.
[start-backend] 2025-09-17 21:18:57 - janus_backend - [INFO] - Using persona prompt for 'ai_assistant'
[start-backend] 2025-09-17 21:18:57 - janus_backend - [INFO] - [DEBUG] FINAL HYBRID Memory Context Generated (length: 0):
[start-backend] 2025-09-17 21:18:57 - janus_backend - [INFO] - Touched 0 memory snippets to update their relevance.
[start-backend] 2025-09-17 21:18:59 - janus_backend - [INFO] - Gemini requested tool call: create_file_tool with args: {'content': 'Das Bild zeigt eine freundlich l�chelnde Frau mittleren Alters mit langen, r�tlich-braunen Locken und blauen Augen, die einen silbernen H�ngeohrring und eine dezente Halskette tr�gt, vor einem unscharfen Hintergrund mit Fenstern und gr�ner Vegetation.', 'path': 'C:\\Users\\pruve\\Desktop\\maggys.txt'}
[start-backend] 2025-09-17 21:18:59 - janus_backend - [INFO] -
[start-backend] --- USAGE TRACKING ---
[start-backend] Model: gemini-2.5-flash
[start-backend] Input Tokens: 0
[start-backend] Output Tokens: 0
[start-backend] Image Quality: N/A
[start-backend] Image Size: N/A
[start-backend] Total Cost: 0.00000000 �
[start-backend] ----------------------
[start-backend] 2025-09-17 21:18:59 - janus_backend - [WARNING] - Unknown tool call: create_file_tool for provider: gemini
[start-backend] 2025-09-17 21:18:59 - janus_backend - [INFO] - Executing tool 'create_file_tool' with args: {'content': 'Das Bild zeigt eine freundlich l�chelnde Frau mittleren Alters mit langen, r�tlich-braunen Locken und blauen Augen, die einen silbernen H�ngeohrring und eine dezente Halskette tr�gt, vor einem unscharfen Hintergrund mit Fenstern und gr�ner Vegetation.', 'path': 'C:\\Users\\pruve\\Desktop\\maggys.txt'}
[start-backend] 2025-09-17 21:18:59 - janus_backend - [INFO] - Datei erstellt: C:\Users\pruve\Desktop\maggys.txt
[start-backend] 2025-09-17 21:18:59 - janus_backend - [INFO] - Final answer before check: 'Ergebnis von Tool 'create_file_tool': {
[start-backend]   "output": "Datei 'C:\\Users\\pruve\\Desktop\\maggys.txt' wurde erfolgreich erstellt."
[start-backend] }'
[start-backend] INFO:     127.0.0.1:49800 - "POST /api/chat HTTP/1.1" 200 OK
[start-backend] INFO:     127.0.0.1:49800 - "GET /api/costs/dashboard HTTP/1.1" 200 OK
[start-backend] 2025-09-17 21:19:10 - janus_backend - [INFO] - Beginne Zusammenfassung f�r Chat ID: 1
[start-backend] INFO:     127.0.0.1:49861 - "POST /api/chats HTTP/1.1" 200 OK
[start-backend] INFO:     127.0.0.1:49861 - "GET /api/chats?include_archived=false HTTP/1.1" 200 OK
[start-backend] INFO:     127.0.0.1:49861 - "GET /api/chats/2 HTTP/1.1" 200 OK
[start-backend] INFO:     127.0.0.1:49861 - "GET /api/chats/2/messages HTTP/1.1" 200 OK
[start-backend] 2025-09-17 21:19:11 - janus_backend - [WARNING] - Gemini returned no candidates, possibly due to safety filters or an empty prompt. History: [{'role': 'user', 'parts': [{'text': 'hi'}]}, {'role': 'model', 'parts': [{'text': 'Hallo! Ich bin dein pers�nlicher KI-Assistent. Ich unterst�tze dich bei Aufgaben im Alltag � von Planung �ber Recherche bis Umsetzung. Womit starten wir?'}]}, {'role': 'user', 'parts': [{'text': 'weiviel kostet aktuell die switch 2?'}]}, {'role': 'model', 'parts': [{'text': 'Die Nintendo Switch 2, die am 5. Juni 2025 weltweit erschienen ist, kostet in der Standardvariante ohne Spiel 469,99 Euro.[1][2][3][4][5][6] Es gibt auch ein Bundle mit dem Spiel "Mario Kart World" (digital), das f�r 509,99 Euro erh�ltlich ist. Laut [1][3] Preisvergleichen ist die Konsole auch ab 461,98 Euro bei verschiedenen Anbietern zu finden, wobei Bundles mit "Mario Kart World" oder "Pok�mon-Legenden: Z-A" bei etwa 499,00 Euro bzw. 509,00 Euro liegen.\n\nDer [7] Pro-Controller f�r die Switch 2 kostet 89,99 Euro und bietet unter anderem einen Klinkenanschluss f�r Headsets.\n\nDie [1] Konsole verf�gt �ber ein 7,9 Zoll gro�es LCD-Display mit 1080p und 120 fps sowie 256 GB internen Speicher. Der Speicher [1][7][8] kann mit microSD-Express-Karten erweitert werden.[3][8]\n\n---\n**Quellen:**\n1. [gamepro.de](https://www.gamepro.de/artikel/nintendo-switch-2-preis-und-termin,3430550.html)\n2. [spiegel.de](https://www.spiegel.de/netzwelt/games/switch-2-nintendo-gibt-release-datum-und-preis-bekannt-a-2f01921b-cd3b-4676-9339-a573539fada1)\n3. [wikipedia.org](https://de.wikipedia.org/wiki/Nintendo_Switch_2)\n4. [gamestar.de](https://www.gamestar.de/artikel/nintendo-switch-2-release-specs-preis-alle-infos-geruechte,3401147.html)\n5. [geizhals.de](https://geizhals.de/nintendo-switch-2-v195471.html)\n6. [mediamarkt.de](https://www.mediamarkt.de/de/product/_nintendo-switch-2-2989498.html)\n7. [idealo.de](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQGZpTC7uIN2CpfrGURQotvMfhF1ZptCLd05W4EuEatFH0wfOASJLv6fjZYsy_NOFweG8w4jZYjgWRrjDe9QpAo_eyhSuy-R7W5dUsJ_Hoj8HbAEjkiNnK1gL2KJHkPEUbmaU8iza_uyhH7zwqCwmTpynTlP_eqYtoJBMLtDvgJhNctB-Hm8pRQoy_RAhvtVPpMc)\n8. [ign.com](https://de.ign.com/nintendo/146166/page/nintendo-switch-2-release-preis-spiele-hardware)\n'}]}, {'role': 'user', 'parts': [{'text': 'speicher mir diesen sucherbnisse als txt datei namens rolfistgut auf dem desktop'}]}, {'role': 'model', 'parts': [{'text': 'Ergebnis von Tool \'create_file_tool\': {\n  "output": "Datei \'C:\\\\Users\\\\pruve\\\\Desktop\\\\rolfistgut.txt\' wurde erfolgreich erstellt."\n}'}]}, {'role': 'user', 'parts': [{'text': 'Gib eine kurze Best�tigung und die wichtigsten Merkmale des Bildes in einem Satz.'}]}, {'role': 'model', 'parts': [{'text': 'Ja, das Bild wurde erfolgreich verarbeitet. Es zeigt eine Frau mit langen, r�tlich-braunen Locken und blauen Augen, die freundlich in die Kamera l�chelt.'}]}, {'role': 'user', 'parts': [{'text': 'beschreib das bild ganz genau'}]}, {'role': 'model', 'parts': [{'text': 'Das Bild zeigt eine Frau mittleren Alters in einer Nahaufnahme, die von der Brust aufw�rts zu sehen ist. Sie hat langes, sehr volles und stark gelocktes bis welliges, r�tlich-braunes Haar, das beidseitig vom Gesicht zur�ckf�llt und �ber die Schultern reicht.\n\nIhr Gesicht ist freundlich und leicht gerundet, mit einem sanften, geschlossenen L�cheln, das ihre Wangen leicht hebt und kleine Lachf�ltchen um die Augenwinkel erzeugt. Sie hat hellblaue oder graublaue Augen, die einen leicht gl�nzenden Lidschatten tragen. Ihre Lippen sind voll und nat�rlich rosa. Die Augenbrauen sind nat�rlich geformt und von mittlerer Dichte.\n\nAm linken Ohr (vom Betrachter aus gesehen) tr�gt sie einen silbernen H�ngeohrring mit mehreren kleinen, gl�nzenden Elementen. Um ihren Hals ist eine feine silberne Kette mit einem kleinen, dezenten Anh�nger zu erkennen.\n\nSie tr�gt ein dunkles Oberteil, das an der rechten Schulter (von ihr aus gesehen) ein subtiles, m�glicherweise kariertes oder gewebtes Muster in dunklen T�nen aufweist.\n\nDer Hintergrund ist unscharf und verschwommen, deutet aber auf eine Umgebung mit gro�en Fenstern hin. Auf der linken Seite sind helle Vorh�nge oder Fensterrahmen erkennbar, dahinter scheinen warme Farben (orange, gelb) durch. Auf der rechten Seite sind im verschwommenen Hintergrund gr�ne Vegetation und helle, unklare Strukturen zu sehen, die an Geb�ude oder Zeltd�cher erinnern. Die Beleuchtung scheint nat�rlich und von vorne oder leicht seitlich zu kommen und beleuchtet ihr Gesicht gut.'}]}, {'role': 'user', 'parts': [{'text': 'ok fass mir diese beschreibung in einer txt datei namens maggys auf dem desktop zusammen'}]}, {'role': 'model', 'parts': [{'text': 'Ergebnis von Tool \'create_file_tool\': {\n  "output": "Datei \'C:\\\\Users\\\\pruve\\\\Desktop\\\\maggys.txt\' wurde erfolgreich erstellt."\n}'}]}]
[start-backend] 2025-09-17 21:19:11 - janus_backend - [INFO] - Generating embedding for text: 'Ich konnte keine passende Antwort generieren. M�glicherweise wurde sie durch einen Sicherheitsfilter blockiert.'
Batches: 100%|##########| 1/1 [00:00<00:00, 32.92it/s]
[start-backend] 2025-09-17 21:19:11 - janus_backend - [INFO] - Embedding generated successfully for text: 'Ich konnte keine passende Antwort generieren. M�glicherweise wurde sie durch einen Sicherheitsfilter blockiert.'
[start-backend] 2025-09-17 21:19:11 - janus_backend - [INFO] - Chat 1 erfolgreich zusammengefasst: 'Ich konnte keine passende Antwort generieren. M�glicherweise wurde sie durch einen Sicherheitsfilter blockiert.'
[start-backend] INFO:     127.0.0.1:49895 - "OPTIONS /api/chats/2/title HTTP/1.1" 200 OK
[start-backend] INFO:     127.0.0.1:49895 - "PUT /api/chats/2/title HTTP/1.1" 200 OK
[start-backend] INFO:     127.0.0.1:49895 - "GET /api/chats?include_archived=false HTTP/1.1" 200 OK
[start-backend] 2025-09-17 21:19:17 - janus_backend - [INFO] - Image saved from bytes to C:\Users\pruve\AppData\Local\JanusDev\Janus Projekt\images\user-upload-24-17-09-25.png
[start-backend] 2025-09-17 21:19:17 - janus_backend - [INFO] - User-uploaded image saved to: /user_images/user-upload-24-17-09-25.png
[start-backend] 2025-09-17 21:19:17 - janus_backend - [INFO] - Explizite Werkzeug-Direktive wurde auf den System-Prompt angewendet.
[start-backend] 2025-09-17 21:19:17 - janus_backend - [INFO] - Using persona prompt for 'ai_assistant'
[start-backend] 2025-09-17 21:19:17 - janus_backend - [INFO] - [DEBUG] FINAL HYBRID Memory Context Generated (length: 0):
[start-backend] 2025-09-17 21:19:17 - janus_backend - [INFO] - Touched 0 memory snippets to update their relevance.
[start-backend] 2025-09-17 21:19:17 - janus_backend - [INFO] - Image data detected for Gemini. Processing as a multi-modal request.
[start-backend] 2025-09-17 21:19:19 - janus_backend - [INFO] -
[start-backend] --- USAGE TRACKING ---
[start-backend] Model: gemini-2.5-flash
[start-backend] Input Tokens: 1261
[start-backend] Output Tokens: 45
[start-backend] Total Cost: 0.00038955 �
[start-backend] ----------------------
[start-backend] 2025-09-17 21:19:19 - janus_backend - [INFO] - Final answer before check: 'Best�tigung: Das Bild zeigt eine freundlich l�chelnde Frau mittleren Alters mit langen, r�tlich-braunen Locken und blauen Augen, die Schmuck tr�gt, vor einem unscharfen Hintergrund.'
[start-backend] 2025-09-17 21:19:19 - janus_backend - [INFO] - [FACT EXTRACTION] Starte Extraktion f�r Chat 2 mit Text: 'User: Gib eine kurze Best�tigung und die wichtigsten Merkmale des Bildes in einem Satz.
[start-backend] Assistant: Best�tigung: Das Bild zeigt eine freundlich l�chelnde Frau mittleren Alters mit langen, r�tlich-braunen Locken und blauen Augen, die Schmuck tr�gt, vor einem unscharfen Hintergrund.'
[start-backend] INFO:     127.0.0.1:49895 - "POST /api/chat HTTP/1.1" 200 OK
[start-backend] INFO:     127.0.0.1:49895 - "GET /api/costs/dashboard HTTP/1.1" 200 OK
[start-backend] 2025-09-17 21:19:21 - janus_backend - [INFO] -
[start-backend] --- USAGE TRACKING ---
[start-backend] Model: gemini-2.5-flash
[start-backend] Input Tokens: 0
[start-backend] Output Tokens: 0
[start-backend] Image Quality: N/A
[start-backend] Image Size: N/A
[start-backend] Total Cost: 0.00000000 �
[start-backend] ----------------------
[start-backend] 2025-09-17 21:19:21 - janus_backend - [INFO] - Extracted text: 'Keine.'
[start-backend] 2025-09-17 21:19:21 - janus_backend - [INFO] - Kein relevanter Fakt im Textblock gefunden.
[start-backend] 2025-09-17 21:20:02 - janus_backend - [INFO] - No new image uploaded. Checking history for existing image context.
[start-backend] 2025-09-17 21:20:02 - janus_backend - [INFO] - Task-oriented prompt detected (file ops/web search). Suppressing visual context to ensure tool usage.
[start-backend] 2025-09-17 21:20:02 - janus_backend - [INFO] - Explizite Werkzeug-Direktive wurde auf den System-Prompt angewendet.
[start-backend] 2025-09-17 21:20:02 - janus_backend - [INFO] - Using persona prompt for 'ai_assistant'
[start-backend] 2025-09-17 21:20:02 - janus_backend - [INFO] - Image generation intent detected by keyword.
[start-backend] 2025-09-17 21:20:02 - janus_backend - [INFO] - Found reference image for image-to-image task: /user_images/user-upload-24-17-09-25.png
[start-backend] 2025-09-17 21:20:02 - janus_backend - [INFO] - Reference image provided: /user_images/user-upload-24-17-09-25.png. Preparing image-to-image generation.
[start-backend] 2025-09-17 21:20:02 - janus_backend - [INFO] - Calling Gemini image model 'gemini-2.5-flash-image-preview' with prompt: 'erstelle ein bild auf dem die frau auf dem referenzbild an einem sch�nen strand sitzt' and reference image: True
[start-backend] 2025-09-17 21:20:10 - janus_backend - [INFO] - Image saved from bytes to C:\Users\pruve\AppData\Local\JanusDev\Janus Projekt\images\ein-bild-auf-dem-die-frau-auf-dem-referenzbild-an-einem-schnen-strand-sitzt-17-09-25.png
[start-backend] 2025-09-17 21:20:10 - janus_backend - [INFO] -
[start-backend] --- USAGE TRACKING ---
[start-backend] Model: gemini-2.5-flash-image-preview
[start-backend] Input Tokens: N/A
[start-backend] Output Tokens: N/A
[start-backend] Image Quality: standard
[start-backend] Image Size: 1024x1024
[start-backend] Total Cost: 0.02000000 �
[start-backend] ----------------------
[start-backend] INFO:     127.0.0.1:50156 - "POST /api/chat HTTP/1.1" 200 OK
[start-backend] INFO:     127.0.0.1:50156 - "GET /api/costs/dashboard HTTP/1.1" 200 OK
[start-backend] INFO:     127.0.0.1:50196 - "GET /user_images/ein-bild-auf-dem-die-frau-auf-dem-referenzbild-an-einem-schnen-strand-sitzt-17-09-25.png HTTP/1.1" 200 OK
[start-backend] INFO:     127.0.0.1:50265 - "GET /user_images/ein-bild-auf-dem-die-frau-auf-dem-referenzbild-an-einem-schnen-strand-sitzt-17-09-25.png HTTP/1.1" 200 OK
[start-backend] 2025-09-17 21:21:43 - janus_backend - [INFO] - No new image uploaded. Checking history for existing image context.
[start-backend] 2025-09-17 21:21:43 - janus_backend - [INFO] - Image context is relevant. Reloading previous image: C:\Users\pruve\AppData\Local\JanusDev\Janus Projekt\images\ein-bild-auf-dem-die-frau-auf-dem-referenzbild-an-einem-schnen-strand-sitzt-17-09-25.png
[start-backend] 2025-09-17 21:21:43 - janus_backend - [INFO] - Explizite Werkzeug-Direktive wurde auf den System-Prompt angewendet.
[start-backend] 2025-09-17 21:21:43 - janus_backend - [INFO] - Using persona prompt for 'ai_assistant'
[start-backend] 2025-09-17 21:21:43 - janus_backend - [INFO] - [DEBUG] FINAL HYBRID Memory Context Generated (length: 0):
[start-backend] 2025-09-17 21:21:43 - janus_backend - [INFO] - Touched 0 memory snippets to update their relevance.
[start-backend] 2025-09-17 21:21:43 - janus_backend - [INFO] - Image data detected for Gemini. Processing as a multi-modal request.
[start-backend] 2025-09-17 21:21:48 - janus_backend - [INFO] -
[start-backend] --- USAGE TRACKING ---
[start-backend] Model: gemini-2.5-flash
[start-backend] Input Tokens: 1246
[start-backend] Output Tokens: 31
[start-backend] Total Cost: 0.00038155 �
[start-backend] ----------------------
[start-backend] 2025-09-17 21:21:48 - janus_backend - [INFO] - Final answer before check: 'Vielen Dank! Freut mich, dass ich helfen konnte.
[start-backend]
[start-backend] Gibt es noch etwas, womit ich dir behilflich sein kann?'
[start-backend] 2025-09-17 21:21:48 - janus_backend - [INFO] - [FACT EXTRACTION] Starte Extraktion f�r Chat 2 mit Text: 'User: sehr gut
[start-backend] Assistant: Vielen Dank! Freut mich, dass ich helfen konnte.
[start-backend]
[start-backend] Gibt es noch etwas, womit ich dir behilflich sein kann?'
[start-backend] INFO:     127.0.0.1:50624 - "POST /api/chat HTTP/1.1" 200 OK
[start-backend] INFO:     127.0.0.1:50624 - "GET /api/costs/dashboard HTTP/1.1" 200 OK
[start-backend] 2025-09-17 21:21:50 - janus_backend - [INFO] -
[start-backend] --- USAGE TRACKING ---
[start-backend] Model: gemini-2.5-flash
[start-backend] Input Tokens: 0
[start-backend] Output Tokens: 0
[start-backend] Image Quality: N/A
[start-backend] Image Size: N/A
[start-backend] Total Cost: 0.00000000 �
[start-backend] ----------------------
[start-backend] 2025-09-17 21:21:50 - janus_backend - [INFO] - Extracted text: 'Keine.'
[start-backend] 2025-09-17 21:21:50 - janus_backend - [INFO] - Kein relevanter Fakt im Textblock gefunden.