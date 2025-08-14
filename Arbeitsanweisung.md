PS C:\KI\Janus-Projekt> npm run start-dev

> janus-projekt@1.0.0 start-dev
> concurrently "npm run start-electron" "npm run start-vite" "C:\KI\Janus-Projekt\backend\venv\Scripts\python.exe -m uvicorn backend.main:app --reload --port 8000"

[2] INFO:     Will watch for changes in these directories: ['C:\\KI\\Janus-Projekt']
[2] INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
[2] INFO:     Started reloader process [28148] using WatchFiles
[0]
[0] > janus-projekt@1.0.0 start-electron
[0] > cross-env NODE_ENV=development electron .
[0]
[1]
[1] > janus-projekt@1.0.0 start-vite
[1] > vite
[1]
[0]
[1] The CJS build of Vite's Node API is deprecated. See https://vite.dev/guide/troubleshooting.html#vite-cjs-node-api-deprecated for more details.
[1]
[1]   VITE v5.4.19  ready in 275 ms
[1]
[1]   ➜  Local:   http://localhost:5173/
[1]   ➜  Network: use --host to expose
[2] INFO:     Started server process [29536]
[2] INFO:     Waiting for application startup.
[2] INFO:     Application startup complete.
[2] Database initialized.
[2] Database initialized.
[2] INFO:     127.0.0.1:57813 - "GET /api/costs/dashboard HTTP/1.1" 200 OK
[2] DEBUG: Attempting to load model catalog from: C:\KI\Janus-Projekt\backend\model_catalog.json
[2] DEBUG: Does model catalog file exist? True
[2] INFO:     127.0.0.1:57813 - "GET /api/models/selection/openai HTTP/1.1" 200 OK
[2] INFO:     127.0.0.1:57815 - "GET /api/costs/details HTTP/1.1" 200 OK
[2] DEBUG: Attempting to load model catalog from: C:\KI\Janus-Projekt\backend\model_catalog.json
[2] DEBUG: Does model catalog file exist? True
[2] INFO:     127.0.0.1:57815 - "GET /api/models/selection/gemini HTTP/1.1" 200 OK
[2] INFO:     127.0.0.1:57812 - "OPTIONS /api/chat HTTP/1.1" 200 OK
[2] Call LLM - Provider: openai, Model: gpt-4o-mini
[2] INFO:     127.0.0.1:57811 - "POST /api/chat HTTP/1.1" 500 Internal Server Error
[2] Task exception was never retrieved
[2] future: <Task finished name='Task-13' coro=<AsyncClient.aclose() done, defined at C:\KI\Janus-Projekt\backend\venv\Lib\site-packages\httpx\_client.py:1978> exception=AttributeError("'AsyncHttpxClientWrapper' object has no attribute '_state'")>
[2] Traceback (most recent call last):
[2]   File "C:\KI\Janus-Projekt\backend\venv\Lib\site-packages\httpx\_client.py", line 1982, in aclose
[2]     if self._state != ClientState.CLOSED:
[2]        ^^^^^^^^^^^
[2] AttributeError: 'AsyncHttpxClientWrapper' object has no attribute '_state'