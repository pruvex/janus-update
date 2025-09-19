ell
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
[start-backend] INFO:     Started reloader process [35296] using WatchFiles
[start-frontend] [1]
[start-frontend] [1] > janus-projekt@1.1.0 start-vite
[start-frontend] [1] > vite
[start-frontend] [1]
[start-frontend] [0]
[start-frontend] [0] > janus-projekt@1.1.0 start-electron
[start-frontend] [0] > wait-on tcp:8001 && cross-env NODE_ENV=development electron .
[start-frontend] [0]
[start-backend] 2025-09-18 23:25:49 - janus_backend - [INFO] - Logger wurde initialisiert.
[start-backend] 2025-09-18 23:25:49 - keyring.backend - [DEBUG] - Loading KWallet
[start-backend] 2025-09-18 23:25:49 - keyring.backend - [DEBUG] - Loading SecretService
[start-backend] 2025-09-18 23:25:49 - keyring.backend - [DEBUG] - Loading Windows
[start-backend] 2025-09-18 23:25:49 - win32ctypes.core.ctypes - [DEBUG] - Loaded ctypes backend
[start-backend] 2025-09-18 23:25:49 - keyring.backend - [DEBUG] - Loading chainer
[start-backend] 2025-09-18 23:25:49 - keyring.backend - [DEBUG] - Loading libsecret
[start-backend] 2025-09-18 23:25:49 - keyring.backend - [DEBUG] - Loading macOS
[start-backend] 2025-09-18 23:25:49 - janus_backend - [INFO] - OpenAI API key loaded from keyring and set as environment variable.
[start-frontend] [1] The CJS build of Vite's Node API is deprecated. See https://vite.dev/guide/troubleshooting.html#vite-cjs-node-api-deprecated for more details.
[start-frontend] [1]
[start-frontend] [1]   VITE v5.4.19  ready in 289 ms
[start-frontend] [1]
[start-frontend] [1]   ➜  Local:   http://localhost:5173/
[start-frontend] [1]   ➜  Network: use --host to expose
[start-backend] 2025-09-18 23:25:52 - janus_backend - [INFO] - Logger wurde initialisiert.
[start-backend] 2025-09-18 23:25:52 - janus_backend - [INFO] - Logger wurde initialisiert.
[start-backend] 2025-09-18 23:26:00 - sentence_transformers.SentenceTransformer - [INFO] - Use pytorch device_name: cpu
[start-backend] 2025-09-18 23:26:00 - sentence_transformers.SentenceTransformer - [INFO] - Load pretrained SentenceTransformer: C:\KI\Janus-Projekt\backend/model_cache/all-MiniLM-L6-v2
[start-backend] 2025-09-18 23:26:00 - janus_backend - [INFO] - Application Data Directory: C:\Users\pruve\AppData\Local\JanusDev\Janus Projekt
[start-backend] INFO:     Started server process [36496]
[start-backend] INFO:     Waiting for application startup.
[start-backend] 2025-09-18 23:26:01 - janus_backend - [INFO] - Scheduling initial memory maintenance tasks on startup.
[start-backend] 2025-09-18 23:26:01 - janus_backend - [INFO] - Background memory archival task starting.
[start-backend] 2025-09-18 23:26:01 - janus_backend - [INFO] - STM size (0) is within limit (250). No archival needed.
[start-backend] 2025-09-18 23:26:01 - janus_backend - [INFO] - Background memory archival task finished successfully.
[start-backend] 2025-09-18 23:26:01 - janus_backend - [INFO] - Background memory pruning task starting.
[start-backend] 2025-09-18 23:26:01 - janus_backend - [INFO] - No expired memories to prune.
[start-backend] INFO:     Application startup complete.
[start-backend] 2025-09-18 23:26:01 - janus_backend - [INFO] - Background memory pruning task finished successfully.
[start-frontend] [0]
[start-frontend] [0] Main process: Script started (Root main.electron.js)
[start-frontend] [0] Main process: ipcMain.handle registered for save-image
[start-frontend] [0] Main process: createWindow called
[start-frontend] [0] [Main Process] Attempting to load preload script from: C:\KI\Janus-Projekt\frontend\preload.js
[start-backend] INFO:     127.0.0.1:56283 - "GET /api/models/catalog HTTP/1.1" 200 OK
[start-frontend] [0] [Electron Main] Backend is ready!
[start-backend] INFO:     127.0.0.1:56292 - "GET /api/personalities HTTP/1.1" 200 OK
[start-backend] INFO:     127.0.0.1:56291 - "GET /api/models/catalog HTTP/1.1" 200 OK
[start-backend] INFO:     127.0.0.1:56292 - "GET /api/personalities/active HTTP/1.1" 200 OK
[start-backend] INFO:     127.0.0.1:56291 - "GET /api/models/catalog HTTP/1.1" 200 OK
[start-backend] 2025-09-18 23:26:02 - janus_backend - [INFO] - Attempting to retrieve API keys.
[start-backend] 2025-09-18 23:26:02 - janus_backend - [INFO] - Successfully retrieved API key for provider: openai
[start-backend] 2025-09-18 23:26:02 - janus_backend - [INFO] - Successfully retrieved API key for provider: gemini
[start-backend] 2025-09-18 23:26:02 - janus_backend - [INFO] - No API key found for provider: anthropic
[start-backend] 2025-09-18 23:26:02 - janus_backend - [INFO] - No API key found for provider: cohere
[start-backend] INFO:     127.0.0.1:56293 - "GET /api/keys HTTP/1.1" 200 OK
[start-backend] INFO:     127.0.0.1:56292 - "GET /api/personalities/active HTTP/1.1" 200 OK
[start-backend] INFO:     127.0.0.1:56291 - "GET /api/last-used-model HTTP/1.1" 200 OK
[start-backend] 2025-09-18 23:26:02 - janus_backend - [INFO] - Attempting to retrieve API keys.
[start-backend] 2025-09-18 23:26:02 - janus_backend - [INFO] - Successfully retrieved API key for provider: openai
[start-backend] 2025-09-18 23:26:02 - janus_backend - [INFO] - Successfully retrieved API key for provider: gemini
[start-backend] 2025-09-18 23:26:02 - janus_backend - [INFO] - No API key found for provider: anthropic
[start-backend] 2025-09-18 23:26:02 - janus_backend - [INFO] - No API key found for provider: cohere
[start-backend] INFO:     127.0.0.1:56292 - "GET /api/keys HTTP/1.1" 200 OK
[start-backend] INFO:     127.0.0.1:56293 - "GET /api/models/selection/openai HTTP/1.1" 200 OK
[start-backend] INFO:     127.0.0.1:56291 - "GET /api/personalities HTTP/1.1" 200 OK
[start-backend] INFO:     127.0.0.1:56291 - "GET /api/models/selection/gemini HTTP/1.1" 200 OK
[start-frontend] [0] [34104:0918/232602.391:ERROR:CONSOLE(1)] "Request Autofill.enable failed. {"code":-32601,"message":"'Autofill.enable' wasn't found"}", source: devtools://devtools/bundled/core/protocol_client/protocol_client.js (1)
[start-frontend] [0] [34104:0918/232602.392:ERROR:CONSOLE(1)] "Request Autofill.setAddresses failed. {"code":-32601,"message":"'Autofill.setAddresses' wasn't found"}", source: devtools://devtools/bundled/core/protocol_client/protocol_client.js (1)
[start-backend] INFO:     127.0.0.1:56293 - "GET /api/costs/dashboard HTTP/1.1" 200 OK
[start-backend] INFO:     127.0.0.1:56291 - "GET /api/chats?include_archived=false HTTP/1.1" 200 OK
[start-backend] INFO:     127.0.0.1:56291 - "OPTIONS /api/chats HTTP/1.1" 200 OK
[start-backend] INFO:     127.0.0.1:56293 - "POST /api/chats HTTP/1.1" 200 OK
[start-backend] INFO:     127.0.0.1:56293 - "GET /api/chats?include_archived=false HTTP/1.1" 200 OK
[start-backend] INFO:     127.0.0.1:56293 - "GET /api/chats/1 HTTP/1.1" 200 OK
[start-backend] INFO:     127.0.0.1:56293 - "GET /api/chats/1 HTTP/1.1" 200 OK
[start-backend] INFO:     127.0.0.1:56293 - "GET /api/chats/1/messages HTTP/1.1" 200 OK
[start-backend] INFO:     127.0.0.1:56293 - "GET /api/chats/1/messages HTTP/1.1" 200 OK
[start-backend] INFO:     127.0.0.1:56293 - "OPTIONS /api/chats/1/title HTTP/1.1" 200 OK
[start-backend] INFO:     127.0.0.1:56293 - "PUT /api/chats/1/title HTTP/1.1" 200 OK
[start-backend] INFO:     127.0.0.1:56293 - "GET /api/chats?include_archived=false HTTP/1.1" 200 OK
[start-backend] INFO:     127.0.0.1:56293 - "OPTIONS /api/chat HTTP/1.1" 200 OK
[start-backend] 2025-09-18 23:26:09 - janus_backend - [INFO] - Image saved from bytes to C:\Users\pruve\AppData\Local\JanusDev\Janus Projekt\images\uploads\user-upload-18-18-09-25.png
[start-backend] 2025-09-18 23:26:09 - janus_backend - [INFO] - User-uploaded image saved to: /user_images/uploads/user-upload-18-18-09-25.png
[start-backend] 2025-09-18 23:26:09 - janus_backend - [INFO] - Explizite Werkzeug-Direktive wurde auf den System-Prompt angewendet.
[start-backend] 2025-09-18 23:26:09 - janus_backend - [INFO] - Using persona prompt for 'ai_assistant'
[start-backend] 2025-09-18 23:26:09 - janus_backend - [INFO] - Pure image analysis request detected. Suppressing chat history for focused analysis.
[start-backend] 2025-09-18 23:26:09 - janus_backend - [INFO] - [DEBUG] FINAL HYBRID Memory Context Generated (length: 0):
[start-backend] 2025-09-18 23:26:09 - janus_backend - [INFO] - Touched 0 memory snippets to update their relevance.
[start-backend] 2025-09-18 23:26:09 - janus_backend - [INFO] - Successfully added image data to the Gemini request parts.
[start-backend] 2025-09-18 23:26:09 - janus_backend - [INFO] - Initializing Gemini model for pure image analysis (no system instruction, no tools).
[start-backend] 2025-09-18 23:26:09 - grpc._cython.cygrpc - [DEBUG] - Using AsyncIOEngine.POLLER as I/O engine
[start-backend] 2025-09-18 23:26:11 - janus_backend - [INFO] -
[start-backend] --- USAGE TRACKING ---
[start-backend] Model: gemini-2.5-flash
[start-backend] Input Tokens: 374
[start-backend] Output Tokens: 36
[start-backend] Image Quality: N/A
[start-backend] Image Size: N/A
[start-backend] Total Cost: 0.00012120 �
[start-backend] ----------------------
[start-backend] 2025-09-18 23:26:11 - janus_backend - [INFO] - Final answer before check: 'Gerne, das Bild zeigt eine l�chelnde Frau mit langen, lockigen, rotbraunen Haaren und blauen Augen, die direkt in die Kamera blickt.'
[start-backend] 2025-09-18 23:26:11 - janus_backend - [INFO] - [FACT EXTRACTION] Starte Extraktion f�r Chat 1 mit Text: 'User: Gib eine kurze Best�tigung und die wichtigsten Merkmale des Bildes in einem Satz.
[start-backend] Assistant: Gerne, das Bild zeigt eine l�chelnde Frau mit langen, lockigen, rotbraunen Haaren und blauen Augen, die direkt in die Kamera blickt.'
[start-backend] 2025-09-18 23:26:11 - grpc._cython.cygrpc - [DEBUG] - Using AsyncIOEngine.POLLER as I/O engine
[start-backend] INFO:     127.0.0.1:56291 - "POST /api/chat HTTP/1.1" 200 OK
[start-backend] INFO:     127.0.0.1:56291 - "GET /api/costs/dashboard HTTP/1.1" 200 OK
[start-backend] 2025-09-18 23:26:12 - janus_backend - [INFO] -
[start-backend] --- USAGE TRACKING ---
[start-backend] Model: gemini-2.5-flash
[start-backend] Input Tokens: 542
[start-backend] Output Tokens: 3
[start-backend] Image Quality: N/A
[start-backend] Image Size: N/A
[start-backend] Total Cost: 0.00016335 �
[start-backend] ----------------------
[start-backend] 2025-09-18 23:26:12 - janus_backend - [INFO] - Extracted text: 'Keine.'
[start-backend] 2025-09-18 23:26:12 - janus_backend - [INFO] - Kein relevanter Fakt im Textblock gefunden.
[start-backend] 2025-09-18 23:26:28 - janus_backend - [INFO] - No new image uploaded. Checking history for existing image context.
[start-backend] 2025-09-18 23:26:28 - janus_backend - [INFO] - Image context is relevant. Reloading previous image: C:\Users\pruve\AppData\Local\JanusDev\Janus Projekt\images\uploads/user-upload-18-18-09-25.png
[start-backend] 2025-09-18 23:26:28 - janus_backend - [INFO] - Explizite Werkzeug-Direktive wurde auf den System-Prompt angewendet.
[start-backend] 2025-09-18 23:26:28 - janus_backend - [INFO] - Using persona prompt for 'ai_assistant'
[start-backend] 2025-09-18 23:26:28 - janus_backend - [INFO] - Image generation intent detected by keyword.
[start-backend] 2025-09-18 23:26:28 - janus_backend - [INFO] - Found reference image for image-to-image task: /user_images/uploads/user-upload-18-18-09-25.png
[start-backend] 2025-09-18 23:26:28 - janus_backend - [INFO] - Reference image provided: /user_images/uploads/user-upload-18-18-09-25.png. Preparing image-to-image generation.
[start-backend] 2025-09-18 23:26:28 - janus_backend - [INFO] - Calling Gemini image model 'gemini-2.5-flash-image-preview' with prompt: 'erstelle ein bild auf dem die frau auf dem referenzbild an einem strand sitzt' and reference image: True
[start-backend] 2025-09-18 23:26:28 - grpc._cython.cygrpc - [DEBUG] - Using AsyncIOEngine.POLLER as I/O engine
[start-backend] 2025-09-18 23:26:37 - janus_backend - [INFO] - Image saved from bytes to C:\Users\pruve\AppData\Local\JanusDev\Janus Projekt\images\ein-bild-auf-dem-die-frau-auf-dem-referenzbild-an-einem-strand-sitzt-18-09-25.png
[start-backend] 2025-09-18 23:26:37 - janus_backend - [INFO] -
[start-backend] --- USAGE TRACKING ---
[start-backend] Model: gemini-2.5-flash-image-preview
[start-backend] Input Tokens: N/A
[start-backend] Output Tokens: N/A
[start-backend] Image Quality: standard
[start-backend] Image Size: 1024x1024
[start-backend] Total Cost: 0.02000000 �
[start-backend] ----------------------
[start-backend] INFO:     127.0.0.1:56417 - "POST /api/chat HTTP/1.1" 200 OK
[start-backend] INFO:     127.0.0.1:56417 - "GET /api/costs/dashboard HTTP/1.1" 200 OK
[start-backend] INFO:     127.0.0.1:56459 - "GET /user_images/ein-bild-auf-dem-die-frau-auf-dem-referenzbild-an-einem-strand-sitzt-18-09-25.png HTTP/1.1" 200 OK
[start-backend] 2025-09-18 23:27:00 - janus_backend - [INFO] - No new image uploaded. Checking history for existing image context.
[start-backend] 2025-09-18 23:27:00 - janus_backend - [INFO] - Image context is relevant. Reloading previous image: C:\Users\pruve\AppData\Local\JanusDev\Janus Projekt\images\ein-bild-auf-dem-die-frau-auf-dem-referenzbild-an-einem-strand-sitzt-18-09-25.png
[start-backend] 2025-09-18 23:27:00 - janus_backend - [INFO] - Explizite Werkzeug-Direktive wurde auf den System-Prompt angewendet.
[start-backend] 2025-09-18 23:27:00 - janus_backend - [INFO] - Using persona prompt for 'ai_assistant'
[start-backend] 2025-09-18 23:27:00 - janus_backend - [INFO] - Pure image analysis request detected. Suppressing chat history for focused analysis.
[start-backend] 2025-09-18 23:27:00 - janus_backend - [INFO] - [DEBUG] FINAL HYBRID Memory Context Generated (length: 0):
[start-backend] 2025-09-18 23:27:00 - janus_backend - [INFO] - Touched 0 memory snippets to update their relevance.
[start-backend] 2025-09-18 23:27:00 - janus_backend - [INFO] - Successfully added image data to the Gemini request parts.
[start-backend] 2025-09-18 23:27:00 - janus_backend - [INFO] - Initializing Gemini model for pure image analysis (no system instruction, no tools).
[start-backend] 2025-09-18 23:27:00 - grpc._cython.cygrpc - [DEBUG] - Using AsyncIOEngine.POLLER as I/O engine
[start-backend] 2025-09-18 23:27:02 - janus_backend - [WARNING] - Gemini response was blocked. Reason: STOP. Safety Ratings: []
[start-backend] 2025-09-18 23:27:02 - janus_backend - [INFO] - Final answer before check: 'Meine Antwort wurde aufgrund von Sicherheitsrichtlinien blockiert. Bitte formuliere die Anfrage anders.'
[start-backend] 2025-09-18 23:27:02 - janus_backend - [INFO] - [FACT EXTRACTION] Starte Extraktion f�r Chat 1 mit Text: 'User: sehr sch�n, aber �nder die farbe des kleides zu rot
[start-backend] Assistant: Meine Antwort wurde aufgrund von Sicherheitsrichtlinien blockiert. Bitte formuliere die Anfrage anders.'
[start-backend] 2025-09-18 23:27:02 - grpc._cython.cygrpc - [DEBUG] - Using AsyncIOEngine.POLLER as I/O engine
[start-backend] INFO:     127.0.0.1:56565 - "POST /api/chat HTTP/1.1" 200 OK
[start-backend] INFO:     127.0.0.1:56565 - "GET /api/costs/dashboard HTTP/1.1" 200 OK
[start-backend] 2025-09-18 23:27:04 - janus_backend - [INFO] -
[start-backend] --- USAGE TRACKING ---
[start-backend] Model: gemini-2.5-flash
[start-backend] Input Tokens: 521
[start-backend] Output Tokens: 2
[start-backend] Image Quality: N/A
[start-backend] Image Size: N/A
[start-backend] Total Cost: 0.00015680 �
[start-backend] ----------------------
[start-backend] 2025-09-18 23:27:04 - janus_backend - [INFO] - Extracted text: 'Keine'
[start-backend] 2025-09-18 23:27:04 - janus_backend - [INFO] - Kein relevanter Fakt im Textblock gefunden.
[start-backend] 2025-09-18 23:27:27 - janus_backend - [INFO] - No new image uploaded. Checking history for existing image context.
[start-backend] 2025-09-18 23:27:27 - janus_backend - [INFO] - Image context is relevant. Reloading previous image: C:\Users\pruve\AppData\Local\JanusDev\Janus Projekt\images\ein-bild-auf-dem-die-frau-auf-dem-referenzbild-an-einem-strand-sitzt-18-09-25.png
[start-backend] 2025-09-18 23:27:27 - janus_backend - [INFO] - Explizite Werkzeug-Direktive wurde auf den System-Prompt angewendet.
[start-backend] 2025-09-18 23:27:27 - janus_backend - [INFO] - Using persona prompt for 'ai_assistant'
[start-backend] 2025-09-18 23:27:27 - janus_backend - [INFO] - Pure image analysis request detected. Suppressing chat history for focused analysis.
[start-backend] 2025-09-18 23:27:27 - janus_backend - [INFO] - [DEBUG] FINAL HYBRID Memory Context Generated (length: 0):
[start-backend] 2025-09-18 23:27:27 - janus_backend - [INFO] - Touched 0 memory snippets to update their relevance.
[start-backend] 2025-09-18 23:27:27 - janus_backend - [INFO] - Successfully added image data to the Gemini request parts.
[start-backend] 2025-09-18 23:27:27 - janus_backend - [INFO] - Initializing Gemini model for pure image analysis (no system instruction, no tools).
[start-backend] 2025-09-18 23:27:27 - grpc._cython.cygrpc - [DEBUG] - Using AsyncIOEngine.POLLER as I/O engine
[start-backend] 2025-09-18 23:27:29 - janus_backend - [INFO] -
[start-backend] --- USAGE TRACKING ---
[start-backend] Model: gemini-2.5-flash
[start-backend] Input Tokens: 372
[start-backend] Output Tokens: 18
[start-backend] Image Quality: N/A
[start-backend] Image Size: N/A
[start-backend] Total Cost: 0.00011610 �
[start-backend] ----------------------
[start-backend] 2025-09-18 23:27:29 - janus_backend - [INFO] - Final answer before check: 'Gerne, hier ist das Bild, auf dem die Frau ein rotes Kleid tr�gt:
[start-backend]
[start-backend] '
[start-backend] 2025-09-18 23:27:29 - janus_backend - [INFO] - [FACT EXTRACTION] Starte Extraktion f�r Chat 1 mit Text: 'User: die frau auf dem bild soll statt eines blauen ein rotes kleis tragen
[start-backend] Assistant: Gerne, hier ist das Bild, auf dem die Frau ein rotes Kleid tr�gt:
[start-backend]
[start-backend] '
[start-backend] 2025-09-18 23:27:29 - grpc._cython.cygrpc - [DEBUG] - Using AsyncIOEngine.POLLER as I/O engine
[start-backend] INFO:     127.0.0.1:56689 - "POST /api/chat HTTP/1.1" 200 OK
[start-backend] INFO:     127.0.0.1:56689 - "GET /api/costs/dashboard HTTP/1.1" 200 OK
[start-backend] 2025-09-18 23:27:32 - janus_backend - [INFO] - Beginne Zusammenfassung f�r Chat ID: 1
[start-backend] INFO:     127.0.0.1:56689 - "POST /api/chats HTTP/1.1" 200 OK
[start-backend] INFO:     127.0.0.1:56689 - "GET /api/chats?include_archived=false HTTP/1.1" 200 OK
[start-backend] INFO:     127.0.0.1:56689 - "GET /api/chats/2 HTTP/1.1" 200 OK
[start-backend] INFO:     127.0.0.1:56689 - "GET /api/chats/2/messages HTTP/1.1" 200 OK
[start-backend] 2025-09-18 23:27:33 - janus_backend - [INFO] -
[start-backend] --- USAGE TRACKING ---
[start-backend] Model: gemini-2.5-flash
[start-backend] Input Tokens: 523
[start-backend] Output Tokens: 2
[start-backend] Image Quality: N/A
[start-backend] Image Size: N/A
[start-backend] Total Cost: 0.00015740 �
[start-backend] ----------------------
[start-backend] 2025-09-18 23:27:33 - janus_backend - [INFO] - Extracted text: 'Keine'
[start-backend] 2025-09-18 23:27:33 - janus_backend - [INFO] - Kein relevanter Fakt im Textblock gefunden.
[start-backend] 2025-09-18 23:27:34 - janus_backend - [INFO] -
[start-backend] --- USAGE TRACKING ---
[start-backend] Model: gemini-2.5-flash
[start-backend] Input Tokens: 191
[start-backend] Output Tokens: 51
[start-backend] Image Quality: N/A
[start-backend] Image Size: N/A
[start-backend] Total Cost: 0.00007005 �
[start-backend] ----------------------
[start-backend] 2025-09-18 23:27:34 - janus_backend - [INFO] - Generating embedding for text: '[Link oder das Bild selbst, wenn ich Bilder direkt einbetten k�nnte]
[start-backend]
[start-backend] Bitte beachte, dass die �nderung des Kleides die Darstellung der Frau oder des Strandes leicht beeinflussen kann, je nachdem wie pr�zise die Bearbeitung erfolgt.'
Batches: 100%|##########| 1/1 [00:00<00:00, 25.40it/s]
[start-backend] 2025-09-18 23:27:34 - janus_backend - [INFO] - Embedding generated successfully for text: '[Link oder das Bild selbst, wenn ich Bilder direkt einbetten k�nnte]
[start-backend]
[start-backend] Bitte beachte, dass die �nderung des Kleides die Darstellung der Frau oder des Strandes leicht beeinflussen kann, je nachdem wie pr�zise die Bearbeitung erfolgt.'
[start-backend] 2025-09-18 23:27:34 - janus_backend - [INFO] - Chat 1 erfolgreich zusammengefasst: '[Link oder das Bild selbst, wenn ich Bilder direkt einbetten k�nnte]
[start-backend]
[start-backend] Bitte beachte, dass die �nderung des Kleides die Darstellung der Frau oder des Strandes leicht beeinflussen kann, je nachdem wie pr�zise die Bearbeitung erfolgt.'
[start-backend] INFO:     127.0.0.1:56766 - "OPTIONS /api/chats/2/title HTTP/1.1" 200 OK
[start-backend] INFO:     127.0.0.1:56766 - "PUT /api/chats/2/title HTTP/1.1" 200 OK
[start-backend] INFO:     127.0.0.1:56766 - "GET /api/chats?include_archived=false HTTP/1.1" 200 OK
[start-backend] 2025-09-18 23:27:42 - janus_backend - [INFO] - No new image uploaded. Checking history for existing image context.
[start-backend] 2025-09-18 23:27:42 - janus_backend - [INFO] - Explizite Werkzeug-Direktive wurde auf den System-Prompt angewendet.
[start-backend] 2025-09-18 23:27:42 - janus_backend - [INFO] - Using persona prompt for 'ai_assistant'
[start-backend] 2025-09-18 23:27:42 - janus_backend - [INFO] - Image generation intent detected by keyword.
[start-backend] 2025-09-18 23:27:42 - janus_backend - [INFO] - Calling Gemini image model 'gemini-2.5-flash-image-preview' with prompt: 'erstelle ein bild eines k�tzchens' and reference image: False
[start-backend] 2025-09-18 23:27:42 - grpc._cython.cygrpc - [DEBUG] - Using AsyncIOEngine.POLLER as I/O engine
[start-backend] 2025-09-18 23:27:49 - janus_backend - [INFO] - Image saved from bytes to C:\Users\pruve\AppData\Local\JanusDev\Janus Projekt\images\ein-bild-eines-ktzchens-18-09-25.png
[start-backend] 2025-09-18 23:27:49 - janus_backend - [INFO] -
[start-backend] --- USAGE TRACKING ---
[start-backend] Model: gemini-2.5-flash-image-preview
[start-backend] Input Tokens: N/A
[start-backend] Output Tokens: N/A
[start-backend] Image Quality: standard
[start-backend] Image Size: 1024x1024
[start-backend] Total Cost: 0.02000000 �
[start-backend] ----------------------
[start-backend] INFO:     127.0.0.1:56766 - "POST /api/chat HTTP/1.1" 200 OK
[start-backend] INFO:     127.0.0.1:56766 - "GET /api/costs/dashboard HTTP/1.1" 200 OK
[start-backend] INFO:     127.0.0.1:56802 - "GET /user_images/ein-bild-eines-ktzchens-18-09-25.png HTTP/1.1" 200 OK
[start-backend] 2025-09-18 23:28:00 - janus_backend - [INFO] - No new image uploaded. Checking history for existing image context.
[start-backend] 2025-09-18 23:28:00 - janus_backend - [INFO] - Image context is relevant. Reloading previous image: C:\Users\pruve\AppData\Local\JanusDev\Janus Projekt\images\ein-bild-eines-ktzchens-18-09-25.png
[start-backend] 2025-09-18 23:28:00 - janus_backend - [INFO] - Explizite Werkzeug-Direktive wurde auf den System-Prompt angewendet.
[start-backend] 2025-09-18 23:28:00 - janus_backend - [INFO] - Using persona prompt for 'ai_assistant'
[start-backend] 2025-09-18 23:28:00 - janus_backend - [INFO] - Pure image analysis request detected. Suppressing chat history for focused analysis.
[start-backend] 2025-09-18 23:28:00 - janus_backend - [INFO] - [DEBUG] FINAL HYBRID Memory Context Generated (length: 0):
[start-backend] 2025-09-18 23:28:00 - janus_backend - [INFO] - Touched 0 memory snippets to update their relevance.
[start-backend] 2025-09-18 23:28:00 - janus_backend - [INFO] - Successfully added image data to the Gemini request parts.
[start-backend] 2025-09-18 23:28:00 - janus_backend - [INFO] - Initializing Gemini model for pure image analysis (no system instruction, no tools).
[start-backend] 2025-09-18 23:28:00 - grpc._cython.cygrpc - [DEBUG] - Using AsyncIOEngine.POLLER as I/O engine
[start-backend] 2025-09-18 23:28:07 - janus_backend - [INFO] -
[start-backend] --- USAGE TRACKING ---
[start-backend] Model: gemini-2.5-flash
[start-backend] Input Tokens: 366
[start-backend] Output Tokens: 13
[start-backend] Image Quality: N/A
[start-backend] Image Size: N/A
[start-backend] Total Cost: 0.00011305 �
[start-backend] ----------------------
[start-backend] 2025-09-18 23:28:07 - janus_backend - [INFO] - Final answer before check: 'Gerne, hier ist dein Bild mit zus�tzlichen Schmetterlingen!
[start-backend]
[start-backend] '
[start-backend] 2025-09-18 23:28:07 - janus_backend - [INFO] - [FACT EXTRACTION] Starte Extraktion f�r Chat 2 mit Text: 'User: f�ge dem bild ein paar schmetterlinge hinzu
[start-backend] Assistant: Gerne, hier ist dein Bild mit zus�tzlichen Schmetterlingen!
[start-backend]
[start-backend] '
[start-backend] 2025-09-18 23:28:07 - grpc._cython.cygrpc - [DEBUG] - Using AsyncIOEngine.POLLER as I/O engine
[start-backend] INFO:     127.0.0.1:56851 - "POST /api/chat HTTP/1.1" 200 OK
[start-backend] INFO:     127.0.0.1:56851 - "GET /api/costs/dashboard HTTP/1.1" 200 OK
[start-backend] 2025-09-18 23:28:08 - janus_backend - [INFO] -
[start-backend] --- USAGE TRACKING ---
[start-backend] Model: gemini-2.5-flash
[start-backend] Input Tokens: 512
[start-backend] Output Tokens: 3
[start-backend] Image Quality: N/A
[start-backend] Image Size: N/A
[start-backend] Total Cost: 0.00015435 �
[start-backend] ----------------------
[start-backend] 2025-09-18 23:28:08 - janus_backend - [INFO] - Extracted text: 'Keine.'
[start-backend] 2025-09-18 23:28:08 - janus_backend - [INFO] - Kein relevanter Fakt im Textblock gefunden.
[start-backend] INFO:     127.0.0.1:55216 - "GET /api/chats/1 HTTP/1.1" 200 OK
[start-backend] INFO:     127.0.0.1:55216 - "GET /api/chats/1/messages HTTP/1.1" 200 OK
[start-backend] INFO:     127.0.0.1:55217 - "GET /user_images/uploads/user-upload-18-18-09-25.png HTTP/1.1" 200 OK
[start-backend] INFO:     127.0.0.1:55218 - "GET /user_images/ein-bild-auf-dem-die-frau-auf-dem-referenzbild-an-einem-strand-sitzt-18-09-25.png HTTP/1.1" 304 Not Modified
[start-backend] INFO:     127.0.0.1:55996 - "GET /api/chats/2 HTTP/1.1" 200 OK
[start-backend] INFO:     127.0.0.1:55996 - "GET /api/chats/2/messages HTTP/1.1" 200 OK