2025-09-06 21:43:26 - janus_backend - [INFO] - Logger wurde initialisiert.
2025-09-06 21:43:30 - sentence_transformers.SentenceTransformer - [INFO] - Use pytorch device_name: cpu
2025-09-06 21:43:30 - sentence_transformers.SentenceTransformer - [INFO] - Load pretrained SentenceTransformer: C:\Program Files\Janus Projekt\resources\dist\janus_backend\_internal\backend/model_cache/all-MiniLM-L6-v2
2025-09-06 21:43:30 - janus_backend - [INFO] - Logger wurde initialisiert.
2025-09-06 21:43:30 - janus_backend - [INFO] - Logger wurde initialisiert.
2025-09-06 21:43:30 - janus_backend - [INFO] - Application Data Directory: C:\Users\pruve\AppData\Local\JanusDev\Janus Projekt
2025-09-06 21:43:30 - asyncio - [DEBUG] - Using proactor: IocpProactor
INFO:     127.0.0.1:63489 - "GET /api/models/catalog HTTP/1.1" 200 OK
INFO:     127.0.0.1:63490 - "GET /api/models/catalog HTTP/1.1" 200 OK
INFO:     127.0.0.1:63490 - "GET /api/models/catalog HTTP/1.1" 200 OK
2025-09-06 21:43:30 - janus_backend - [INFO] - Attempting to retrieve API keys.
2025-09-06 21:43:30 - keyring.backend - [DEBUG] - Loading KWallet
2025-09-06 21:43:30 - keyring.backend - [DEBUG] - Loading SecretService
2025-09-06 21:43:30 - keyring.backend - [DEBUG] - Loading Windows
2025-09-06 21:43:30 - win32ctypes.core.cffi - [DEBUG] - Loaded cffi backend
2025-09-06 21:43:30 - keyring.backend - [DEBUG] - Loading chainer
2025-09-06 21:43:30 - keyring.backend - [DEBUG] - Loading libsecret
2025-09-06 21:43:30 - keyring.backend - [DEBUG] - Loading macOS
2025-09-06 21:43:30 - janus_backend - [INFO] - Successfully retrieved API key for provider: openai
2025-09-06 21:43:30 - janus_backend - [INFO] - Successfully retrieved API key for provider: gemini
2025-09-06 21:43:30 - janus_backend - [INFO] - No API key found for provider: anthropic
2025-09-06 21:43:30 - janus_backend - [INFO] - No API key found for provider: cohere
INFO:     127.0.0.1:63491 - "GET /api/keys HTTP/1.1" 200 OK
INFO:     127.0.0.1:63490 - "GET /api/last-used-model HTTP/1.1" 200 OK
2025-09-06 21:43:30 - janus_backend - [INFO] - Attempting to retrieve API keys.
2025-09-06 21:43:30 - janus_backend - [INFO] - Successfully retrieved API key for provider: openai
2025-09-06 21:43:30 - janus_backend - [INFO] - Successfully retrieved API key for provider: gemini
2025-09-06 21:43:30 - janus_backend - [INFO] - No API key found for provider: anthropic
2025-09-06 21:43:30 - janus_backend - [INFO] - No API key found for provider: cohere
INFO:     127.0.0.1:63490 - "GET /api/keys HTTP/1.1" 200 OK
INFO:     127.0.0.1:63491 - "GET /api/models/selection/openai HTTP/1.1" 200 OK
INFO:     127.0.0.1:63491 - "GET /api/models/selection/gemini HTTP/1.1" 200 OK
INFO:     127.0.0.1:63490 - "GET /api/costs/dashboard HTTP/1.1" 200 OK
INFO:     127.0.0.1:63491 - "GET /api/chats?include_archived=false HTTP/1.1" 200 OK
INFO:     127.0.0.1:63491 - "GET /api/chats/1 HTTP/1.1" 200 OK
INFO:     127.0.0.1:63491 - "GET /api/chats/1/messages HTTP/1.1" 200 OK
2025-09-06 21:43:36 - janus_backend - [INFO] - Snippet: 'Keine.')
2025-09-06 21:43:36 - janus_backend - [INFO] - Snippet: 'Die Anfrage an die API ist nach mehreren Versuchen fehlgeschlagen.')
2025-09-06 21:43:36 - janus_backend - [INFO] - find_similar_snippets: Returning 2 similar memories.
2025-09-06 21:43:36 - janus_backend - [INFO] - reason_and_respond: Original user_prompt=hi
2025-09-06 21:43:36 - grpc._cython.cygrpc - [DEBUG] - Using AsyncIOEngine.POLLER as I/O engine
2025-09-06 21:43:36 - janus_backend - [WARNING] - An error occurred with Gemini API, retrying... Error: 400 API key expired. Please renew the API key. [reason: "API_KEY_INVALID"
domain: "googleapis.com"
metadata {
  key: "service"
  value: "generativelanguage.googleapis.com"
}
, locale: "en-US"
message: "API key expired. Please renew the API key."
]
2025-09-06 21:43:39 - janus_backend - [WARNING] - An error occurred with Gemini API, retrying... Error: 400 API key expired. Please renew the API key. [reason: "API_KEY_INVALID"
domain: "googleapis.com"
metadata {
  key: "service"
  value: "generativelanguage.googleapis.com"
}
, locale: "en-US"
message: "API key expired. Please renew the API key."
]
2025-09-06 21:43:41 - janus_backend - [WARNING] - An error occurred with Gemini API, retrying... Error: 400 API key expired. Please renew the API key. [reason: "API_KEY_INVALID"
domain: "googleapis.com"
metadata {
  key: "service"
  value: "generativelanguage.googleapis.com"
}
, locale: "en-US"
message: "API key expired. Please renew the API key."
]
2025-09-06 21:43:41 - janus_backend - [ERROR] - API call failed after multiple retries: RetryError[<Future at 0x1b545c0a510 state=finished raised InvalidArgument>]
2025-09-06 21:43:41 - janus_backend - [INFO] - Attempting to extract and save facts for chat 1 from text: 'User: hi
Assistant: Die Anfrage an die API ist nach mehreren Versuchen fehlgeschlagen.'
INFO:     127.0.0.1:63491 - "POST /api/chat HTTP/1.1" 200 OK
INFO:     127.0.0.1:63491 - "GET /api/costs/dashboard HTTP/1.1" 200 OK
2025-09-06 21:43:41 - janus_backend - [WARNING] - An error occurred with Gemini API, retrying... Error: 400 API key expired. Please renew the API key. [reason: "API_KEY_INVALID"
domain: "googleapis.com"
metadata {
  key: "service"
  value: "generativelanguage.googleapis.com"
}
, locale: "en-US"
message: "API key expired. Please renew the API key."
]
2025-09-06 21:43:43 - janus_backend - [WARNING] - An error occurred with Gemini API, retrying... Error: 400 API key expired. Please renew the API key. [reason: "API_KEY_INVALID"
domain: "googleapis.com"
metadata {
  key: "service"
  value: "generativelanguage.googleapis.com"
}
, locale: "en-US"
message: "API key expired. Please renew the API key."
]
2025-09-06 21:43:45 - janus_backend - [WARNING] - An error occurred with Gemini API, retrying... Error: 400 API key expired. Please renew the API key. [reason: "API_KEY_INVALID"
domain: "googleapis.com"
metadata {
  key: "service"
  value: "generativelanguage.googleapis.com"
}
, locale: "en-US"
message: "API key expired. Please renew the API key."
]
2025-09-06 21:43:45 - janus_backend - [ERROR] - API call failed after multiple retries: RetryError[<Future at 0x1b545bd6210 state=finished raised InvalidArgument>]
2025-09-06 21:43:45 - janus_backend - [INFO] - Extracted text: 'Die Anfrage an die API ist nach mehreren Versuchen fehlgeschlagen.'
2025-09-06 21:43:45 - janus_backend - [INFO] - Snippet: 'Die Anfrage an die API ist nach mehreren Versuchen fehlgeschlagen.')
2025-09-06 21:43:45 - janus_backend - [INFO] - find_similar_snippets: Returning 1 similar memories.
2025-09-06 21:43:45 - janus_backend - [INFO] - Bekannter Fakt ignoriert (Duplikat): 'Die Anfrage an die API ist nach mehreren Versuchen fehlgeschlagen.'.
2025-09-06 21:43:48 - janus_backend - [INFO] - Snippet: 'Keine.')
2025-09-06 21:43:48 - janus_backend - [INFO] - find_similar_snippets: Returning 1 similar memories.
2025-09-06 21:43:48 - janus_backend - [INFO] - reason_and_respond: Original user_prompt=hallo
2025-09-06 21:43:49 - openai._base_client - [DEBUG] - Request options: {'method': 'post', 'url': '/chat/completions', 'files': None, 'idempotency_key': 'stainless-python-retry-29ceaeb4-1a63-40b2-b177-958d21d49ab3', 'json_data': {'messages': [{'role': 'user', 'content': "Du bist Janus, ein hilfreicher KI-Assistent, der logisch schlussfolgert. Deine Aufgabe ist es, die Frage des Benutzers zu beantworten.\n**DEINE GOLDENE REGEL: Deine Antwort MUSS sich auf die unten stehenden BEWEISE st tzen. Erfinde keine Fakten.**\n\n1.  **FAKTEN AUS DEM LANGZEITGED CHTNIS:** Dies ist die absolute Wahrheit  ber den Benutzer.\n2.  **AKTUELLER GESPR CHSVERLAUF:** Dieser liefert den unmittelbaren Kontext.\n\n**DEIN VORGEHEN:**\n- **KOMBINIERE FAKTEN:** Deine wichtigste F higkeit ist es, Fakten zu kombinieren, um eine logische Schlussfolgerung zu ziehen. (Beispiel: Wenn FAKT A 'Kalle mag Blau' ist und FAKT B 'Das Auto des Benutzers ist blau' ist, lautet die Schlussfolgerung 'Kalle w rde eine Fahrt in dem Auto gefallen').\n- **ANTWORTE HILFREICH:** Formuliere eine direkte und n tzliche Antwort auf die Frage des Benutzers, basierend auf den Fakten und deinen Schlussfolgerungen.\n- **GIB WISSENSL CKEN ZU:** Wenn die Beweise nicht ausreichen, um eine Frage vollst ndig zu beantworten, sage das klar und deutlich.\n\n--- FAKTEN AUS DEM LANGZEITGED CHTNIS ---\n- Keine.\n\nAllowed workspaces:\n- Test: C:\\Test\n- Desktop: C:\\Users\\pruve\\Desktop\n- workspace: C:\\Users\\pruve\\AppData\\Local\\JanusDev\\Janus Projekt\\workspace\n\n\n--- AKTUELLER GESPR CHSVERLAUF ---\nuser: hi\nassistant: Hallo! Wie kann ich Ihnen helfen? Wenn Sie Fragen haben oder Unterst tzung ben tigen, lassen Sie es mich einfach wissen!\nuser: erstell auf dem desktop einen ordner namens fritsche\nassistant: Ergebnis von Tool 'create_directory_tool': Ordner 'C:\\Users\\pruve\\Desktop\\fritsche' wurde erfolgreich erstellt.\nuser: erstell im ordner test einen ordner fisch\nassistant: Ergebnis von Tool 'create_directory_tool': Ordner 'C:\\Test\\fisch' wurde erfolgreich erstellt.\nuser: hi\nassistant: Die Anfrage an die API ist nach mehreren Versuchen fehlgeschlagen.\nuser: hi\nassistant: Die Anfrage an die API ist nach mehreren Versuchen fehlgeschlagen.\nuser: hi\nassistant: Hallo! Es scheint, dass ich in letzter Zeit einige Schwierigkeiten hatte, Anfragen zu bearbeiten. Wie kann ich Ihnen heute helfen? Wenn Sie spezifische Fragen oder W nsche haben, lassen Sie es mich bitte wissen!\nuser: hallo\nassistant: Die Anfrage an die API ist nach mehreren Versuchen fehlgeschlagen.\nuser: erstelle ein bild einer eule\nuser: erstelle ein bild einer eule\nassistant: Es tut mir leid, aber die Anfrage an die API, um ein Bild einer Eule zu erstellen, ist nach mehreren Versuchen fehlgeschlagen. M chten Sie es sp ter noch einmal versuchen oder gibt es etwas anderes, bei dem ich Ihnen helfen kann?\nuser: hi\nassistant: Hallo! Es scheint, dass ich Schwierigkeiten hatte, Anfragen zu bearbeiten, aber ich bin hier, um zu helfen. Gibt es etwas Spezielles, wor ber Sie sprechen oder was Sie tun m chten?\nuser: hi\n\n--- FRAGE DES BENUTZERS ---\nhallo\n\n--- ANTWORT ---"}], 'model': 'gpt-4o-mini', 'tool_choice': 'auto', 'tools': [{'type': 'function', 'function': {'name': 'generate_image_tool', 'description': None, 'parameters': {'type': 'object', 'properties': {'prompt': {'title': 'Prompt', 'type': 'string'}, 'size': {'anyOf': [{'type': 'string'}, {'type': 'null'}], 'default': '1024x1024', 'title': 'Size'}, 'quality': {'anyOf': [{'type': 'string'}, {'type': 'null'}], 'default': 'standard', 'title': 'Quality'}, 'response_format': {'anyOf': [{'type': 'string'}, {'type': 'null'}], 'default': 'url', 'title': 'Response Format'}}, 'required': ['prompt']}}}, {'type': 'function', 'function': {'name': 'cross_chat_memory_tool', 'description': 'Ruft Zusammenfassungen der letzten Konversationen ab, um Fragen  ber die Vergangenheit zu beantworten.', 'parameters': {'type': 'object', 'properties': {'query': {'title': 'Query', 'type': 'string'}}, 'required': ['query']}}}, {'type': 'function', 'function': {'name': 'create_file_tool', 'description': 'Erstellt eine neue Datei im Workspace.', 'parameters': {'type': 'object', 'properties': {'path': {'title': 'Path', 'type': 'string'}, 'content': {'anyOf': [{'type': 'string'}, {'type': 'null'}], 'default': '', 'title': 'Content'}}, 'required': ['path']}}}, {'type': 'function', 'function': {'name': 'read_file_tool', 'description': 'Liest den Inhalt einer Datei aus dem Workspace.', 'parameters': {'type': 'object', 'properties': {'path': {'title': 'Path', 'type': 'string'}}, 'required': ['path']}}}, {'type': 'function', 'function': {'name': 'delete_file_tool', 'description': 'L scht eine Datei aus dem Workspace.', 'parameters': {'type': 'object', 'properties': {'path': {'title': 'Path', 'type': 'string'}}, 'required': ['path']}}}, {'type': 'function', 'function': {'name': 'list_directory_tool', 'description': "Listet den Inhalt eines Ordners auf. Kann mit einem Wildcard-Muster wie '*.png' oder 'test*' filtern.", 'parameters': {'type': 'object', 'properties': {'path': {'title': 'Path', 'type': 'string'}, 'pattern': {'anyOf': [{'type': 'string'}, {'type': 'null'}], 'default': None, 'title': 'Pattern'}}, 'required': ['path']}}}, {'type': 'function', 'function': {'name': 'create_directory_tool', 'description': 'Erstellt einen neuen, leeren Ordner im Workspace.', 'parameters': {'type': 'object', 'properties': {'path': {'title': 'Path', 'type': 'string'}}, 'required': ['path']}}}, {'type': 'function', 'function': {'name': 'delete_directory_tool', 'description': 'L scht einen Ordner und dessen gesamten Inhalt aus dem Workspace.', 'parameters': {'type': 'object', 'properties': {'path': {'title': 'Path', 'type': 'string'}}, 'required': ['path']}}}, {'type': 'function', 'function': {'name': 'rename_file_tool', 'description': 'Benennt eine Datei oder einen Ordner um.', 'parameters': {'type': 'object', 'properties': {'old_path': {'title': 'Old Path', 'type': 'string'}, 'new_path': {'title': 'New Path', 'type': 'string'}}, 'required': ['old_path', 'new_path']}}}, {'type': 'function', 'function': {'name': 'move_file_tool', 'description': 'Verschiebt eine einzelne Datei oder einen Ordner.', 'parameters': {'type': 'object', 'properties': {'source_path': {'title': 'Source Path', 'type': 'string'}, 'destination_path': {'title': 'Destination Path', 'type': 'string'}}, 'required': ['source_path', 'destination_path']}}}, {'type': 'function', 'function': {'name': 'move_files_tool', 'description': "Verschiebt mehrere Dateien, die einem Muster (z.B. '*.png') entsprechen, von einem Ordner in einen anderen. Ideal f r Massenoperationen.", 'parameters': {'type': 'object', 'properties': {'source_directory': {'title': 'Source Directory', 'type': 'string'}, 'destination_directory': {'title': 'Destination Directory', 'type': 'string'}, 'pattern': {'title': 'Pattern', 'type': 'string'}}, 'required': ['source_directory', 'destination_directory', 'pattern']}}}, {'type': 'function', 'function': {'name': 'list_allowed_workspaces_tool', 'description': 'Listet alle f r Dateioperationen freigegebenen Ordner (Workspaces) auf.', 'parameters': {'type': 'object', 'properties': {}, 'required': []}}}]}}
2025-09-06 21:43:49 - openai._base_client - [DEBUG] - Sending HTTP Request: POST https://api.openai.com/v1/chat/completions
2025-09-06 21:43:49 - httpcore.connection - [DEBUG] - connect_tcp.started host='api.openai.com' port=443 local_address=None timeout=5.0 socket_options=None
2025-09-06 21:43:49 - httpcore.connection - [DEBUG] - connect_tcp.complete return_value=<httpcore._backends.anyio.AnyIOStream object at 0x000001B5462D8D10>
2025-09-06 21:43:49 - httpcore.connection - [DEBUG] - start_tls.started ssl_context=<ssl.SSLContext object at 0x000001B545E716D0> server_hostname='api.openai.com' timeout=5.0
2025-09-06 21:43:49 - httpcore.connection - [DEBUG] - start_tls.complete return_value=<httpcore._backends.anyio.AnyIOStream object at 0x000001B5462D8D90>
2025-09-06 21:43:49 - httpcore.http11 - [DEBUG] - send_request_headers.started request=<Request [b'POST']>
2025-09-06 21:43:49 - httpcore.http11 - [DEBUG] - send_request_headers.complete
2025-09-06 21:43:49 - httpcore.http11 - [DEBUG] - send_request_body.started request=<Request [b'POST']>
2025-09-06 21:43:49 - httpcore.http11 - [DEBUG] - send_request_body.complete
2025-09-06 21:43:49 - httpcore.http11 - [DEBUG] - receive_response_headers.started request=<Request [b'POST']>
2025-09-06 21:43:49 - httpcore.http11 - [DEBUG] - receive_response_headers.complete return_value=(b'HTTP/1.1', 200, b'OK', [(b'Date', b'Sat, 06 Sep 2025 19:43:52 GMT'), (b'Content-Type', b'application/json'), (b'Transfer-Encoding', b'chunked'), (b'Connection', b'keep-alive'), (b'access-control-expose-headers', b'X-Request-ID'), (b'openai-organization', b'user-9rymi7trhkh9wx0cjpzb4txg'), (b'openai-processing-ms', b'648'), (b'openai-project', b'proj_xZDNucsxSbdjkba6PitMv58d'), (b'openai-version', b'2020-10-01'), (b'x-envoy-upstream-service-time', b'658'), (b'x-ratelimit-limit-requests', b'5000'), (b'x-ratelimit-limit-tokens', b'2000000'), (b'x-ratelimit-remaining-requests', b'4999'), (b'x-ratelimit-remaining-tokens', b'1999292'), (b'x-ratelimit-reset-requests', b'12ms'), (b'x-ratelimit-reset-tokens', b'21ms'), (b'x-request-id', b'req_5fde3e8a8efd4854949e487cb45ccc97'), (b'cf-cache-status', b'DYNAMIC'), (b'Set-Cookie', b'__cf_bm=yhwcx1hr8tTTzdjZSF741V0D0ccWcnV4oY2k7ypKT0E-1757187832-1.0.1.1-Yh7fOoRBxkS6QQ4MBF58v.MbH1on6VM_Bd77vP_VRd0UJqNEXJnHFU.6_FRwBEkMoTEZZ6ZCJQ4PwlZXMPlD83HCU9wFiiCr5e.d1EK158E; path=/; expires=Sat, 06-Sep-25 20:13:52 GMT; domain=.api.openai.com; HttpOnly; Secure; SameSite=None'), (b'Strict-Transport-Security', b'max-age=31536000; includeSubDomains; preload'), (b'X-Content-Type-Options', b'nosniff'), (b'Set-Cookie', b'_cfuvid=blhyxxpVno0NTpYFYGJjQlyutYE3XMhy_Ovr2fry0TM-1757187832815-0.0.1.1-604800000; path=/; domain=.api.openai.com; HttpOnly; Secure; SameSite=None'), (b'Server', b'cloudflare'), (b'CF-RAY', b'97b0752deeecb92a-AMS'), (b'Content-Encoding', b'gzip'), (b'alt-svc', b'h3=":443"; ma=86400')])
2025-09-06 21:43:49 - httpx - [INFO] - HTTP Request: POST https://api.openai.com/v1/chat/completions "HTTP/1.1 200 OK"
2025-09-06 21:43:49 - httpcore.http11 - [DEBUG] - receive_response_body.started request=<Request [b'POST']>
2025-09-06 21:43:49 - httpcore.http11 - [DEBUG] - receive_response_body.complete
2025-09-06 21:43:49 - httpcore.http11 - [DEBUG] - response_closed.started
2025-09-06 21:43:49 - httpcore.http11 - [DEBUG] - response_closed.complete
2025-09-06 21:43:49 - openai._base_client - [DEBUG] - HTTP Response: POST https://api.openai.com/v1/chat/completions "200 OK" Headers([('date', 'Sat, 06 Sep 2025 19:43:52 GMT'), ('content-type', 'application/json'), ('transfer-encoding', 'chunked'), ('connection', 'keep-alive'), ('access-control-expose-headers', 'X-Request-ID'), ('openai-organization', 'user-9rymi7trhkh9wx0cjpzb4txg'), ('openai-processing-ms', '648'), ('openai-project', 'proj_xZDNucsxSbdjkba6PitMv58d'), ('openai-version', '2020-10-01'), ('x-envoy-upstream-service-time', '658'), ('x-ratelimit-limit-requests', '5000'), ('x-ratelimit-limit-tokens', '2000000'), ('x-ratelimit-remaining-requests', '4999'), ('x-ratelimit-remaining-tokens', '1999292'), ('x-ratelimit-reset-requests', '12ms'), ('x-ratelimit-reset-tokens', '21ms'), ('x-request-id', 'req_5fde3e8a8efd4854949e487cb45ccc97'), ('cf-cache-status', 'DYNAMIC'), ('set-cookie', '__cf_bm=yhwcx1hr8tTTzdjZSF741V0D0ccWcnV4oY2k7ypKT0E-1757187832-1.0.1.1-Yh7fOoRBxkS6QQ4MBF58v.MbH1on6VM_Bd77vP_VRd0UJqNEXJnHFU.6_FRwBEkMoTEZZ6ZCJQ4PwlZXMPlD83HCU9wFiiCr5e.d1EK158E; path=/; expires=Sat, 06-Sep-25 20:13:52 GMT; domain=.api.openai.com; HttpOnly; Secure; SameSite=None'), ('strict-transport-security', 'max-age=31536000; includeSubDomains; preload'), ('x-content-type-options', 'nosniff'), ('set-cookie', '_cfuvid=blhyxxpVno0NTpYFYGJjQlyutYE3XMhy_Ovr2fry0TM-1757187832815-0.0.1.1-604800000; path=/; domain=.api.openai.com; HttpOnly; Secure; SameSite=None'), ('server', 'cloudflare'), ('cf-ray', '97b0752deeecb92a-AMS'), ('content-encoding', 'gzip'), ('alt-svc', 'h3=":443"; ma=86400')])
2025-09-06 21:43:49 - openai._base_client - [DEBUG] - request_id: req_5fde3e8a8efd4854949e487cb45ccc97
2025-09-06 21:43:49 - janus_backend - [INFO] - 
--- USAGE TRACKING ---
Model: gpt-4o-mini
Input Tokens: 1234
Output Tokens: 24
Image Quality: N/A
Image Size: N/A
Total Cost: 0.00019950  
----------------------
2025-09-06 21:43:49 - janus_backend - [INFO] - Attempting to extract and save facts for chat 1 from text: 'User: hallo
Assistant: Hallo! Wie kann ich Ihnen heute helfen? Wenn Sie Fragen oder Anliegen haben, lassen Sie es mich bitte wissen!'
2025-09-06 21:43:50 - openai._base_client - [DEBUG] - Request options: {'method': 'post', 'url': '/chat/completions', 'files': None, 'idempotency_key': 'stainless-python-retry-0c427982-ebac-4360-918f-6c53d1feb905', 'json_data': {'messages': [{'role': 'system', 'content': "Du bist ein ultra-pr ziser Daten-Logger. Deine einzige Aufgabe ist es, Fakten aus der **letzten  u erung des 'user'** in einem Dialog zu extrahieren. **IGNORIERE ALLES, WAS DER 'assistant' SAGT.**\n**REGELN:**\n1.  Extrahiere jeden einzelnen Fakt auf einer **NEUEN ZEILE**. \n2.  Formuliere die Fakten als knappe, neutrale Aussagen in der dritten Person (z.B. 'Der Benutzer hei t Klaus', 'Die Tante des Benutzers mag Fisch').\n3.  Wenn der **'user'** in seiner letzten Nachricht keine neuen, konkreten Fakten nennt, antworte NUR mit dem Wort 'Keine'.\n\n--- BEISPIEL ---\nuser: Ich hei e Anna, mein Hund Bello mag Knochen und meine Katze Minka ist schwarz.\n--- EXTRAHIERTE FAKTEN ---\nDer Benutzer hei t Anna.\nDer Hund des Benutzers hei t Bello.\nBello mag Knochen.\nDie Katze des Benutzers hei t Minka.\nMinka ist schwarz.\n\n--- DIALOG ---\n\n\n--- EXTRAHIERTE FAKTEN ---"}, {'role': 'user', 'content': 'User: hallo\nAssistant: Hallo! Wie kann ich Ihnen heute helfen? Wenn Sie Fragen oder Anliegen haben, lassen Sie es mich bitte wissen!'}], 'model': 'gpt-4o-mini'}}
2025-09-06 21:43:50 - openai._base_client - [DEBUG] - Sending HTTP Request: POST https://api.openai.com/v1/chat/completions
INFO:     127.0.0.1:63717 - "POST /api/chat HTTP/1.1" 200 OK
2025-09-06 21:43:50 - httpcore.connection - [DEBUG] - connect_tcp.started host='api.openai.com' port=443 local_address=None timeout=5.0 socket_options=None
INFO:     127.0.0.1:63717 - "GET /api/costs/dashboard HTTP/1.1" 200 OK
2025-09-06 21:43:50 - httpcore.connection - [DEBUG] - connect_tcp.complete return_value=<httpcore._backends.anyio.AnyIOStream object at 0x000001B545BF1610>
2025-09-06 21:43:50 - httpcore.connection - [DEBUG] - start_tls.started ssl_context=<ssl.SSLContext object at 0x000001B5460474A0> server_hostname='api.openai.com' timeout=5.0
2025-09-06 21:43:50 - httpcore.connection - [DEBUG] - start_tls.complete return_value=<httpcore._backends.anyio.AnyIOStream object at 0x000001B5443E4FD0>
2025-09-06 21:43:50 - httpcore.http11 - [DEBUG] - send_request_headers.started request=<Request [b'POST']>
2025-09-06 21:43:50 - httpcore.http11 - [DEBUG] - send_request_headers.complete
2025-09-06 21:43:50 - httpcore.http11 - [DEBUG] - send_request_body.started request=<Request [b'POST']>
2025-09-06 21:43:50 - httpcore.http11 - [DEBUG] - send_request_body.complete
2025-09-06 21:43:50 - httpcore.http11 - [DEBUG] - receive_response_headers.started request=<Request [b'POST']>
2025-09-06 21:43:51 - httpcore.http11 - [DEBUG] - receive_response_headers.complete return_value=(b'HTTP/1.1', 200, b'OK', [(b'Date', b'Sat, 06 Sep 2025 19:43:53 GMT'), (b'Content-Type', b'application/json'), (b'Transfer-Encoding', b'chunked'), (b'Connection', b'keep-alive'), (b'access-control-expose-headers', b'X-Request-ID'), (b'openai-organization', b'user-9rymi7trhkh9wx0cjpzb4txg'), (b'openai-processing-ms', b'265'), (b'openai-project', b'proj_xZDNucsxSbdjkba6PitMv58d'), (b'openai-version', b'2020-10-01'), (b'x-envoy-upstream-service-time', b'530'), (b'x-ratelimit-limit-requests', b'5000'), (b'x-ratelimit-limit-tokens', b'2000000'), (b'x-ratelimit-remaining-requests', b'4999'), (b'x-ratelimit-remaining-tokens', b'1999746'), (b'x-ratelimit-reset-requests', b'12ms'), (b'x-ratelimit-reset-tokens', b'7ms'), (b'x-request-id', b'req_995d461eccca47b8a892bfb048c9d7ef'), (b'cf-cache-status', b'DYNAMIC'), (b'Set-Cookie', b'__cf_bm=8DYJ0iZeuxHhxR0CIq7saizac.eIV8o1Vm8tFF8cQmA-1757187833-1.0.1.1-miJuahVAplZMg4cfb6UrEsXO63fkzQa.pV9Ew015kVXBrq_Hg5Ov358Wu.npFjv.AiC6eyZkSidv0WQ_DDSCaqBw08KTzSDwcvThA_me_LY; path=/; expires=Sat, 06-Sep-25 20:13:53 GMT; domain=.api.openai.com; HttpOnly; Secure; SameSite=None'), (b'Strict-Transport-Security', b'max-age=31536000; includeSubDomains; preload'), (b'X-Content-Type-Options', b'nosniff'), (b'Set-Cookie', b'_cfuvid=zP2.c_WP.FGd4YGVDC1Us_l3N6_SLRTjoSKLS2O9G1I-1757187833843-0.0.1.1-604800000; path=/; domain=.api.openai.com; HttpOnly; Secure; SameSite=None'), (b'Server', b'cloudflare'), (b'CF-RAY', b'97b075350a65661a-AMS'), (b'Content-Encoding', b'gzip'), (b'alt-svc', b'h3=":443"; ma=86400')])
2025-09-06 21:43:51 - httpx - [INFO] - HTTP Request: POST https://api.openai.com/v1/chat/completions "HTTP/1.1 200 OK"
2025-09-06 21:43:51 - httpcore.http11 - [DEBUG] - receive_response_body.started request=<Request [b'POST']>
2025-09-06 21:43:51 - httpcore.http11 - [DEBUG] - receive_response_body.complete
2025-09-06 21:43:51 - httpcore.http11 - [DEBUG] - response_closed.started
2025-09-06 21:43:51 - httpcore.http11 - [DEBUG] - response_closed.complete
2025-09-06 21:43:51 - openai._base_client - [DEBUG] - HTTP Response: POST https://api.openai.com/v1/chat/completions "200 OK" Headers([('date', 'Sat, 06 Sep 2025 19:43:53 GMT'), ('content-type', 'application/json'), ('transfer-encoding', 'chunked'), ('connection', 'keep-alive'), ('access-control-expose-headers', 'X-Request-ID'), ('openai-organization', 'user-9rymi7trhkh9wx0cjpzb4txg'), ('openai-processing-ms', '265'), ('openai-project', 'proj_xZDNucsxSbdjkba6PitMv58d'), ('openai-version', '2020-10-01'), ('x-envoy-upstream-service-time', '530'), ('x-ratelimit-limit-requests', '5000'), ('x-ratelimit-limit-tokens', '2000000'), ('x-ratelimit-remaining-requests', '4999'), ('x-ratelimit-remaining-tokens', '1999746'), ('x-ratelimit-reset-requests', '12ms'), ('x-ratelimit-reset-tokens', '7ms'), ('x-request-id', 'req_995d461eccca47b8a892bfb048c9d7ef'), ('cf-cache-status', 'DYNAMIC'), ('set-cookie', '__cf_bm=8DYJ0iZeuxHhxR0CIq7saizac.eIV8o1Vm8tFF8cQmA-1757187833-1.0.1.1-miJuahVAplZMg4cfb6UrEsXO63fkzQa.pV9Ew015kVXBrq_Hg5Ov358Wu.npFjv.AiC6eyZkSidv0WQ_DDSCaqBw08KTzSDwcvThA_me_LY; path=/; expires=Sat, 06-Sep-25 20:13:53 GMT; domain=.api.openai.com; HttpOnly; Secure; SameSite=None'), ('strict-transport-security', 'max-age=31536000; includeSubDomains; preload'), ('x-content-type-options', 'nosniff'), ('set-cookie', '_cfuvid=zP2.c_WP.FGd4YGVDC1Us_l3N6_SLRTjoSKLS2O9G1I-1757187833843-0.0.1.1-604800000; path=/; domain=.api.openai.com; HttpOnly; Secure; SameSite=None'), ('server', 'cloudflare'), ('cf-ray', '97b075350a65661a-AMS'), ('content-encoding', 'gzip'), ('alt-svc', 'h3=":443"; ma=86400')])
2025-09-06 21:43:51 - openai._base_client - [DEBUG] - request_id: req_995d461eccca47b8a892bfb048c9d7ef
2025-09-06 21:43:51 - janus_backend - [INFO] - 
--- USAGE TRACKING ---
Model: gpt-4o-mini
Input Tokens: 283
Output Tokens: 2
Image Quality: N/A
Image Size: N/A
Total Cost: 0.00004365  
----------------------
2025-09-06 21:43:51 - janus_backend - [INFO] - Extracted text: 'Keine.'
2025-09-06 21:43:51 - janus_backend - [INFO] - Snippet: 'Keine.')
2025-09-06 21:43:51 - janus_backend - [INFO] - find_similar_snippets: Returning 1 similar memories.
2025-09-06 21:43:51 - janus_backend - [INFO] - Bekannter Fakt ignoriert (Duplikat): 'Keine.'.
INFO:     127.0.0.1:63717 - "GET /api/costs/summary-by-model HTTP/1.1" 200 OK
INFO:     127.0.0.1:63756 - "GET /api/costs/dashboard HTTP/1.1" 200 OK
2025-09-06 21:44:00 - janus_backend - [INFO] - Attempting to retrieve API keys.
2025-09-06 21:44:00 - janus_backend - [INFO] - Successfully retrieved API key for provider: openai
2025-09-06 21:44:00 - janus_backend - [INFO] - Successfully retrieved API key for provider: gemini
2025-09-06 21:44:00 - janus_backend - [INFO] - No API key found for provider: anthropic
2025-09-06 21:44:00 - janus_backend - [INFO] - No API key found for provider: cohere
INFO:     127.0.0.1:63793 - "GET /api/keys HTTP/1.1" 200 OK
2025-09-06 21:44:00 - janus_backend - [INFO] - Attempting to retrieve API keys.
2025-09-06 21:44:00 - janus_backend - [INFO] - Successfully retrieved API key for provider: openai
2025-09-06 21:44:00 - janus_backend - [INFO] - Successfully retrieved API key for provider: gemini
2025-09-06 21:44:00 - janus_backend - [INFO] - No API key found for provider: anthropic
2025-09-06 21:44:00 - janus_backend - [INFO] - No API key found for provider: cohere
INFO:     127.0.0.1:63793 - "GET /api/keys HTTP/1.1" 200 OK
INFO:     127.0.0.1:63793 - "GET /api/models/selection/gemini HTTP/1.1" 200 OK
INFO:     127.0.0.1:63793 - "POST /api/models/selection HTTP/1.1" 200 OK
2025-09-06 21:44:03 - janus_backend - [INFO] - Attempting to retrieve API keys.
2025-09-06 21:44:03 - janus_backend - [INFO] - Successfully retrieved API key for provider: openai
2025-09-06 21:44:03 - janus_backend - [INFO] - Successfully retrieved API key for provider: gemini
2025-09-06 21:44:03 - janus_backend - [INFO] - No API key found for provider: anthropic
2025-09-06 21:44:03 - janus_backend - [INFO] - No API key found for provider: cohere
INFO:     127.0.0.1:63793 - "GET /api/keys HTTP/1.1" 200 OK
2025-09-06 21:44:03 - janus_backend - [INFO] - Attempting to retrieve API keys.
2025-09-06 21:44:03 - janus_backend - [INFO] - Successfully retrieved API key for provider: openai
2025-09-06 21:44:03 - janus_backend - [INFO] - Successfully retrieved API key for provider: gemini
2025-09-06 21:44:03 - janus_backend - [INFO] - No API key found for provider: anthropic
2025-09-06 21:44:03 - janus_backend - [INFO] - No API key found for provider: cohere
INFO:     127.0.0.1:63793 - "GET /api/keys HTTP/1.1" 200 OK
2025-09-06 21:44:03 - httpcore.connection - [DEBUG] - close.started
2025-09-06 21:44:03 - httpcore.connection - [DEBUG] - close.complete
2025-09-06 21:44:09 - janus_backend - [INFO] - Snippet: 'Keine.')
2025-09-06 21:44:09 - janus_backend - [INFO] - Snippet: 'Die Anfrage an die API ist nach mehreren Versuchen fehlgeschlagen.')
2025-09-06 21:44:09 - janus_backend - [INFO] - find_similar_snippets: Returning 2 similar memories.
2025-09-06 21:44:09 - janus_backend - [INFO] - reason_and_respond: Original user_prompt=hi
2025-09-06 21:44:09 - grpc._cython.cygrpc - [DEBUG] - Using AsyncIOEngine.POLLER as I/O engine
2025-09-06 21:44:09 - janus_backend - [WARNING] - An error occurred with Gemini API, retrying... Error: 400 API key expired. Please renew the API key. [reason: "API_KEY_INVALID"
domain: "googleapis.com"
metadata {
  key: "service"
  value: "generativelanguage.googleapis.com"
}
, locale: "en-US"
message: "API key expired. Please renew the API key."
]
2025-09-06 21:44:11 - janus_backend - [WARNING] - An error occurred with Gemini API, retrying... Error: 400 API key expired. Please renew the API key. [reason: "API_KEY_INVALID"
domain: "googleapis.com"
metadata {
  key: "service"
  value: "generativelanguage.googleapis.com"
}
, locale: "en-US"
message: "API key expired. Please renew the API key."
]
2025-09-06 21:44:13 - janus_backend - [WARNING] - An error occurred with Gemini API, retrying... Error: 400 API key expired. Please renew the API key. [reason: "API_KEY_INVALID"
domain: "googleapis.com"
metadata {
  key: "service"
  value: "generativelanguage.googleapis.com"
}
, locale: "en-US"
message: "API key expired. Please renew the API key."
]
2025-09-06 21:44:13 - janus_backend - [ERROR] - API call failed after multiple retries: RetryError[<Future at 0x1b54632ead0 state=finished raised InvalidArgument>]
2025-09-06 21:44:13 - janus_backend - [INFO] - Attempting to extract and save facts for chat 1 from text: 'User: hi
Assistant: Die Anfrage an die API ist nach mehreren Versuchen fehlgeschlagen.'
INFO:     127.0.0.1:63950 - "POST /api/chat HTTP/1.1" 200 OK
INFO:     127.0.0.1:63950 - "GET /api/costs/dashboard HTTP/1.1" 200 OK
2025-09-06 21:44:13 - janus_backend - [WARNING] - An error occurred with Gemini API, retrying... Error: 400 API key expired. Please renew the API key. [reason: "API_KEY_INVALID"
domain: "googleapis.com"
metadata {
  key: "service"
  value: "generativelanguage.googleapis.com"
}
, locale: "en-US"
message: "API key expired. Please renew the API key."
]
2025-09-06 21:44:15 - janus_backend - [WARNING] - An error occurred with Gemini API, retrying... Error: 400 API key expired. Please renew the API key. [reason: "API_KEY_INVALID"
domain: "googleapis.com"
metadata {
  key: "service"
  value: "generativelanguage.googleapis.com"
}
, locale: "en-US"
message: "API key expired. Please renew the API key."
]
2025-09-06 21:44:17 - janus_backend - [WARNING] - An error occurred with Gemini API, retrying... Error: 400 API key expired. Please renew the API key. [reason: "API_KEY_INVALID"
domain: "googleapis.com"
metadata {
  key: "service"
  value: "generativelanguage.googleapis.com"
}
, locale: "en-US"
message: "API key expired. Please renew the API key."
]
2025-09-06 21:44:17 - janus_backend - [ERROR] - API call failed after multiple retries: RetryError[<Future at 0x1b545c08610 state=finished raised InvalidArgument>]
2025-09-06 21:44:17 - janus_backend - [INFO] - Extracted text: 'Die Anfrage an die API ist nach mehreren Versuchen fehlgeschlagen.'
2025-09-06 21:44:17 - janus_backend - [INFO] - Snippet: 'Die Anfrage an die API ist nach mehreren Versuchen fehlgeschlagen.')
2025-09-06 21:44:17 - janus_backend - [INFO] - find_similar_snippets: Returning 1 similar memories.
2025-09-06 21:44:18 - janus_backend - [INFO] - Bekannter Fakt ignoriert (Duplikat): 'Die Anfrage an die API ist nach mehreren Versuchen fehlgeschlagen.'.