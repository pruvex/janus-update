
Running 6 tests using 4 workers

  ✓  4 [chromium] › tests\functional\chat-core.spec.js:6:3 › Kern-Funktionalität des Chats › sollte einen neuen Chat starten und eine Antwort vom Modell erhalten (988ms)
  ✓  5 [webkit] › tests\functional\chat-core.spec.js:6:3 › Kern-Funktionalität des Chats › sollte einen neuen Chat starten und eine Antwort vom Modell erhalten (1.5s)
---------------------------------------------------
--- HIER IST DER HTML CODE DER CHAT ANSICHT ---

        <div id="main-content">
          <div id="chat-window-host">
            <div id="chat-window" class="chat-window">
              <div id="chat-header">hi</div>
              <div id="chat-messages"><div class="message user"><div class="bubble"><p><p>hi</p>
</p></div><div class="timestamp">18:22</div></div><div class="message assistant"><div class="bubble"><p><p>Hi! Wobei kann ich dir heute helfen?</p>
</p></div><div class="timestamp">18:22</div></div></div>
              <div id="chat-input-container">
                <form id="chat-form">
                  <input type="file" id="image-upload-input" style="display: none" accept="image/*">
                  <button type="button" id="image-upload-btn">📎</button>
                  <input type="text" id="chat-input" placeholder="Nachricht an Janus senden...">
                  <button type="button" id="mic-btn">🎤</button>
                  <button type="button" id="tts-toggle-btn" title="TTS aktivieren/deaktivieren">
                    🔊
                  </button>
                  <button id="send-button" type="submit">Senden</button>
                </form>
              </div>
            </div>
          </div>
        </div>
      
---------------------------------------------------
  ✓  1 [chromium] › tests\functional\debug-selector.spec.js:3:1 › Spionage-Test: HTML Struktur auslesen (6.1s)
  ✓  2 [firefox] › tests\functional\chat-core.spec.js:6:3 › Kern-Funktionalität des Chats › sollte einen neuen Chat starten und eine Antwort vom Modell erhalten (5.5s)
---------------------------------------------------
--- HIER IST DER HTML CODE DER CHAT ANSICHT ---

        <div id="main-content">
          <div id="chat-window-host">
            <div id="chat-window" class="chat-window">
              <div id="chat-header">Neuer Chat</div>
              <div id="chat-messages"></div>
              <div id="chat-input-container">
                <form id="chat-form">
                  <input type="file" id="image-upload-input" style="display: none" accept="image/*">
                  <button type="button" id="image-upload-btn">📎</button>
                  <input type="text" id="chat-input" placeholder="Nachricht an Janus senden...">
                  <button type="button" id="mic-btn">🎤</button>
                  <button type="button" id="tts-toggle-btn" title="TTS aktivieren/deaktivieren">
                    🔊
                  </button>
                  <button id="send-button" type="submit">Senden</button>
                </form>
              </div>
            </div>
          </div>
        </div>
      
---------------------------------------------------
  ✓  3 [firefox] › tests\functional\debug-selector.spec.js:3:1 › Spionage-Test: HTML Struktur auslesen (9.8s)
---------------------------------------------------
--- HIER IST DER HTML CODE DER CHAT ANSICHT ---

        <div id="main-content">
          <div id="chat-window-host">
            <div id="chat-window" class="chat-window">
              <div id="chat-header">Neuer Chat</div>
              <div id="chat-messages"><div class="message user"><div class="bubble"><p><p>hi</p>
</p></div><div class="timestamp">18:22</div></div><div class="message assistant"><div class="bubble"><p><p>Hi! Wobei kann ich dir helfen – Planung, schnelle Recherche, Text formulieren oder etwas Organisatorisches (Termine, Route, Wetter)?</p>
</p></div><div class="timestamp">18:22</div></div><div class="message user"><div class="bubble"><p><p>hi</p>
</p></div><div class="timestamp">18:22</div></div><div class="message assistant"><div class="bubble"><p><p>Hallo! Wie kann ich dir heute helfen? Möchtest du planen, etwas recherchieren, einen Text formulieren oder ein Organisatorisches erledigen (Termine, Route, Wetter)? Sag mir kurz, wobei ich dich unterstützen soll.</p>
</p></div><div class="timestamp">18:22</div></div><div class="message user"><div class="bubble"><p><p>hi</p>
</p></div><div class="timestamp">18:22</div></div><div class="message user"><div class="bubble"><p><p>Hallo Janus</p>
</p></div><div class="timestamp">18:22</div></div><div class="message assistant"><div class="bubble"><p><p>Hallo! Schön, dich zu hören. Womit soll ich dir heute helfen? Wähle eine der Optionen oder beschreibe dein Ziel kurz:</p>
<ul>
<li>Planung (Projekte, Aufgaben)</li>
<li>Recherche (Web, Fakten)</li>
<li>Textformulierung (Emails, Texte, Inhalte)</li>
<li>Organisatorisches (Termine, Route, Wetter)</li>
</ul>
<p>Sag mir einfach, was du brauchst.</p>
</p></div><div class="timestamp">18:22</div></div><div class="message user"><div class="bubble"><p><p>Hier ist die genaue Aufschlüsselung, was der aktuelle Testblock tests/functional/chat-core.spec.js Schritt für Schritt sicherstellt:Was wir in chat-core.spec.js aktuell abdecken:Erreichbarkeit der App:Startet die Anwendung überhaupt (page.goto('/'))?Lädt die Startseite fehlerfrei?Navigation / Reset:Funktioniert der "Neuer Chat" Button?Dies ist wichtig, um sicherzustellen, dass der State der Anwendung sauber zurückgesetzt werden kann.UI-Interaktion (Eingabe):Ist das Eingabefeld vorhanden und interagierbar?Können wir Text hineinschreiben?Sende-Logik (Hydration &amp; Events):Funktioniert das Absenden per ENTER-Taste?Hintergrund: Das testet, ob die JavaScript-Event-Listener korrekt an das HTML gebunden wurden (React "Hydration") und ob das Formular-Handling (onSubmit) greift.Feedback-Schleife (User-Sicht):Input-Reset: Wird das Eingabefeld nach dem Senden geleert? (Wichtiges visuelles Feedback für den User).Eigene Nachricht: Taucht "Hallo Janus" im Chat-Verlauf auf? (Testet, ob die lokale Liste der Nachrichten korrekt aktualisiert wird).Backend-Integration (Die "Intelligenz"):Antwort-Empfang: Erscheint eine Antwort-Blase (.message.assistant)?Inhalt: Ist in dieser Blase tatsächlich Text (oder zumindest ein Lade-Indikator, der nicht leer ist)?Bedeutung: Dieser Schritt bestätigt, dass die Kommunikation zwischen Frontend -&gt; Backend -&gt; LLM -&gt; Frontend einmal komplett durchlaufen ist. verstehst du worum es hier geht?</p>
</p></div><div class="timestamp">18:22</div></div><div class="message assistant"><div class="bubble"><p><p>Ja, ich verstehe genau, worum es hier geht.</p>
<p>Du beschreibst einen <strong>funktionalen End-to-End-Test (z.B. Playwright)</strong> für euren Chat, der nicht nur UI-Klicks prüft, sondern die <strong>komplette Kern-User-Journey</strong> validiert – inklusive der kritischen technischen Punkte:</p>
<ul>
<li><strong>Smoke-Test der App</strong>: <code>page.goto('/')</code> + Seite lädt ohne Fehler ⇒ Deployment/Server/Build grundsätzlich ok.</li>
<li><strong>State-Reset über „Neuer Chat“</strong>: Stellt sicher, dass man aus einem “dirty state” wieder in einen definierten Ausgangszustand kommt (wichtig für UX und Folgetests).</li>
<li><strong>Input ist benutzbar</strong>: Feld existiert, ist fokussierbar, Text kann eingegeben werden ⇒ grundlegende UI-Interaktion steht.</li>
<li><strong>Hydration/Event-Binding</strong>: ENTER triggert wirklich <code>onSubmit</code> ⇒ testet indirekt, dass React hydratisiert hat und Listener nicht fehlen (klassischer Fehler bei SSR/Hydration-Problemen).</li>
<li><strong>Unmittelbares User-Feedback</strong>:<ul>
<li>Input wird geleert ⇒ bestätigt, dass Submit-Flow im Frontend durchgelaufen ist.</li>
<li>Eigene Nachricht erscheint im Verlauf ⇒ lokale Message-Liste/State-Update funktioniert.</li>
</ul>
</li>
<li><strong>Backend + LLM Roundtrip</strong>:<ul>
<li>Assistant-Bubble erscheint ⇒ Response kommt zurück/Streaming startet.</li>
<li>Bubble enthält Text oder zumindest nicht-leeren Indikator ⇒ “Antwort-Pipeline lebt” (Frontend → Backend → LLM → Frontend).</li>
</ul>
</li>
</ul>
<p>Unterm Strich: Der Test stellt sicher, dass <strong>der Chat als Produktkern</strong> wirklich bedienbar ist und die <strong>wichtigste Integration</strong> (LLM-Antwort) mindestens einmal erfolgreich durchläuft.</p>
<p>Wenn du willst, kann ich dir auch sagen, <strong>welche typischen Flakes</strong> bei genau solchen Tests auftreten (Hydration-Timing, Streaming, Selektoren) und wie man sie stabilisiert.</p>
</p></div><div class="timestamp">18:22</div></div><div class="message user"><div class="bubble"><p><p>gäbe es zusätzliche tests die ir in diesem block ergänzen sollten damit die test industriestandard diamantstandard machen? oder siehst du anderes optimierungspotential?</p>
</p></div><div class="timestamp">18:22</div></div><div class="message assistant"><div class="bubble"><p><p>Ja – euer Block ist ein sehr guter „Happy-Path“-Kern. Für „Industrie-/Diamantstandard“ würde ich ihn in zwei Richtungen ergänzen: <strong>mehr Risikoflächen abdecken</strong> (Fehlerfälle, Accessibility, Streaming) und <strong>stabiler/diagnostischer</strong> machen (weniger Flakes, bessere Assertions).</p>
<h2>1) Zusätzliche Tests, die typischerweise als Standard gelten</h2>
<h3>A) Robustheit / Error-Paths (sehr wichtig)</h3>
<ol>
<li><p><strong>Backend nicht erreichbar / 5xx</strong></p>
<ul>
<li>Erwartung: UI zeigt eine klare Fehlermeldung („Antwort fehlgeschlagen, erneut versuchen“), kein endloses Laden.</li>
<li>Zusätzlich: Retry-Button funktioniert, und der Chat bleibt bedienbar.</li>
</ul>
</li>
<li><p><strong>Timeout / sehr langsame Antwort</strong></p>
<ul>
<li>Erwartung: Loading-Indikator bleibt sichtbar, ggf. Abbrechen möglich; nach Timeout verständliche Meldung.</li>
</ul>
</li>
<li><p><strong>Rate limit (429)</strong></p>
<ul>
<li>Erwartung: spezifische Meldung + ggf. Cooldown/Retry.</li>
</ul>
</li>
<li><p><strong>Netzwerk-Offline (browser offline)</strong></p>
<ul>
<li>Erwartung: Senden wird verhindert oder führt zu sauberem Fehlerzustand.</li>
</ul>
</li>
</ol>
<p>Warum: Happy Path ist gut – aber “Industrie-Standard” heißt: <strong>Fehler sind UX-stabil und nicht state-corrupting</strong>.</p>
<h3>B) Streaming-/Teilausgabe-Verhalten (wenn ihr streamt)</h3>
<ul>
<li>Teste, dass bei einer gestreamten Antwort:<ul>
<li>zuerst ein <strong>Loading/„typing“</strong> sichtbar ist,</li>
<li>dann <strong>Text inkrementell</strong> oder zumindest final erscheint,</li>
<li>am Ende ein „done“-Zustand erreicht wird (kein Loader bleibt hängen).</li>
</ul>
</li>
</ul>
<h3>C) Conversation State / Mehrfachnachrichten</h3>
<ol>
<li><strong>Zwei Nachrichten nacheinander senden</strong><ul>
<li>Erwartung: Reihenfolge stimmt, beide User-Messages sichtbar, zwei Assistant-Responses (oder eine je nach Logik).</li>
</ul>
</li>
<li><strong>„Neuer Chat“ löscht wirklich alles</strong><ul>
<li>Erwartung: Verlauf weg, Input leer, ggf. neue Conversation-ID (falls vorhanden).</li>
</ul>
</li>
</ol>
<h3>D) Input-Validierung &amp; UX-Details</h3>
<ul>
<li><strong>Leere Nachricht</strong> (nur Enter, nur Spaces) darf nicht senden.</li>
<li><strong>Sehr lange Nachricht</strong> (z.B. 10k chars): UI bleibt responsiv, ggf. Hinweis/Limit.</li>
<li><strong>Multiline</strong>: <code>Shift+Enter</code> erzeugt Zeilenumbruch, <code>Enter</code> sendet (falls so intended).</li>
</ul>
<h3>E) Accessibility / Semantik (oft Pflicht in reifen Teams)</h3>
<ul>
<li>Input hat korrektes Label/aria-label.</li>
<li>Buttons haben zugängliche Namen.</li>
<li>Chat-Nachrichten haben sinnvolle Rollen/Struktur (z.B. <code>role="log"</code> / <code>aria-live</code>), damit Screenreader neue Messages ansagen.</li>
<li>Fokus-Management: nach Senden bleibt Fokus im Input (typisch UX-Standard).</li>
</ul>
<h3>F) Security-/Content-Safety auf UI-Ebene</h3>
<ul>
<li><strong>XSS-Schutz</strong>: Wenn User <code>&lt;script&gt;alert(1)&lt;/script&gt;</code> sendet, darf das im Verlauf <strong>als Text</strong> erscheinen, nicht ausgeführt werden.</li>
<li><strong>Markdown/HTML Rendering</strong> (falls vorhanden): Links sicher (<code>rel="noopener noreferrer"</code>), keine raw HTML injection.</li>
</ul>
<h2>2) Optimierungspotential im bestehenden Testblock (Stabilität &amp; Aussagekraft)</h2>
<h3>A) Selektoren „hart“ machen (Flake-Reduktion)</h3>
<ul>
<li>Verwendet nach Möglichkeit <strong><code>data-testid</code></strong> oder <strong>ARIA-Rollen</strong> statt CSS-Klassen wie <code>.message.assistant</code>.</li>
<li>Beispiel: <code>getByTestId('message-assistant')</code> oder <code>getByRole('textbox', { name: /nachricht/i })</code>.</li>
</ul>
<h3>B) Assertions auf „fertigen Zustand“ statt „irgendwas ist da“</h3>
<p>Aktuell: “Assistant bubble existiert und hat Text oder Loader”. Besser:</p>
<ul>
<li><strong>Wenn ihr Streaming habt</strong>: erst Loader erscheint, dann <strong>final</strong> Text nicht leer <em>und</em> Loader verschwindet.</li>
<li>Wenn kein Streaming: warte auf Response-Completion Indikator (z.B. <code>data-status="done"</code>).</li>
</ul>
<h3>C) Network Mocking: zwei Testarten statt einer</h3>
<p>Für Diamantstandard ist die Kombination stark:</p>
<ol>
<li><strong>E2E „Real backend“ Smoke</strong> (so wie jetzt): prüft die echte Integration.</li>
<li><strong>Deterministischer UI-Test mit Mock</strong> (<code>page.route</code>):<ul>
<li>Antwort ist immer gleich ⇒ stabil, schnell, testet UI-Logik ohne Backend-Flakes.</li>
</ul>
</li>
</ol>
<p>Damit entkoppelt ihr „Backend down“ von „UI regressions“.</p>
<h3>D) Konsistente Waiting-Strategie</h3>
<ul>
<li>Vermeidet <code>waitForTimeout</code>.</li>
<li>Wartet gezielt auf:<ul>
<li>DOM-Zustand (Message count steigt)</li>
<li>Request/Response (wenn ihr die API-Route kennt)</li>
<li>Statusindikatoren (loading→done)</li>
</ul>
</li>
</ul>
<h3>E) Diagnostik bei Failures</h3>
<ul>
<li>Bei Fehler: Screenshot + HAR/trace + Konsole/Netzwerkfehler loggen (Playwright Trace Viewer ist Goldstandard).</li>
<li>Das spart massiv Zeit bei CI-Flakes.</li>
</ul>
<h2>3) Wenn du willst: Vorschlag für „Diamant“-Test-Suite-Struktur</h2>
<ul>
<li><strong>chat-core.spec.ts</strong>: 1–2 Happy-Path-Smokes (real backend)</li>
<li><strong>chat-ui.spec.ts</strong>: deterministisch gemockt: input/send/reset/render/streaming states</li>
<li><strong>chat-errors.spec.ts</strong>: 401/429/500/timeout/offline</li>
<li><strong>chat-a11y.spec.ts</strong>: Axe/ARIA smoke</li>
</ul>
<p>Wenn du mir sagst:</p>
<ol>
<li>nutzt ihr <strong>Streaming (SSE/Websocket)</strong> oder klassische Response?  </li>
<li>gibt es <strong>Conversation-IDs / Persistenz</strong> (localStorage, DB)?  </li>
<li>Playwright-Selektoren aktuell eher CSS oder testids?</li>
</ol>
<p>…dann kann ich dir sehr konkret 5–8 zusätzliche Tests priorisieren (mit Beispiel-Assertions), die am meisten „Qualität pro Minute“ bringen.</p>
</p></div><div class="timestamp">18:22</div></div><div class="message user"><div class="bubble"><p><p>Lass uns die Antworten auf deine Fragen strukturieren:Streaming (SSE/Websocket) vs. klassische Response:Aktuell nutzen wir eine klassische Request/Response-Architektur.Die Antwort wird in einem Stück zurückgegeben, wie in der Test-Implementierung zu sehen ist, wo wir auf die vollständige Antwort warten.Conversation-IDs / Persistenz:Ja, es gibt Conversation-IDs, wie in der Testdatei zu sehen, wo wir mit newChatButton einen neuen Chat starten.Die Persistenz wird über localStorage oder eine Datenbank realisiert, da der Chatverlauf zwischengespeichert wird.Playwright-Selektoren:Wir verwenden hauptsächlich CSS-Selektoren (z.B. .message.user, .message.assistant).Zusätzlich nutzen wir ARIA-Rollen und -Namen (z.B. getByRole('button', { name: /neuer chat/i })).Es gibt keine expliziten data-testid-Attribute in den Selektoren.</p>
</p></div><div class="timestamp">18:22</div></div><div class="message assistant"><div class="bubble"><p><p>Gut, damit kann man sehr gezielt „Diamantstandard“ draufsetzen. Bei <strong>klassischem Request/Response</strong> + <strong>Conversation-IDs/Persistenz</strong> + <strong>CSS/ARIA-Selektoren</strong> würde ich wie folgt priorisieren:</p>
<h2>1) Die 8 sinnvollsten Ergänzungen (priorisiert, hoher Nutzen)</h2>
<h3>1) Persistenz-Reload-Test (kritisch bei localStorage/DB)</h3>
<p><strong>Ziel:</strong> Chatverlauf überlebt einen Page-Reload (oder eben bewusst nicht – je nach Produktentscheidung).</p>
<ul>
<li>Sende Nachricht → Assistant antwortet.</li>
<li><code>page.reload()</code></li>
<li>Erwartung: Verlauf ist wieder da <strong>und</strong> Conversation-ID ist gleich (oder es gibt eine klare definierte Regel).</li>
</ul>
<p><strong>Warum Diamant:</strong> deckt reale Nutzer-Session ab, findet viele „state lost“-Bugs.</p>
<hr>
<h3>2) Neue Conversation-ID bei „Neuer Chat“</h3>
<p><strong>Ziel:</strong> „Neuer Chat“ erzeugt wirklich eine neue Konversation, nicht nur UI-Clear.</p>
<ul>
<li>Vorher: Conversation-ID aus UI/URL/localStorage auslesen (falls zugänglich).</li>
<li>„Neuer Chat“ klicken.</li>
<li>Erwartung: ID hat sich geändert <strong>und</strong> Verlauf ist leer.</li>
</ul>
<p><strong>Warum:</strong> verhindert stilles Vermischen von Threads (häufiger Prod-Bug).</p>
<hr>
<h3>3) Leere/Whitespace-Message wird nicht gesendet</h3>
<p><strong>Ziel:</strong> Input-Validierung + UX.</p>
<ul>
<li>Input: <code>"   "</code> oder leer</li>
<li>Enter</li>
<li>Erwartung: keine neue <code>.message.user</code>, kein Request (optional via route/spy), ggf. Button disabled.</li>
</ul>
<p><strong>Warum:</strong> verhindert Spam/Fehlerzustände im Backend.</p>
<hr>
<h3>4) Zwei Nachrichten hintereinander (Reihenfolge &amp; korrekte Zuordnung)</h3>
<p><strong>Ziel:</strong> Reihenfolge im UI, State-Updates, kein Überschreiben.</p>
<ul>
<li>Sende „A“, warte auf Assistant.</li>
<li>Sende „B“, warte auf Assistant.</li>
<li>Erwartung: 4 Messages in korrekter Reihenfolge (user A, assistant A, user B, assistant B).</li>
</ul>
<p><strong>Warum:</strong> deckt Race Conditions / „last message wins“ ab.</p>
<hr>
<h3>5) Fehlerfall 500/Netzwerkfehler (UI bleibt stabil)</h3>
<p><strong>Ziel:</strong> kontrollierter Error-State.</p>
<ul>
<li>Mocke die Chat-API einmalig auf 500.</li>
<li>Erwartung: sichtbare Fehlermeldung, kein endloser Loader, Input bleibt nutzbar, „erneut versuchen“ funktioniert (falls vorhanden).</li>
</ul>
<p><strong>Warum:</strong> Industrie-Standard = Fehler sind UX-stabil.</p>
<hr>
<h3>6) Timeout/Slow Backend (falls ihr timeouts habt)</h3>
<p><strong>Ziel:</strong> definierte UX bei langen Requests.</p>
<ul>
<li>API absichtlich verzögern (Playwright route mit delayed fulfill) oder Timeout simulieren.</li>
<li>Erwartung: Loading-Zustand sichtbar, dann Timeout-Meldung oder weiter warten gemäß Spezifikation.</li>
</ul>
<hr>
<h3>7) XSS/HTML-Injection im Chatverlauf (UI-Security)</h3>
<p><strong>Ziel:</strong> Nachricht wird als Text gerendert, nicht als HTML ausgeführt.</p>
<ul>
<li>Sende <code>&lt;img src=x onerror=alert(1)&gt;</code> oder <code>&lt;script&gt;…&lt;/script&gt;</code></li>
<li>Erwartung: erscheint escaped (Text), keine Dialoge/JS-Ausführung.</li>
</ul>
<p><strong>Warum:</strong> extrem wichtiger „Diamant“-Test, sehr günstig zu testen.</p>
<hr>
<h3>8) A11y-Smoke: Input/Buttons haben gute accessible names</h3>
<p><strong>Ziel:</strong> Mindeststandard für reife Apps.</p>
<ul>
<li><code>getByRole('textbox', { name: /nachricht|message/i })</code> muss funktionieren.</li>
<li>„Neuer Chat“ Button via Role/Name.</li>
<li>Optional: Chatlog hat sinnvolle Rolle (z.B. <code>role="log"</code>).</li>
</ul>
<p><strong>Warum:</strong> stabilere Selektoren + echte Accessibility.</p>
<hr>
<h2>2) Optimierungspotential bei Selektoren (ohne sofort data-testid einzuführen)</h2>
<p>Ihr macht schon etwas richtig (Role/Name). Für „Diamant“:</p>
<ul>
<li><strong>Bevorzuge <code>getByRole</code>/<code>getByLabel</code></strong> wo möglich (Input, Buttons).</li>
<li>Für Nachrichten: statt <code>.message.assistant</code> lieber:<ul>
<li>ein Container mit Rolle: <code>getByRole('log')</code> und darin <code>locator(...)</code></li>
<li>oder zumindest: <code>locator('[data-role="assistant-message"]')</code> (falls ihr mini-Attribute hinzufügen könnt, ohne „testid“-Policy zu brechen)</li>
</ul>
</li>
</ul>
<p>Wenn ihr minimal in die App eingreifen dürft, wäre <strong>ein einziges</strong> stabiles Attribut Gold wert:</p>
<ul>
<li>z.B. <code>data-message-role="assistant|user"</code> oder <code>data-testid="chat-message"</code> mit <code>data-author=...</code>.
Das reduziert CSS-Brüche durch Refactors massiv.</li>
</ul>
<hr>
<h2>3) Ein „Diamant“-Pattern: Real-Backend-Smoke + deterministische Mock-Tests</h2>
<p>Ich würde euren aktuellen Test als <strong>Smoke (real backend)</strong> behalten, aber ihn schlank halten.
Daneben 3–6 <strong>Mock-basierte</strong> Specs, die:</p>
<ul>
<li>schnell,</li>
<li>deterministisch,</li>
<li>flake-arm
sind (Validation, Error-States, Persistenz-Regeln, Reihenfolge).</li>
</ul>
<p>Playwright: <code>page.route('**/api/chat**', route =&gt; route.fulfill(...))</code> o.ä.</p>
<hr>
<h2>4) Zwei konkrete nächste Schritte (wenn du willst)</h2>
<ol>
<li>Sag mir, <strong>wie</strong> ihr die Conversation-ID verfügbar habt (URL? localStorage key? Response-Feld? DOM?) – dann gebe ich dir einen sauberen Assertion-Plan.</li>
<li>Nenn mir euren <strong>Chat-Endpoint</strong> (Pattern reicht, z.B. <code>/api/chat</code>), dann kann ich dir 2–3 Mock-Tests als Code-Skizze formulieren (inkl. einmaligem 500 und einmaligem Success).</li>
</ol>
</p></div><div class="timestamp">18:22</div></div><div class="message user"><div class="bubble"><p><p>Hier sind die wichtigsten Erkenntnisse zu deinen Fragen:1. Chat-Endpunkte:POST /api/chat - Hauptendpunkt für Chat-NachrichtenPOST /api/chats - Erstellt einen neuen ChatGET /api/chats/{chat_id} - Lädt einen bestimmten ChatGET /api/chats/{chat_id}/messages - Lädt Nachrichten eines ChatsPUT /api/chats/{chat_id}/title - Aktualisiert den Chat-Titel2. Conversation-ID:Wird als chat_id in den API-Endpunkten verwendetWird erstellt, wenn ein neuer Chat über POST /api/chats gestartet wirdWird in der Antwort auf die Chat-Erstellung zurückgegeben3. Mock-Test-Skizze:javascript// Test für erfolgreiche Chat-Erstellungtest('sollte erfolgreich einen neuen Chat erstellen', async ({ page }) =&gt; {  // Mock für Chat-Erstellung  await page.route('<strong>/api/chats', route =&gt; {    route.fulfill({      status: 200,      contentType: 'application/json',      body: JSON.stringify({        id: 'test-chat-123',        title: 'Neuer Test-Chat',        created_at: new Date().toISOString()      })    });  });  // Testcode...});// Test für Server-Fehlertest('sollte mit Server-Fehler umgehen', async ({ page }) =&gt; {  await page.route('</strong>/api/chat', route =&gt; {    route.fulfill({      status: 500,      body: 'Internal Server Error'    });  });  // Testcode...});// Test für erfolgreiche Nachrichttest('sollte eine Nachricht erfolgreich senden', async ({ page }) =&gt; {  await page.route('**/api/chat', route =&gt; {    route.fulfill({      status: 200,      contentType: 'application/json',      body: JSON.stringify({        id: 'msg-123',        content: 'Antwort vom Modell',        timestamp: new Date().toISOString()      })    });  });  // Testcode...});</p>
</p></div><div class="timestamp">18:22</div></div><div class="message assistant"><div class="bubble"><p><p>Super – mit euren konkreten Endpunkten kann man Mock-Tests sehr sauber und stabil machen. Unten sind 3 „Diamant“-Tests als <strong>konkrete Playwright-Skizzen</strong>, plus ein paar wichtige Details, damit sie nicht flaken.</p>
<blockquote>
<p>Annahmen: Ihr nutzt Playwright Test (<code>import { test, expect } from '@playwright/test'</code>), und UI startet auf <code>/</code>. Selektoren bitte ggf. an eure App anpassen.</p>
</blockquote>
<hr>
<h2>1) Deterministischer Happy-Path mit Mock: Chat erstellen + Nachricht senden</h2>
<p><strong>Ziel:</strong> UI-Flow ist korrekt, unabhängig von DB/LLM. Prüft auch, dass Requests die richtige <code>chat_id</code> verwenden.</p>
<pre><code class="language-js">import { test, expect } from '@playwright/test';

test('chat flow (mock): erstellt chat, sendet nachricht, rendert antwort', async ({ page }) =&gt; {
  // 1) Mock: POST /api/chats -&gt; neue chat_id
  await page.route('**/api/chats', async route =&gt; {
    if (route.request().method() !== 'POST') return route.fallback();

    return route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        id: 'test-chat-123',
        title: 'Neuer Test-Chat',
        created_at: new Date('2025-12-31T17:30:00.000Z').toISOString(),
      }),
    });
  });

  // 2) Mock: POST /api/chat -&gt; assistant antwort
  await page.route('**/api/chat', async route =&gt; {
    if (route.request().method() !== 'POST') return route.fallback();

    const body = route.request().postDataJSON?.() ?? {};
    // Optional: harte Contract-Assertion
    // Erwartung: body.chat_id === 'test-chat-123'
    if (body.chat_id &amp;&amp; body.chat_id !== 'test-chat-123') {
      return route.fulfill({ status: 400, body: 'wrong chat_id' });
    }

    return route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        id: 'msg-123',
        role: 'assistant',
        content: 'Antwort vom Modell',
        timestamp: new Date('2025-12-31T17:30:05.000Z').toISOString(),
      }),
    });
  });

  await page.goto('/');

  // Neuer Chat
  await page.getByRole('button', { name: /neuer chat/i }).click();

  // Nachricht senden
  const input = page.getByRole('textbox'); // ggf. getByRole('textbox', { name: /nachricht/i })
  await input.fill('Hallo Janus');
  await input.press('Enter');

  // Assertions: user msg + assistant msg gerendert
  await expect(page.locator('.message.user').filter({ hasText: 'Hallo Janus' })).toBeVisible();
  await expect(page.locator('.message.assistant').filter({ hasText: 'Antwort vom Modell' })).toBeVisible();

  // Optional: Input ist wieder leer
  await expect(input).toHaveValue('');
});
</code></pre>
<p><strong>Warum gut:</strong> Das ist euer jetziger Test, aber „CI-stabil“ und schneller, weil kein echtes Backend/LLM.</p>
<hr>
<h2>2) „Neuer Chat“ erzeugt neue Conversation-ID (zwei Chat-IDs hintereinander)</h2>
<p><strong>Ziel:</strong> Nicht nur UI resetten, sondern wirklich neue <code>chat_id</code>.</p>
<pre><code class="language-js">import { test, expect } from '@playwright/test';

test('new chat (mock): erzeugt neue chat_id und trennt konversationen', async ({ page }) =&gt; {
  const createdChatIds = ['chat-1', 'chat-2'];

  await page.route('**/api/chats', async route =&gt; {
    if (route.request().method() !== 'POST') return route.fallback();

    const id = createdChatIds.shift();
    return route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ id, title: 'Chat', created_at: new Date().toISOString() }),
    });
  });

  const seenChatIds = [];
  await page.route('**/api/chat', async route =&gt; {
    if (route.request().method() !== 'POST') return route.fallback();

    const body = route.request().postDataJSON?.() ?? {};
    if (body.chat_id) seenChatIds.push(body.chat_id);

    return route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ id: 'a1', role: 'assistant', content: `ok-${body.chat_id ?? 'noid'}` }),
    });
  });

  await page.goto('/');

  // Chat 1
  await page.getByRole('button', { name: /neuer chat/i }).click();
  await page.getByRole('textbox').fill('A');
  await page.getByRole('textbox').press('Enter');
  await expect(page.locator('.message.user', { hasText: 'A' })).toBeVisible();

  // Reset -&gt; Chat 2
  await page.getByRole('button', { name: /neuer chat/i }).click();

  // Erwartung: Verlauf ist leer (je nach UI kann man hier auf "keine .message" oder "placeholder" prüfen)
  await expect(page.locator('.message.user')).toHaveCount(0);

  await page.getByRole('textbox').fill('B');
  await page.getByRole('textbox').press('Enter');
  await expect(page.locator('.message.user', { hasText: 'B' })).toBeVisible();

  // Harte Assertion: Requests gingen mit zwei unterschiedlichen chat_ids raus
  expect(seenChatIds).toEqual(['chat-1', 'chat-2']);
});
</code></pre>
<p><strong>Wichtig:</strong> Diese Art Test ist Goldstandard, weil sie <strong>Contract + UI</strong> prüft.</p>
<hr>
<h2>3) Fehlerfall 500 für POST /api/chat: UI zeigt Fehler und bleibt benutzbar</h2>
<p><strong>Ziel:</strong> Kein endloser Loader, klarer Error-State, Input bleibt bedienbar.</p>
<pre><code class="language-js">import { test, expect } from '@playwright/test';

test('error handling (mock): 500 beim senden zeigt fehlermeldung, kein stuck state', async ({ page }) =&gt; {
  // Chat-Erstellung ok
  await page.route('**/api/chats', route =&gt; {
    if (route.request().method() !== 'POST') return route.fallback();
    return route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ id: 'test-chat-123', title: 'Chat', created_at: new Date().toISOString() }),
    });
  });

  // Senden -&gt; 500
  await page.route('**/api/chat', route =&gt; {
    if (route.request().method() !== 'POST') return route.fallback();
    return route.fulfill({ status: 500, contentType: 'text/plain', body: 'Internal Server Error' });
  });

  await page.goto('/');
  await page.getByRole('button', { name: /neuer chat/i }).click();

  const input = page.getByRole('textbox');
  await input.fill('Hello');
  await input.press('Enter');

  // Erwartung: Fehlermeldung sichtbar (bitte an euren UI-Text/Selector anpassen)
  await expect(page.getByText(/fehler|failed|something went wrong/i)).toBeVisible();

  // Erwartung: Input weiterhin nutzbar (kein global disabled / overlay)
  await expect(input).toBeEnabled();
});
</code></pre>
<p><strong>Tipp:</strong> Wenn ihr noch keinen sichtbaren Fehlertext habt, ist das ein echtes Produkt-Upgrade, das ihr hiermit „erzwingt“.</p>
<hr>
<h2>4) Kleine, aber wichtige Verbesserungen an euren Mocks</h2>
<ol>
<li><p><strong><code>route.fallback()</code> für nicht gemockte Methoden</strong><br>Sonst fängt ihr ggf. <code>GET /api/chats/...</code> unabsichtlich ab.</p>
</li>
<li><p><strong>Fixe Timestamps statt <code>new Date()</code></strong><br>Macht Snapshots/Sortierungen stabiler. (Oder zumindest keine Assertions auf genaue Zeit.)</p>
</li>
<li><p><strong>Request-Body validieren</strong><br>Das hebt Tests von „UI-only“ auf „Contract“-Level (Diamantstandard).</p>
</li>
<li><p><strong>Einmalige Fehler (Retry-Test)</strong><br>Erstes <code>POST /api/chat</code> → 500, zweites → 200. Dann testet ihr einen Retry-Button wirklich.</p>
</li>
</ol>
<hr>
<h2>5) Zwei Fragen, damit ich das 1:1 auf euren Code zuschneiden kann</h2>
<ol>
<li>Wie sieht der Request-Body bei <code>POST /api/chat</code> genau aus? (Felder: <code>chat_id</code>, <code>message</code>, <code>messages[]</code>, …)  </li>
<li>Rendert ihr eine explizite Fehler-Komponente (z.B. <code>.message.error</code>, Toast, Banner)? Wenn ja: welcher Selector/Text?</li>
</ol>
<p>Dann kann ich dir die Tests so formulieren, dass sie bei euch praktisch „copy/paste + minimal anpassen“ sind.</p>
</p></div><div class="timestamp">18:22</div></div><div class="message user"><div class="bubble"><p><ol>
<li>Request-Body bei POST /api/chat:Basierend auf dem Code in schemas.py und chat.py:typescript{  prompt?: string;               // Optionaler Text-Prompt  content?: ContentPart[];      // Alternative zu prompt für strukturierte Inhalte  provider: string;             // Z.B. "openai", "gemini" etc.  model?: string;               // Optionales spezifisches Modell  chat_id?: number;             // ID des bestehenden Chats  temperature?: number;         // Optional: Kreativität  max_tokens?: number;          // Optional: Maximale Antwortlänge}2. Error-Handling:HTTP-Status-Codes:200: Erfolg400: Ungültige Anfrage404: Chat nicht gefunden429: Rate Limit überschritten500: Server-FehlerFehlerkomponenten:Toast-Nachrichten für BenachrichtigungenRote Hervorhebung für fehlgeschlagene NachrichtenWiederholungs-Button für fehlgeschlagene AnfragenBeispiel für einen robusten Test mit Fehlerbehandlung:javascripttest('sollte Server-Fehler anzeigen', async ({ page }) =&gt; {  // Mock für fehlgeschlagene Anfrage  await page.route('**/api/chat', route =&gt; {    route.fulfill({      status: 500,      body: JSON.stringify({ detail: "Internal server error" })    });  });  // Nachricht senden  const messageInput = page.getByRole('textbox');  await messageInput.fill('Testnachricht');  await messageInput.press('Enter');  // Auf Fehlermeldung warten  const errorToast = page.locator('.toast.error');  await expect(errorToast).toBeVisible();    // Prüfen, ob die Nachricht als fehlgeschlagen markiert ist  const failedMessage = page.locator('.message.failed');  await expect(failedMessage).toContainText('Fehler beim Senden');    // Prüfen, ob Wiederholungs-Button sichtbar ist  const retryButton = failedMessage.locator('button.retry');  await expect(retryButton).toBeVisible();});</li>
</ol>
</p></div><div class="timestamp">18:22</div></div><div class="message assistant"><div class="bubble"><p><p>Perfekt – damit kann man die Tests <strong>contract-sicher</strong> machen (Body prüfen) und eure <strong>Error-UX</strong> (Toast + failed message + Retry) zuverlässig testen. Hier sind drei „Diamant“-Tests als nahezu copy/paste-fähige Skizzen, zugeschnitten auf euren Request-Body und Error-Handling.</p>
<hr>
<h2>A) Contract-Test: <code>POST /api/chat</code> enthält <code>provider</code> + <code>prompt</code> und verwendet die richtige <code>chat_id</code></h2>
<p><strong>Ziel:</strong> stellt sicher, dass UI → API-Contract stabil bleibt (kein „stiller“ Break).</p>
<pre><code class="language-js">import { test, expect } from '@playwright/test';

test('contract (mock): POST /api/chat sendet provider + prompt + chat_id', async ({ page }) =&gt; {
  // 1) Chat erstellen -&gt; gibt chat_id zurück
  await page.route('**/api/chats', async route =&gt; {
    if (route.request().method() !== 'POST') return route.fallback();
    return route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ id: 123, title: 'Chat', created_at: '2025-12-31T17:00:00.000Z' }),
    });
  });

  let capturedBody;

  // 2) Chat senden -&gt; Contract prüfen
  await page.route('**/api/chat', async route =&gt; {
    if (route.request().method() !== 'POST') return route.fallback();

    capturedBody = route.request().postDataJSON?.();

    return route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        id: 'msg-1',
        role: 'assistant',
        content: 'Antwort ok',
        timestamp: '2025-12-31T17:00:02.000Z',
      }),
    });
  });

  await page.goto('/');

  await page.getByRole('button', { name: /neuer chat/i }).click();

  const input = page.getByRole('textbox');
  await input.fill('Testnachricht');
  await input.press('Enter');

  // UI Assertion
  await expect(page.locator('.message.assistant', { hasText: 'Antwort ok' })).toBeVisible();

  // Contract Assertions (hart)
  expect(capturedBody).toBeTruthy();
  expect(capturedBody.provider).toBeTruthy();         // z.B. "openai"
  expect(capturedBody.prompt ?? null).toBe('Testnachricht');
  expect(capturedBody.chat_id ?? null).toBe(123);

  // Optional: sicherstellen, dass NICHT prompt+content gleichzeitig gesendet wird
  expect(!(capturedBody.prompt &amp;&amp; capturedBody.content)).toBeTruthy();
});
</code></pre>
<p><strong>Hinweis:</strong> Wenn eure UI statt <code>prompt</code> die <code>content: ContentPart[]</code> nutzt, dann die Assertion entsprechend drehen.</p>
<hr>
<h2>B) Error-Handling 500: Toast + Nachricht als failed + Retry-Button sichtbar</h2>
<p>Das ist sehr nah an deinem Beispiel, aber mit zwei Stabilitäts-Details:</p>
<ul>
<li><code>contentType: 'application/json'</code> + Body sauber JSON</li>
<li>Optional: sicherstellen, dass <strong>kein Assistant-Message</strong> erscheint</li>
</ul>
<pre><code class="language-js">import { test, expect } from '@playwright/test';

test('error (mock): 500 zeigt toast, markiert message failed, zeigt retry', async ({ page }) =&gt; {
  // Chat erstellen
  await page.route('**/api/chats', async route =&gt; {
    if (route.request().method() !== 'POST') return route.fallback();
    return route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ id: 123, title: 'Chat', created_at: '2025-12-31T17:00:00.000Z' }),
    });
  });

  // Chat send -&gt; 500
  await page.route('**/api/chat', async route =&gt; {
    if (route.request().method() !== 'POST') return route.fallback();
    return route.fulfill({
      status: 500,
      contentType: 'application/json',
      body: JSON.stringify({ detail: 'Internal server error' }),
    });
  });

  await page.goto('/');
  await page.getByRole('button', { name: /neuer chat/i }).click();

  const messageInput = page.getByRole('textbox');
  await messageInput.fill('Testnachricht');
  await messageInput.press('Enter');

  // Toast sichtbar
  const errorToast = page.locator('.toast.error');
  await expect(errorToast).toBeVisible();

  // Nachricht als fehlgeschlagen markiert
  const failedMessage = page.locator('.message.failed').filter({ hasText: 'Testnachricht' });
  await expect(failedMessage).toBeVisible();

  // Retry sichtbar
  const retryButton = failedMessage.locator('button.retry');
  await expect(retryButton).toBeVisible();

  // Optional: Es darf keine Assistant-Antwort erscheinen
  await expect(page.locator('.message.assistant')).toHaveCount(0);
});
</code></pre>
<hr>
<h2>C) Retry-Flow: erstes Senden 500, nach Retry 200 und Failed-Status verschwindet</h2>
<p><strong>Ziel:</strong> echter Diamant-Test, weil er einen kompletten Recovery-Flow verifiziert.</p>
<pre><code class="language-js">import { test, expect } from '@playwright/test';

test('retry (mock): nach 500 kann retry erfolgreich senden und failed marker verschwindet', async ({ page }) =&gt; {
  await page.route('**/api/chats', async route =&gt; {
    if (route.request().method() !== 'POST') return route.fallback();
    return route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ id: 123, title: 'Chat', created_at: '2025-12-31T17:00:00.000Z' }),
    });
  });

  let callCount = 0;

  await page.route('**/api/chat', async route =&gt; {
    if (route.request().method() !== 'POST') return route.fallback();
    callCount += 1;

    if (callCount === 1) {
      return route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({ detail: 'Internal server error' }),
      });
    }

    return route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        id: 'msg-2',
        role: 'assistant',
        content: 'Jetzt hat es geklappt',
        timestamp: '2025-12-31T17:00:10.000Z',
      }),
    });
  });

  await page.goto('/');
  await page.getByRole('button', { name: /neuer chat/i }).click();

  const input = page.getByRole('textbox');
  await input.fill('Testnachricht');
  await input.press('Enter');

  const failedMessage = page.locator('.message.failed').filter({ hasText: 'Testnachricht' });
  await expect(failedMessage).toBeVisible();

  // Retry klicken
  await failedMessage.locator('button.retry').click();

  // Assistant Antwort kommt
  await expect(page.locator('.message.assistant', { hasText: 'Jetzt hat es geklappt' })).toBeVisible();

  // Failed marker sollte weg sein (oder zumindest nicht mehr "failed" sein)
  await expect(failedMessage).toHaveCount(0);
});
</code></pre>
<blockquote>
<p>Falls ihr die failed Message im DOM behaltet, aber z.B. Klasse wechselt (z.B. <code>.message.sent</code>), dann die letzte Assertion entsprechend anpassen.</p>
</blockquote>
<hr>
<h2>D) Mini-Upgrade für Stabilität (ohne data-testid)</h2>
<p>Wenn ihr keine <code>data-testid</code> wollt, würde ich trotzdem 1–2 „semantische“ Hooks empfehlen:</p>
<ul>
<li>Retry-Button: <code>aria-label="Retry message"</code> oder sichtbarer Text „Erneut versuchen“</li>
<li>Chatlog Container: <code>role="log"</code></li>
</ul>
<p>Dann könnt ihr von CSS-Klassen weg und <code>getByRole</code> nutzen, was extrem robust ist.</p>
<hr>
<h2>Zwei letzte Rückfragen (damit ich es 100% passend mache)</h2>
<ol>
<li>Ist die Chat-ID im Response wirklich <code>{ id: 123 }</code> oder <code>{ chat_id: 123 }</code>? (du sagtest „id“ bei <code>/api/chats</code>, aber „chat_id“ im Request)  </li>
<li>Wenn ihr <code>prompt</code> <strong>oder</strong> <code>content</code> sendet: Welche Form nutzt die UI aktuell? (reiner Text =&gt; <code>prompt</code>?)</li>
</ol>
<p>Wenn du das bestätigst, kann ich dir die Assertions exakt auf euren Ist-Zustand „festnageln“ (inkl. 400/404/429 Tests in derselben Qualität).</p>
</p></div><div class="timestamp">18:22</div></div><div class="message user"><div class="bubble"><p><p>Antwort auf deine Fragen: Chat-ID im Response: Die Response von /api/chats verwendet { id: 123 } (nicht chat_id) Im Request-Body wird jedoch chat_id verwendet (nicht id) Feld für die Nachrichtenübermittlung: Die UI verwendet prompt für reine Textnachrichten content wird für strukturierte Inhalte (z.B. mit Bildern) verwendet Korrekte Test-Implementierung: javascript // Für Chat-Erstellung const createResponse = await page.request.post('/api/chats', {   data: { title: 'Test-Chat' } }); const chatId = (await createResponse.json()).id;  // Achtung: Hier ist es .id // Für Nachricht senden await page.request.post('/api/chat', {   data: {     chat_id: chatId,  // Achtung: Hier ist es chat_id     prompt: 'Hallo Janus',     provider: 'openai'   } });</p>
</p></div><div class="timestamp">18:22</div></div><div class="message assistant"><div class="bubble"><p><p>Alles klar – damit können wir die Tests <strong>exakt</strong> an euren Contract nageln: <strong><code>/api/chats</code> liefert <code>{ id }</code></strong>, und <strong><code>/api/chat</code> erwartet <code>chat_id</code></strong> plus <code>prompt</code> und <code>provider</code>.</p>
<p>Unten sind „Diamant“-taugliche, deterministische Playwright-Tests (UI-Flow + Contract-Assertions + Error/Retry).</p>
<hr>
<h2>1) Diamant: Contract-Assertion für <code>/api/chat</code> (chat_id aus <code>/api/chats</code> wird korrekt verwendet)</h2>
<pre><code class="language-js">import { test, expect } from '@playwright/test';

test('contract (mock): erstellt chat (id) und sendet chat_id + prompt + provider', async ({ page }) =&gt; {
  // POST /api/chats -&gt; { id }
  await page.route('**/api/chats', async route =&gt; {
    if (route.request().method() !== 'POST') return route.fallback();
    return route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ id: 123, title: 'Test-Chat', created_at: '2025-12-31T17:00:00.000Z' }),
    });
  });

  let chatRequestBody;

  // POST /api/chat -&gt; prüfe Request-Body, gib Response zurück
  await page.route('**/api/chat', async route =&gt; {
    if (route.request().method() !== 'POST') return route.fallback();

    chatRequestBody = route.request().postDataJSON?.();

    // Harte Contract-Checks direkt im Mock (optional, aber sehr effektiv)
    if (chatRequestBody.chat_id !== 123) {
      return route.fulfill({ status: 400, contentType: 'application/json', body: JSON.stringify({ detail: 'chat_id mismatch' }) });
    }
    if (chatRequestBody.prompt !== 'Hallo Janus') {
      return route.fulfill({ status: 400, contentType: 'application/json', body: JSON.stringify({ detail: 'prompt mismatch' }) });
    }
    if (!chatRequestBody.provider) {
      return route.fulfill({ status: 400, contentType: 'application/json', body: JSON.stringify({ detail: 'provider missing' }) });
    }

    return route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        id: 'msg-1',
        role: 'assistant',
        content: 'Antwort vom Modell',
        timestamp: '2025-12-31T17:00:02.000Z',
      }),
    });
  });

  await page.goto('/');
  await page.getByRole('button', { name: /neuer chat/i }).click();

  const input = page.getByRole('textbox');
  await input.fill('Hallo Janus');
  await input.press('Enter');

  // UI Assertions
  await expect(page.locator('.message.user', { hasText: 'Hallo Janus' })).toBeVisible();
  await expect(page.locator('.message.assistant', { hasText: 'Antwort vom Modell' })).toBeVisible();

  // Contract Assertions (zusätzlich, falls ihr nicht im Mock failen wollt)
  expect(chatRequestBody).toMatchObject({
    chat_id: 123,
    prompt: 'Hallo Janus',
  });
  expect(typeof chatRequestBody.provider).toBe('string');
});
</code></pre>
<hr>
<h2>2) Diamant: 500-Error -&gt; Toast + <code>.message.failed</code> + Retry sichtbar</h2>
<pre><code class="language-js">import { test, expect } from '@playwright/test';

test('error (mock): 500 zeigt toast, markiert message failed, zeigt retry', async ({ page }) =&gt; {
  await page.route('**/api/chats', async route =&gt; {
    if (route.request().method() !== 'POST') return route.fallback();
    return route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ id: 123, title: 'Test-Chat', created_at: '2025-12-31T17:00:00.000Z' }),
    });
  });

  await page.route('**/api/chat', async route =&gt; {
    if (route.request().method() !== 'POST') return route.fallback();
    return route.fulfill({
      status: 500,
      contentType: 'application/json',
      body: JSON.stringify({ detail: 'Internal server error' }),
    });
  });

  await page.goto('/');
  await page.getByRole('button', { name: /neuer chat/i }).click();

  const input = page.getByRole('textbox');
  await input.fill('Testnachricht');
  await input.press('Enter');

  await expect(page.locator('.toast.error')).toBeVisible();

  const failedMessage = page.locator('.message.failed').filter({ hasText: 'Testnachricht' });
  await expect(failedMessage).toBeVisible();

  await expect(failedMessage.locator('button.retry')).toBeVisible();

  // Optional: Keine Assistant Message entstanden
  await expect(page.locator('.message.assistant')).toHaveCount(0);
});
</code></pre>
<hr>
<h2>3) Diamant: Retry-Flow -&gt; erstes Mal 500, nach Retry 200, failed marker weg + Assistant erscheint</h2>
<pre><code class="language-js">import { test, expect } from '@playwright/test';

test('retry (mock): nach 500 führt retry zu 200 und entfernt failed state', async ({ page }) =&gt; {
  await page.route('**/api/chats', async route =&gt; {
    if (route.request().method() !== 'POST') return route.fallback();
    return route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ id: 123, title: 'Test-Chat', created_at: '2025-12-31T17:00:00.000Z' }),
    });
  });

  let callCount = 0;

  await page.route('**/api/chat', async route =&gt; {
    if (route.request().method() !== 'POST') return route.fallback();
    callCount += 1;

    if (callCount === 1) {
      return route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({ detail: 'Internal server error' }),
      });
    }

    return route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        id: 'msg-2',
        role: 'assistant',
        content: 'Jetzt hat es geklappt',
        timestamp: '2025-12-31T17:00:10.000Z',
      }),
    });
  });

  await page.goto('/');
  await page.getByRole('button', { name: /neuer chat/i }).click();

  const input = page.getByRole('textbox');
  await input.fill('Testnachricht');
  await input.press('Enter');

  const failedMessage = page.locator('.message.failed').filter({ hasText: 'Testnachricht' });
  await expect(failedMessage).toBeVisible();

  await failedMessage.locator('button.retry').click();

  await expect(page.locator('.message.assistant', { hasText: 'Jetzt hat es geklappt' })).toBeVisible();

  // Je nach Implementierung: entweder verschwindet failed-message komplett...
  await expect(page.locator('.message.failed').filter({ hasText: 'Testnachricht' })).toHaveCount(0);
  // ...oder sie verliert nur die Klasse "failed" (dann diese Assertion anpassen).
});
</code></pre>
<hr>
<h2>4) Kleines, aber sehr wirkungsvolles Upgrade: „Leere Nachricht“ darf nicht senden</h2>
<p>Wenn ihr das noch nicht testet, ist das ein extrem günstiger Qualitätsgewinn:</p>
<pre><code class="language-js">test('validation: whitespace wird nicht gesendet', async ({ page }) =&gt; {
  let chatCalled = false;

  await page.route('**/api/chat', route =&gt; {
    chatCalled = true;
    return route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ content: 'x' }) });
  });

  await page.goto('/');
  const input = page.getByRole('textbox');
  await input.fill('   ');
  await input.press('Enter');

  expect(chatCalled).toBe(false);
  await expect(page.locator('.message.user')).toHaveCount(0);
});
</code></pre>
<hr>
<h2>2 Hinweise, die eure Tests noch „härter“ machen</h2>
<ol>
<li><strong>Provider fest verdrahten</strong>: Wenn die UI provider auswählbar macht, testet explizit die Default-Logik (z.B. <code>openai</code>) oder die Auswahl im UI und prüft dann den Request-Body.  </li>
<li><strong>429 separat</strong> (Rate Limit): Bei euch gibt’s dafür einen eigenen UX-Pfad – das ist ein typischer „Production pain“, daher lohnt ein eigener Test.</li>
</ol>
<p>Wenn du mir kurz sagst, <strong>wie der Provider in der UI gesetzt wird</strong> (Dropdown? Default in Settings?), kann ich dir den Contract-Test so erweitern, dass er auch die Provider-Auswahl stabil verifiziert.</p>
</p></div><div class="timestamp">18:22</div></div><div class="message user"><div class="bubble"><p><p>hi</p>
</p></div><div class="timestamp">18:22</div></div><div class="message assistant"><div class="bubble"><p><p>Hi! Womit soll ich dir jetzt helfen – weiter an den Playwright-„Diamant“-Tests (z.B. 429/404/Persistenz), oder hast du ein anderes Thema?</p>
</p></div><div class="timestamp">18:22</div></div><div class="message user"><div class="bubble"><p><p>hi</p>
</p></div><div class="timestamp">18:22</div></div><div class="message assistant"><div class="bubble"><p><p>Hi! Sag mir kurz, was du brauchst:</p>
<ol>
<li>Weiter an euren Chat-Tests (z.B. 429/404, Persistenz/Reload, Provider-Auswahl)  </li>
<li>Hilfe beim Debuggen von Flakes/CI  </li>
<li>Etwas ganz anderes</li>
</ol>
<p>Was ist dein Ziel?</p>
</p></div><div class="timestamp">18:22</div></div><div class="message user"><div class="bubble"><p><p>hi</p>
</p></div><div class="timestamp">18:22</div></div><div class="message user"><div class="bubble"><p><p>Hallo Janus</p>
</p></div><div class="timestamp">18:22</div></div><div class="message assistant"><div class="bubble"><p><p>Hallo Janus! Wie kann ich dir helfen?</p>
<p>Wenn du willst, können wir direkt weitermachen mit den „Diamant“-Tests. Sag mir einfach, was du als Nächstes brauchst, z.B.:</p>
<ul>
<li>429 Rate-Limit-Test (Toast + Retry/Backoff)</li>
<li>404 „Chat nicht gefunden“ (neuer Chat wird angeboten?)</li>
<li>Persistenz/Reload (Chatverlauf bleibt nach Refresh)</li>
<li>Provider-Auswahl im UI + Contract-Assertion (<code>provider</code> im Request)</li>
</ul>
</p></div><div class="timestamp">18:22</div></div><div class="message user"><div class="bubble"><p><p>hi</p>
</p></div><div class="timestamp">18:22</div></div><div class="message user"><div class="bubble"><p><p>hi</p>
</p></div><div class="timestamp">18:22</div></div><div class="message user"><div class="bubble"><p><p>hi</p>
</p></div><div class="timestamp">18:22</div></div><div class="message user"><div class="bubble"><p><p>Hallo Janus</p>
</p></div><div class="timestamp">18:22</div></div><div class="message assistant"><div class="bubble"><p><p>Hallo Janus. Was möchtest du jetzt konkret machen?</p>
<ol>
<li>429/Rate-Limit-Test schreiben  </li>
<li>Persistenz/Reload-Test (Chatverlauf + chat_id nach <code>page.reload()</code>)  </li>
<li>404/Chat nicht gefunden + Recovery  </li>
<li>Provider-Auswahl im UI testen (Request enthält richtigen <code>provider</code>)</li>
</ol>
<p>Nenn mir die Nummer und (falls relevant) den aktuellen UI-Selector/Label (z.B. Text vom Toast oder Provider-Dropdown), dann schreibe ich dir den passenden Test.</p>
</p></div><div class="timestamp">18:22</div></div><div class="message user"><div class="bubble"><p><p>hi</p>
</p></div><div class="timestamp">18:22</div></div><div class="message assistant"><div class="bubble"><p><p>400: Missing chat_id</p>
</p></div><div class="timestamp">18:22</div></div></div>
              <div id="chat-input-container">
                <form id="chat-form">
                  <input type="file" id="image-upload-input" style="display: none" accept="image/*">
                  <button type="button" id="image-upload-btn">📎</button>
                  <input type="text" id="chat-input" placeholder="Nachricht an Janus senden...">
                  <button type="button" id="mic-btn">🎤</button>
                  <button type="button" id="tts-toggle-btn" title="TTS aktivieren/deaktivieren">
                    🔊
                  </button>
                  <button id="send-button" type="submit">Senden</button>
                </form>
              </div>
            </div>
          </div>
        </div>
      
---------------------------------------------------
  ✓  6 [webkit] › tests\functional\debug-selector.spec.js:3:1 › Spionage-Test: HTML Struktur auslesen (6.4s)

  6 passed (13.4s)
