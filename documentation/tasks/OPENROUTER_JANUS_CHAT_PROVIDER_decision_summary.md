# LATEST DECISION SUMMARY - OPENROUTER JANUS CHAT PROVIDER

Feature Name: OpenRouter als Janus-Chatprovider mit zertifizierten Modellen

Primary Goal: Einen eigenen OpenRouter-API-Key in Janus verwenden und darüber ausgewählte Claude-, GLM-, DeepSeek- und Qwen-Modelle mit vollständiger Janus-Funktion nutzen.

User Problem: Die bestehende OpenRouter-Nutzung dient überwiegend interner Codex-/Worker-Delegation und stellt OpenRouter noch nicht als normalen, transparenten Janus-Chatprovider mit sicherem Key, Modellauswahl und DeepDive-Kostenwahrheit bereit.

User Value: Ein zusätzlicher sicher gespeicherter API-Key eröffnet mehrere starke Modellfamilien, während Janus weiterhin Verlauf, Redaction, Skills, Tools, Berechtigungen, Auswahl und Kostenanzeige kontrolliert.

Primary Target Surface: Bestehendes Provider- und Modell-Dropdown im Janus-Chat.

Existing or New Surface: Bestehende Chat-Auswahl wird um den neuen Provider `OpenRouter` ergänzt; bestehende Provider und Modelle bleiben unverändert.

Existence Confirmation: Bestehende Provider-/Modell-Dropdowns, Settings-Keyflächen, DeepDive und OpenRouter-Runtime-Grundlage sind im Repository verifiziert; der OpenRouter-Chatprovider selbst ist neu.

User Trigger: Der Nutzer speichert einen OpenRouter-Key in den Einstellungen, wählt danach `OpenRouter` im Provider-Dropdown und anschließend ein sichtbares zertifiziertes Modell im bestehenden Modell-Dropdown.

Success Behavior: OpenRouter ist im Chat auswählbar, wenn ein gültiger eigener Key und mindestens ein vollständig zertifiziertes, exakt versioniertes Modell vorhanden sind. Der Nutzer wählt das konkrete Modell manuell. Der erste Kandidatensatz enthält genau je ein Modell aus Claude, GLM, DeepSeek und Qwen; der Provider darf starten, sobald mindestens ein Kandidat die vollständige Janus-Zertifizierung bestanden hat. Nur bestandene Modelle werden angezeigt.

Failure Behavior: Ungültiger oder fehlender Key, kein zertifiziertes Modell, nicht mehr verfügbare Modellversion oder ein Provider-/Modellfehler bleiben fail-closed. Nur der aktuelle Turn endet; es gibt keine automatische Wiederholung, keine doppelte Übertragung und keinen automatischen Wechsel zu einem anderen OpenRouter-Modell oder Provider. Durchgefallene oder nicht mehr eindeutig identifizierbare Modelle bleiben verborgen.

User Action Surface: OpenRouter-Key sicher speichern, ersetzen und ausschließlich für OpenRouter löschen; OpenRouter manuell als Provider wählen; ein zertifiziertes Modell manuell wählen; Verbrauch und Kosten im bestehenden DeepDive nachvollziehen.

Data / Persistence: Der OpenRouter-Key wird dauerhaft im bestehenden sicheren Keyring unter einem eigenen OpenRouter-Namensraum gespeichert. Zertifizierte Modell-IDs werden ausschließlich über geprüfte Janus-Updates ausgeliefert. DeepDive speichert die tatsächlich von OpenRouter gelieferten Nutzungs- und Kostenwerte getrennt nach Provider, konkretem Modell und Turn. Fehlende Werte werden als `nicht verfügbar` markiert und nicht geschätzt.

Security / Privacy: OpenRouter nutzt dieselbe Janus-Redaction, denselben notwendigen Gesprächskontext, dieselben Skills, Tools, Berechtigungen und Bestätigungsregeln wie andere externe API-Key-Provider. Die Datenschutzinformation nennt ausdrücklich, dass Inhalte über OpenRouter an den ausgewählten Modellanbieter gelangen können. OpenRouter-Credentials und Aktionen beeinflussen keine anderen Provider-Keys. Der normale Chat zeigt ausschließlich vollständig Janus-zertifizierte, exakt versionierte Modell-IDs; keine `latest`-Aliase.

Edge Cases: Ein erfolgreicher Turn bleibt fachlich erfolgreich, wenn OpenRouter einzelne tatsächliche Token- oder Kostendaten nicht liefert; DeepDive zeigt die fehlenden Felder sichtbar als `nicht verfügbar`. Änderungen an Modell-ID, konkreter Version oder Zertifizierungsbatterie sperren das Modell bis zu einer erneuten Zertifizierung in einem Janus-Update. Provider-Sichtbarkeit in den Einstellungen bleibt möglich, während die Chat-Auswahl ohne gültigen Key oder zertifiziertes Modell gesperrt ist.

Selection State Decision: Wird ein zuvor gültiger OpenRouter-Key ungültig oder das ausgewählte exakt versionierte Modell nicht mehr verfügbar beziehungsweise nicht mehr zertifiziert, bleiben `OpenRouter` und das konkrete Modell sichtbar ausgewählt, aber deaktiviert. Senden bleibt fail-closed gesperrt, bis dieselbe Auswahl wieder alle Voraussetzungen erfüllt oder der Nutzer bewusst eine andere gültige Auswahl trifft. Janus löscht die Auswahl nicht automatisch und wechselt weder Modell noch Provider.

Key Validity Contract: Ein gespeicherter oder ersetzter Key wird ohne Chatinhalt gegen den authentifizierten OpenRouter-Key-Status geprüft. Nur eine erfolgreiche Authentifizierung setzt den Key auf `VALID` und entsperrt die Chat-Voraussetzung. Eine Authentifizierungsablehnung setzt ihn auf `INVALID`; eine technisch nicht abgeschlossene Prüfung setzt ihn auf `UNVERIFIED`. `INVALID` und `UNVERIFIED` bleiben fail-closed. Eine vorübergehende Provider-, Netzwerk- oder Modellstörung macht einen zuvor `VALID` bestätigten Key nicht automatisch ungültig.

Certification Authority Contract: Vollständig zertifiziert ist ein exakt versioniertes Modell nur, wenn alle Pflichtfälle der im selben geprüften Janus-Update benannten, versionierten Zertifizierungsbatterie bestanden sind, die zugehörige Test- und Audit-Evidenz vollständig bestanden ist und der ausgelieferte Zertifizierungsdatensatz exakt diese Modell-ID, Modellversion und Batterieversion als bestanden markiert. Dieser ausgelieferte Datensatz ist die alleinige Laufzeitautorität. Fehlender Datensatz, fehlende Pflicht-Evidenz oder eine Abweichung von Modell-ID, Modellversion oder Batterieversion bedeutet nicht zertifiziert und damit verborgen. Eine Änderung an einem dieser drei Bindungswerte erfordert eine erneute vollständige Zertifizierung in einem späteren geprüften Janus-Update.

DeepDive Telemetry Contract: Autoritativ sind ausschließlich die von OpenRouter für den konkreten Turn gelieferten Response-Werte. Für Chat-Completions werden `response.model`, `usage.prompt_tokens`, `usage.completion_tokens`, `usage.total_tokens`, `usage.prompt_tokens_details.cached_tokens`, `usage.prompt_tokens_details.cache_write_tokens`, `usage.completion_tokens_details.reasoning_tokens`, `usage.cost` und `usage.cost_details.upstream_inference_cost` jeweils getrennt dem Janus-Turn zugeordnet, sofern vorhanden. `usage.cost` bleibt als tatsächlich belasteter Wert in OpenRouter-Credits erhalten; es gibt keine lokale Währungsumrechnung. Fehlende optionale Felder werden einzeln als `nicht verfügbar` geführt und weder aus anderen Feldern berechnet noch geschätzt. Weicht `response.model` von der bewusst ausgewählten exakt versionierten Modell-ID ab, gilt der Turn als Modellfehler und endet fail-closed.

Out of Scope: Vollständiger oder automatisch importierter OpenRouter-Modellkatalog; eingeschränkte oder experimentelle Modelle in der normalen Chat-Auswahl; automatische Modellwahl oder MOA-Routing zwischen OpenRouter-Modellen; Laufzeit-Zertifizierung; `latest`-Aliase; lokale Kostenschätzungen; automatische Wiederholung oder Fallback; Änderungen an bestehenden Provider-Credentials; OpenRouter als Ersatz für Embeddings; Release oder Produktionsaktivierung ohne vollständige Test- und Audit-Evidenz.

Routing Decision: FULL FEATURE PIPELINE

Routing Reason: Neue externe Providerintegration mit sicherer Credential-Persistenz, mehreren UI-/Runtime-/Telemetry-Flächen, Modellzertifizierung, Datenschutz und Kostenwahrheit.

Recommended Next Skill: `janus-spec-generator`

Decision Status: LOCKED
