2025-09-17 18:55:56 - janus_backend - [INFO] - Using persona prompt for 'ai_assistant'
[start-backend] 2025-09-17 18:55:56 - janus_backend - [INFO] - [DEBUG] FINAL HYBRID Memory Context Generated (length: 0):
[start-backend] 2025-09-17 18:55:56 - janus_backend - [INFO] - Touched 0 memory snippets to update their relevance.
[start-backend] 2025-09-17 18:55:56 - grpc._cython.cygrpc - [DEBUG] - Using AsyncIOEngine.POLLER as I/O engine
[start-backend] 2025-09-17 18:55:58 - janus_backend - [INFO] - Gemini requested tool call: perform_websearch with args: {'query': 'Nintendo Switch 2 price'}
[start-backend] 2025-09-17 18:55:58 - janus_backend - [INFO] -
[start-backend] --- USAGE TRACKING ---
[start-backend] Model: gemini-2.5-flash
[start-backend] Input Tokens: 0
[start-backend] Output Tokens: 0
[start-backend] Image Quality: N/A
[start-backend] Image Size: N/A
[start-backend] Total Cost: 0.00000000 �
[start-backend] ----------------------
[start-backend] 2025-09-17 18:55:58 - janus_backend - [INFO] - Gemini requested Google Search with query: Nintendo Switch 2 price
[start-backend] 2025-09-17 18:55:58 - janus_backend - [INFO] - Web search requested for Gemini. Using direct REST API call.
[start-backend] 2025-09-17 18:55:59 - httpcore.connection - [DEBUG] - connect_tcp.started host='generativelanguage.googleapis.com' port=443 local_address=None timeout=120.0 socket_options=None
[start-backend] 2025-09-17 18:55:59 - httpcore.connection - [DEBUG] - connect_tcp.complete return_value=<httpcore._backends.anyio.AnyIOStream object at 0x0000020C4F1B1490>
[start-backend] 2025-09-17 18:55:59 - httpcore.connection - [DEBUG] - start_tls.started ssl_context=<ssl.SSLContext object at 0x0000020C506D6840> server_hostname='generativelanguage.googleapis.com' timeout=120.0
[start-backend] 2025-09-17 18:55:59 - httpcore.connection - [DEBUG] - start_tls.complete return_value=<httpcore._backends.anyio.AnyIOStream object at 0x0000020C50762610>
[start-backend] 2025-09-17 18:55:59 - httpcore.http11 - [DEBUG] - send_request_headers.started request=<Request [b'POST']>
[start-backend] 2025-09-17 18:55:59 - httpcore.http11 - [DEBUG] - send_request_headers.complete
[start-backend] 2025-09-17 18:55:59 - httpcore.http11 - [DEBUG] - send_request_body.started request=<Request [b'POST']>
[start-backend] 2025-09-17 18:55:59 - httpcore.http11 - [DEBUG] - send_request_body.complete
[start-backend] 2025-09-17 18:55:59 - httpcore.http11 - [DEBUG] - receive_response_headers.started request=<Request [b'POST']>
[start-backend] 2025-09-17 18:55:59 - httpcore.http11 - [DEBUG] - receive_response_headers.complete return_value=(b'HTTP/1.1', 400, b'Bad Request', [(b'Vary', b'Origin'), (b'Vary', b'X-Origin'), (b'Vary', b'Referer'), (b'Content-Type', b'application/json; charset=UTF-8'), (b'Content-Encoding', b'gzip'), (b'Date', b'Wed, 17 Sep 2025 16:56:00 GMT'), (b'Server', b'scaffolding on HTTPServer2'), (b'X-XSS-Protection', b'0'), (b'X-Frame-Options', b'SAMEORIGIN'), (b'X-Content-Type-Options', b'nosniff'), (b'Server-Timing', b'gfet4t7; dur=53'), (b'Alt-Svc', b'h3=":443"; ma=2592000,h3-29=":443"; ma=2592000'), (b'Transfer-Encoding', b'chunked')])
[start-backend] 2025-09-17 18:55:59 - httpx - [INFO] - HTTP Request: POST https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key=AIzaSyCj0ruf57e_IdxpnpoSq_0AhbGtRJq7_PE "HTTP/1.1 400 Bad Request"
[start-backend] 2025-09-17 18:55:59 - httpcore.http11 - [DEBUG] - receive_response_body.started request=<Request [b'POST']>
[start-backend] 2025-09-17 18:55:59 - httpcore.http11 - [DEBUG] - receive_response_body.complete
[start-backend] 2025-09-17 18:55:59 - httpcore.http11 - [DEBUG] - response_closed.started
[start-backend] 2025-09-17 18:55:59 - httpcore.http11 - [DEBUG] - response_closed.complete
[start-backend] 2025-09-17 18:55:59 - httpcore.connection - [DEBUG] - close.started
[start-backend] 2025-09-17 18:55:59 - httpcore.connection - [DEBUG] - close.complete
[start-backend] 2025-09-17 18:55:59 - janus_backend - [ERROR] - HTTP Error during direct Gemini API call: {'error': {'code': 400, 'message': 'Please use a valid role: user, model.', 'status': 'INVALID_ARGUMENT'}}
[start-backend] Traceback (most recent call last):
[start-backend]   File "C:\KI\Janus-Projekt\backend\llm_providers\capabilities\gemini_web_search.py", line 135, in search_and_generate
[start-backend]     response.raise_for_status()
[start-backend]   File "C:\KI\Janus-Projekt\backend\venv\Lib\site-packages\httpx\_models.py", line 829, in raise_for_status
[start-backend]     raise HTTPStatusError(message, request=request, response=self)
[start-backend] httpx.HTTPStatusError: Client error '400 Bad Request' for url 'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key=AIzaSyCj0ruf57e_IdxpnpoSq_0AhbGtRJq7_PE'
[start-backend] For more information check: https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/400
[start-backend] 2025-09-17 18:55:59 - grpc._cython.cygrpc - [DEBUG] - Using AsyncIOEngine.POLLER as I/O engine
[start-backend] 2025-09-17 18:56:02 - janus_backend - [ERROR] - An unexpected error occurred with Gemini SDK: Could not convert `part.function_call` to text.
[start-backend] Traceback (most recent call last):
[start-backend]   File "C:\KI\Janus-Projekt\backend\llm_providers\gemini_service.py", line 171, in generate_response
[start-backend]     text_response = response.text
[start-backend]                     ^^^^^^^^^^^^^
[start-backend]   File "C:\KI\Janus-Projekt\backend\venv\Lib\site-packages\google\generativeai\types\generation_types.py", line 536, in text
[start-backend]     raise ValueError(f"Could not convert `part.{part_type}` to text.")
[start-backend] ValueError: Could not convert `part.function_call` to text.
[start-backend] 2025-09-17 18:56:02 - janus_backend - [INFO] - Final answer before check: 'Ein unerwarteter Fehler ist aufgetreten: Could not convert `part.function_call` to text.'
[start-backend] 2025-09-17 18:56:02 - janus_backend - [INFO] - [FACT EXTRACTION] Starte Extraktion f�r Chat 1 mit Text: 'User: wievlie kostet aktuell die switch 2?
[start-backend] Assistant: Ein unerwarteter Fehler ist aufgetreten: Could not convert `part.function_call` to text.'
[start-backend] INFO:     127.0.0.1:58407 - "POST /api/chat HTTP/1.1" 200 OK
[start-backend] INFO:     127.0.0.1:58407 - "GET /api/costs/dashboard HTTP/1.1" 200 OK
[start-backend] 2025-09-17 18:56:06 - janus_backend - [INFO] -
[start-backend] --- USAGE TRACKING ---
[start-backend] Model: gemini-2.5-flash
[start-backend] Input Tokens: 0
[start-backend] Output Tokens: 0
[start-backend] Image Quality: N/A
[start-backend] Image Size: N/A
[start-backend] Total Cost: 0.00000000 �
[start-backend] ----------------------
[start-backend] 2025-09-17 18:56:06 - janus_backend - [INFO] - Extracted text: 'Keine.'
[start-backend] 2025-09-17 18:56:06 - janus_backend - [INFO] - Kein relevanter Fakt im Textblock gefunden.
[start-backend] 2025-09-17 18:56:21 - janus_backend - [INFO] - Explizite Werkzeug-Direktive wurde auf den System-Prompt angewendet.
[start-backend] 2025-09-17 18:56:21 - janus_backend - [INFO] - Using persona prompt for 'ai_assistant'
[start-backend] 2025-09-17 18:56:21 - janus_backend - [INFO] - [DEBUG] FINAL HYBRID Memory Context Generated (length: 0):
[start-backend] 2025-09-17 18:56:21 - janus_backend - [INFO] - Touched 0 memory snippets to update their relevance.
[start-backend] 2025-09-17 18:56:23 - janus_backend - [INFO] - Gemini requested tool call: perform_websearch with args: {'query': 'Preis Nintendo Switch 2'}
[start-backend] 2025-09-17 18:56:23 - janus_backend - [INFO] -
[start-backend] --- USAGE TRACKING ---
[start-backend] Model: gemini-2.5-flash
[start-backend] Input Tokens: 0
[start-backend] Output Tokens: 0
[start-backend] Image Quality: N/A
[start-backend] Image Size: N/A
[start-backend] Total Cost: 0.00000000 �
[start-backend] ----------------------
[start-backend] 2025-09-17 18:56:23 - janus_backend - [INFO] - Gemini requested Google Search with query: Preis Nintendo Switch 2
[start-backend] 2025-09-17 18:56:23 - janus_backend - [INFO] - Web search requested for Gemini. Using direct REST API call.
[start-backend] 2025-09-17 18:56:23 - httpcore.connection - [DEBUG] - connect_tcp.started host='generativelanguage.googleapis.com' port=443 local_address=None timeout=120.0 socket_options=None
[start-backend] 2025-09-17 18:56:23 - httpcore.connection - [DEBUG] - connect_tcp.complete return_value=<httpcore._backends.anyio.AnyIOStream object at 0x0000020C219E2690>
[start-backend] 2025-09-17 18:56:23 - httpcore.connection - [DEBUG] - start_tls.started ssl_context=<ssl.SSLContext object at 0x0000020C506D6B10> server_hostname='generativelanguage.googleapis.com' timeout=120.0
[start-backend] 2025-09-17 18:56:23 - httpcore.connection - [DEBUG] - start_tls.complete return_value=<httpcore._backends.anyio.AnyIOStream object at 0x0000020C507D4C50>
[start-backend] 2025-09-17 18:56:23 - httpcore.http11 - [DEBUG] - send_request_headers.started request=<Request [b'POST']>
[start-backend] 2025-09-17 18:56:23 - httpcore.http11 - [DEBUG] - send_request_headers.complete
[start-backend] 2025-09-17 18:56:23 - httpcore.http11 - [DEBUG] - send_request_body.started request=<Request [b'POST']>
[start-backend] 2025-09-17 18:56:23 - httpcore.http11 - [DEBUG] - send_request_body.complete
[start-backend] 2025-09-17 18:56:23 - httpcore.http11 - [DEBUG] - receive_response_headers.started request=<Request [b'POST']>
[start-backend] 2025-09-17 18:56:23 - httpcore.http11 - [DEBUG] - receive_response_headers.complete return_value=(b'HTTP/1.1', 400, b'Bad Request', [(b'Vary', b'Origin'), (b'Vary', b'X-Origin'), (b'Vary', b'Referer'), (b'Content-Type', b'application/json; charset=UTF-8'), (b'Content-Encoding', b'gzip'), (b'Date', b'Wed, 17 Sep 2025 16:56:24 GMT'), (b'Server', b'scaffolding on HTTPServer2'), (b'X-XSS-Protection', b'0'), (b'X-Frame-Options', b'SAMEORIGIN'), (b'X-Content-Type-Options', b'nosniff'), (b'Server-Timing', b'gfet4t7; dur=50'), (b'Alt-Svc', b'h3=":443"; ma=2592000,h3-29=":443"; ma=2592000'), (b'Transfer-Encoding', b'chunked')])
[start-backend] 2025-09-17 18:56:23 - httpx - [INFO] - HTTP Request: POST https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key=AIzaSyCj0ruf57e_IdxpnpoSq_0AhbGtRJq7_PE "HTTP/1.1 400 Bad Request"
[start-backend] 2025-09-17 18:56:23 - httpcore.http11 - [DEBUG] - receive_response_body.started request=<Request [b'POST']>
[start-backend] 2025-09-17 18:56:23 - httpcore.http11 - [DEBUG] - receive_response_body.complete
[start-backend] 2025-09-17 18:56:23 - httpcore.http11 - [DEBUG] - response_closed.started
[start-backend] 2025-09-17 18:56:23 - httpcore.http11 - [DEBUG] - response_closed.complete
[start-backend] 2025-09-17 18:56:23 - httpcore.connection - [DEBUG] - close.started
[start-backend] 2025-09-17 18:56:23 - httpcore.connection - [DEBUG] - close.complete
[start-backend] 2025-09-17 18:56:23 - janus_backend - [ERROR] - HTTP Error during direct Gemini API call: {'error': {'code': 400, 'message': 'Please use a valid role: user, model.', 'status': 'INVALID_ARGUMENT'}}
[start-backend] Traceback (most recent call last):
[start-backend]   File "C:\KI\Janus-Projekt\backend\llm_providers\capabilities\gemini_web_search.py", line 135, in search_and_generate
[start-backend]     response.raise_for_status()
[start-backend]   File "C:\KI\Janus-Projekt\backend\venv\Lib\site-packages\httpx\_models.py", line 829, in raise_for_status
[start-backend]     raise HTTPStatusError(message, request=request, response=self)
[start-backend] httpx.HTTPStatusError: Client error '400 Bad Request' for url 'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key=AIzaSyCj0ruf57e_IdxpnpoSq_0AhbGtRJq7_PE'
[start-backend] For more information check: https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/400
[start-backend] 2025-09-17 18:56:24 - janus_backend - [INFO] -
[start-backend] --- USAGE TRACKING ---
[start-backend] Model: gemini-2.5-flash
[start-backend] Input Tokens: 0
[start-backend] Output Tokens: 0
[start-backend] Image Quality: N/A
[start-backend] Image Size: N/A
[start-backend] Total Cost: 0.00000000 �
[start-backend] ----------------------
[start-backend] 2025-09-17 18:56:24 - janus_backend - [INFO] - Final answer before check: '
[start-backend] '
[start-backend] 2025-09-17 18:56:24 - janus_backend - [INFO] - [FACT EXTRACTION] Starte Extraktion f�r Chat 1 mit Text: 'User: wieviel kostet aktuell die switch 2?
[start-backend] Assistant:
[start-backend] '
[start-backend] INFO:     127.0.0.1:58470 - "POST /api/chat HTTP/1.1" 200 OK
[start-backend] INFO:     127.0.0.1:58470 - "GET /api/costs/dashboard HTTP/1.1" 200 OK
[start-backend] 2025-09-17 18:56:27 - janus_backend - [INFO] -
[start-backend] --- USAGE TRACKING ---
[start-backend] Model: gemini-2.5-flash
[start-backend] Input Tokens: 0
[start-backend] Output Tokens: 0
[start-backend] Image Quality: N/A
[start-backend] Image Size: N/A
[start-backend] Total Cost: 0.00000000 �
[start-backend] ----------------------
[start-backend] 2025-09-17 18:56:27 - janus_backend - [INFO] - Extracted text: 'Keine.'
[start-backend] 2025-09-17 18:56:27 - janus_backend - [INFO] - Kein relevanter Fakt im Textblock gefunden.