# JANUS FEATURE SPEC - DIAMANTSTANDARD v4.4.3

## SPEC REVIEW EXECUTION ROUTING
target_skill: janus-spec-review
recommended_model: 5.6 Sol
recommended_reasoning: high
new_chat: yes
complexity_score: 80
confidence: HIGH
dashboard_hint: CRITICAL
reason: Externe Providerintegration mit isoliertem Credential, Zertifizierungsgate, Kostenwahrheit und mehreren bestehenden Janus-Oberflächen.

## SPEC REVIEW METADATA

- **Review Status:** APPROVED
- **Complexity Score:** 80
- **Risk:** HIGH
- **Recommended Review Model:** 5.6 Sol
- **Skill-1 Ready:** YES
- **Split Required:** NO
- **Reviewed At:** 2026-07-16
- **Review Confidence:** HIGH
- **Review Source:** janus-spec-review

## SPEC IMPLEMENTATION METADATA

- **Implementation Status:** DONE
- **Completed Tasks:** `TASK-OPENROUTER-JANUS-CHAT-PROVIDER.1`, `TASK-OPENROUTER-JANUS-CHAT-PROVIDER.2`, `TASK-OPENROUTER-JANUS-CHAT-PROVIDER.3`, `TASK-OPENROUTER-JANUS-CHAT-PROVIDER.4`, `TASK-OPENROUTER-JANUS-CHAT-PROVIDER.5`, `TASK-OPENROUTER-JANUS-CHAT-PROVIDER.6`
- **Latest Task Final Audit:** Task `.6` PASS WITH FIXES (`2026-07-18`)
- **Validation Evidence:** Task `.1` certification/catalog tests `18 passed`, headed existing-provider regression `10 passed`, manual validation and exact-version `latest` tripwire PASS; Task `.2` OpenRouter API lifecycle `19 passed`, isolated ChatGPT non-interference `1 passed`, Python/JavaScript syntax PASS, scoped mocked Headed Playwright `3 passed`, manual Settings missing-state evidence PASS, and Final-Audit-Validator PASS; Task `.3` bound Python suites `116 passed`, direct stream fail-closed/auth/model matrix PASS, Python/JavaScript syntax and scoped diff/credential checks PASS, exact headed Settings runner twice consecutively `3 passed`, safe manual non-activation observation PASS, and Final-Audit-Validator PASS; Task `.4` selection/eligibility backend matrix `41 passed`, exact headed selection/retention/privacy runner `4 passed`, focused Chat-Core regression `1 passed`, syntax/compile/diff/leak checks PASS, manual privacy/non-activation observation PASS, and Final-Audit-Validator PASS; Task `.5` telemetry/provider/cost/stream-handoff Python matrix `44 passed`, Chat-Core `1 passed`, headed DeepDive suite `3 passed`, compile/syntax/diff/credential checks PASS, and Final-Audit-Validator PASS WITH FIXES; Task `.6` conformance suite `96` then post-activation `101 passed`, live `TEST-RUN-2026-07-17-008` `117/117 PASS`, Final-Audit-Validator PASS WITH FIXES, documentation activation of four exact certified models
- **Evidence Paths:** `documentation/tasks/TASK-OPENROUTER-JANUS-CHAT-PROVIDER.1_final_audit.md`, `documentation/tasks/TASK-OPENROUTER-JANUS-CHAT-PROVIDER.1_AUDIT_PACKAGE.md`, `documentation/tasks/TASK-OPENROUTER-JANUS-CHAT-PROVIDER.2_final_audit.md`, `documentation/tasks/TASK-OPENROUTER-JANUS-CHAT-PROVIDER.2_AUDIT_PACKAGE.md`, `documentation/tasks/TASK-OPENROUTER-JANUS-CHAT-PROVIDER.3_FINAL_AUDIT.md`, `documentation/tasks/TASK-OPENROUTER-JANUS-CHAT-PROVIDER.3_AUDIT_PACKAGE.md`, `documentation/tasks/TASK-OPENROUTER-JANUS-CHAT-PROVIDER.4_FINAL_AUDIT.md`, `documentation/tasks/TASK-OPENROUTER-JANUS-CHAT-PROVIDER.4_AUDIT_PACKAGE.md`, `documentation/tasks/TASK-OPENROUTER-JANUS-CHAT-PROVIDER.5_FINAL_AUDIT.md`, `documentation/tasks/TASK-OPENROUTER-JANUS-CHAT-PROVIDER.5_AUDIT_PACKAGE.md`, `documentation/tasks/TASK-OPENROUTER-JANUS-CHAT-PROVIDER.6_FINAL_AUDIT.md`, `documentation/tasks/TASK-OPENROUTER-JANUS-CHAT-PROVIDER.6_AUDIT_PACKAGE.md`, `documentation/test-results/TEST-RUN-2026-07-17-008_results.md`, `documentation/test-results/TASK-OPENROUTER-JANUS-CHAT-PROVIDER.6_certification_evidence.md`
- **Open Tasks:** none
- **Production State:** ENABLED for the four audit-approved exact OpenRouter models when a `VALID` OpenRouter key is present; other providers unchanged
- **Spec Done Move:** MOVED `2026-07-18` to `documentation/SPEC/Spec Done/OPENROUTER_JANUS_CHAT_PROVIDER_FEATURE_SPEC.md`
- **Final Audit:** PASS WITH FIXES
- **Completed At:** 2026-07-18

## FEATURE IDENTITY
- Feature Name: OpenRouter als Janus-Chatprovider mit zertifizierten Modellen
- Feature ID: OPENROUTER-JANUS-CHAT-PROVIDER
- Decision Source: LATEST DECISION SUMMARY - OPENROUTER JANUS CHAT PROVIDER
- Primary Goal: Einen eigenen OpenRouter-API-Key für ausgewählte Claude-, GLM-, DeepSeek- und Qwen-Modelle mit vollständiger Janus-Funktion nutzbar machen.
- Routing Scope: Full Feature Pipeline

## USER VALUE

Nutzer erhalten mit einem zusätzlichen, sicher gespeicherten OpenRouter-Key Zugriff auf ausgewählte Modelle aus vier Modellfamilien. Janus behält dabei die Kontrolle über Verlauf, Redaction, Skills, Tools, Berechtigungen, bewusste Auswahl sowie die nachvollziehbare Anzeige tatsächlicher Nutzung und Kosten.

## TARGET SURFACE
- Primary Surface: Bestehendes Provider- und Modell-Dropdown im Janus-Chat
- Secondary Surface: Bestehender Bereich für Provider-Keys in den Janus-Einstellungen
- Telemetry Surface: Bestehender DeepDive
- Surface Status: Bestehende Oberflächen werden um OpenRouter ergänzt
- Existing Provider Impact: Bestehende Provider und Modelle bleiben unverändert
- Existence Confirmation: Provider-/Modell-Dropdowns, Settings-Keyflächen, DeepDive und OpenRouter-Runtime-Grundlage sind im Repository verifiziert; der OpenRouter-Chatprovider ist neu

## USER ACTION SURFACE
- Credential Actions: OpenRouter-Key sicher speichern, ersetzen und ausschließlich für OpenRouter löschen
- Provider Action: OpenRouter manuell im bestehenden Provider-Dropdown wählen
- Model Action: Ein sichtbares, vollständig zertifiziertes OpenRouter-Modell manuell im bestehenden Modell-Dropdown wählen
- Inspection Action: Tatsächlichen Verbrauch und tatsächliche Kosten eines OpenRouter-Turns im bestehenden DeepDive nachvollziehen
- Settings Availability: OpenRouter bleibt in den Einstellungen sichtbar, auch wenn die Chat-Auswahl wegen fehlender Voraussetzungen gesperrt ist

## SYSTEM BEHAVIOR

Janus ergänzt OpenRouter als eigenständigen, optionalen Chatprovider. OpenRouter wird im Chat nur auswählbar, wenn ein eigener OpenRouter-Key den Status `VALID` hat und mindestens ein vollständig Janus-zertifiziertes, exakt versioniertes Modell bereitsteht. Ein gespeicherter oder ersetzter Key wird ohne Chatinhalt über den authentifizierten OpenRouter-Key-Status geprüft. Nur erfolgreiche Authentifizierung setzt `VALID`; eine Authentifizierungsablehnung setzt `INVALID`, eine technisch nicht abgeschlossene Prüfung setzt `UNVERIFIED`. Nur `VALID` erfüllt die Chat-Voraussetzung.

Der erste Zertifizierungskandidatensatz enthält genau je ein Modell aus den Familien Claude, GLM, DeepSeek und Qwen. Konkrete Modell-IDs werden ausschließlich als exakt versionierte, geprüfte Janus-Update-Inhalte ausgeliefert. Nicht exakt identifizierbare Bezeichnungen, veraltete Beispiel-Slugs und `latest`-Aliase begründen keine Sichtbarkeit. Der Provider darf starten, sobald mindestens einer der vier Kandidaten die vollständige Janus-Zertifizierung bestanden hat; nur bestandene Modelle werden angezeigt.

Vollständig zertifiziert ist ein Modell ausschließlich dann, wenn alle Pflichtfälle der im selben geprüften Janus-Update benannten, versionierten Zertifizierungsbatterie bestanden sind, die zugehörige Test- und Audit-Evidenz vollständig bestanden ist und der ausgelieferte Zertifizierungsdatensatz exakt die Modell-ID, konkrete Modellversion und Batterieversion als bestanden markiert. Dieser ausgelieferte Zertifizierungsdatensatz ist die alleinige Laufzeitautorität. Fehlt er oder weicht einer der drei Bindungswerte ab, gilt das Modell als nicht zertifiziert und bleibt verborgen.

Für OpenRouter gelten dieselbe Janus-Redaction, derselbe notwendige Gesprächskontext, dieselben Skills und Tools sowie dieselben Berechtigungs- und Bestätigungsregeln wie für andere externe API-Key-Provider. Der Nutzer wählt Provider und konkretes Modell immer bewusst; Janus nimmt keine automatische Modellwahl vor.

Bei fehlendem, `INVALID` oder `UNVERIFIED` markiertem Key, fehlendem zertifiziertem Modell, nicht mehr verfügbarer oder nicht mehr eindeutig identifizierbarer Modellversion sowie bei Provider- oder Modellfehlern verhält sich Janus fail-closed. Nur der aktuelle Turn endet. Janus wiederholt den Turn nicht automatisch, überträgt ihn nicht doppelt und wechselt weder zu einem anderen OpenRouter-Modell noch zu einem anderen Provider. Eine vorübergehende Provider-, Netzwerk- oder Modellstörung macht einen zuvor `VALID` bestätigten Key nicht automatisch ungültig.

Wird ein zuvor gültiger Key `INVALID` oder das ausgewählte Modell nicht mehr verfügbar beziehungsweise nicht mehr zertifiziert, bleiben `OpenRouter` und das konkrete Modell sichtbar ausgewählt, aber deaktiviert. Senden bleibt gesperrt, bis dieselbe Auswahl wieder alle Voraussetzungen erfüllt oder der Nutzer bewusst eine andere gültige Auswahl trifft. Janus löscht die Auswahl nicht automatisch.

DeepDive ordnet ausschließlich von OpenRouter tatsächlich gelieferte Nutzungs- und Kostenwerte dem Provider `OpenRouter`, dem Janus-Turn und dem konkreten Modell zu. Für Chat-Completions gilt folgende autoritative Zuordnung: `response.model` zur konkreten Modell-ID; `usage.prompt_tokens` zu Eingabetokens; `usage.completion_tokens` zu Ausgabetokens; `usage.total_tokens` zu Gesamttokens; `usage.prompt_tokens_details.cached_tokens` zu gelesenen Cache-Tokens; `usage.prompt_tokens_details.cache_write_tokens` zu geschriebenen Cache-Tokens; `usage.completion_tokens_details.reasoning_tokens` zu Reasoning-Tokens; `usage.cost` zum tatsächlich belasteten Gesamtwert in OpenRouter-Credits; `usage.cost_details.upstream_inference_cost` zu den tatsächlichen Upstream-Inferenzkosten. Fehlende optionale Werte bleiben einzeln sichtbar als `nicht verfügbar`; Janus berechnet oder schätzt sie nicht und nimmt keine lokale Währungsumrechnung vor. Ein fachlich erfolgreicher Turn bleibt erfolgreich, wenn einzelne Nutzungs- oder Kostenwerte fehlen. Weicht `response.model` von der bewusst ausgewählten exakt versionierten Modell-ID ab, gilt der Turn als Modellfehler und endet fail-closed.

## DATA / PERSISTENCE
- Credential Storage: Der OpenRouter-Key wird dauerhaft im bestehenden sicheren Keyring gespeichert
- Credential Namespace: OpenRouter verwendet einen eigenen, von allen anderen Provider-Credentials getrennten Namensraum
- Credential Isolation: Speichern, Ersetzen oder Löschen des OpenRouter-Keys beeinflusst keine anderen Provider-Keys
- Key Validity State: Nur eine erfolgreiche inhaltsfreie authentifizierte Key-Prüfung setzt `VALID`; Authentifizierungsablehnung setzt `INVALID`, eine technisch nicht abgeschlossene Prüfung setzt `UNVERIFIED`
- Key Eligibility: Nur `VALID` entsperrt OpenRouter im Chat; `INVALID` und `UNVERIFIED` bleiben fail-closed, ohne den gespeicherten Key automatisch zu löschen
- Certified Model Source: Zertifizierte, exakt versionierte Modell-IDs werden ausschließlich über geprüfte Janus-Updates ausgeliefert
- Certification Authority: Allein der ausgelieferte Zertifizierungsdatensatz des geprüften Janus-Updates bestimmt die Laufzeitsichtbarkeit
- Certification Binding: Der Datensatz bindet bestandenen Status, exakte Modell-ID, konkrete Modellversion und Batterieversion an vollständig bestandene Pflicht-Test- und Audit-Evidenz
- Selection Persistence: Eine ungültig gewordene Provider-/Modellauswahl bleibt sichtbar gespeichert, aber deaktiviert; automatische Löschung oder Ersatzwahl findet nicht statt
- DeepDive Identity: Jeder Datensatz bindet Provider `OpenRouter`, Janus-Turn und `response.model`
- DeepDive Tokens: `prompt_tokens`, `completion_tokens`, `total_tokens`, `cached_tokens`, `cache_write_tokens` und `reasoning_tokens` werden nur aus den gleichnamigen OpenRouter-Usage-Feldern übernommen
- DeepDive Costs: `usage.cost` wird als belasteter Gesamtwert in OpenRouter-Credits und `upstream_inference_cost` als Upstream-Inferenzkosten übernommen; keine lokale Währungsumrechnung
- Missing Telemetry: Jedes nicht gelieferte optionale Feld wird einzeln als `nicht verfügbar` gespeichert oder dargestellt und weder berechnet noch geschätzt

## CONSTRAINTS

OpenRouter ist ein zusätzlicher, isolierter API-Key-Provider und ersetzt keinen bestehenden Provider. Die normale Chat-Auswahl enthält nur vollständig Janus-zertifizierte Modelle mit exakt versionierten IDs. Weder ein vollständiger OpenRouter-Katalog noch eingeschränkte, experimentelle oder uneindeutig versionierte Modelle dürfen in dieser Auswahl erscheinen.

Eine Änderung der Modell-ID, der konkreten Modellversion oder der Zertifizierungsbatterie invalidiert den vorhandenen Zertifizierungsdatensatz und entzieht die Sichtbarkeit, bis das betroffene Modell durch einen späteren geprüften Janus-Update-Stand erneut vollständig zertifiziert ist. Release oder Produktionsaktivierung erfordern vollständig bestandene Pflicht-Test- und Audit-Evidenz und sind nicht durch diese Spec allein freigegeben.

## SECURITY / PRIVACY
- Redaction Boundary: OpenRouter verwendet dieselbe Janus-Redaction wie andere externe API-Key-Provider
- Context Boundary: Nur der für den Turn notwendige Gesprächskontext wird nach den bestehenden Janus-Regeln übertragen
- Tool and Skill Boundary: Bestehende Janus-Skills, Tools, Berechtigungen und Bestätigungsregeln bleiben maßgeblich
- Credential Isolation: OpenRouter-Credentials und OpenRouter-Aktionen beeinflussen keine Credentials anderer Provider
- Privacy Transparency: Die Datenschutzinformation nennt ausdrücklich, dass Inhalte über OpenRouter an den ausgewählten Modellanbieter gelangen können
- Failure Safety: Fehler führen zu keinem automatischen Retry, keiner doppelten Übertragung und keinem Modell- oder Provider-Fallback
- Model Trust Boundary: Nur vollständig zertifizierte, exakt versionierte Modell-IDs sind im normalen Chat sichtbar

## EDGE CASES

- Ohne gültigen OpenRouter-Key bleibt die OpenRouter-Verwaltung in den Einstellungen sichtbar, die Chat-Auswahl jedoch gesperrt.
- Wenn eine Key-Prüfung technisch nicht abgeschlossen werden kann, bleibt der Key `UNVERIFIED` und die Chat-Auswahl fail-closed gesperrt.
- Wenn OpenRouter einen zuvor bestätigten Key bei einer authentifizierten Prüfung oder Anfrage ablehnt, wechselt der Key auf `INVALID`; Provider und Modell bleiben sichtbar ausgewählt, aber deaktiviert.
- Eine vorübergehende Provider-, Netzwerk- oder Modellstörung ändert einen zuvor bestätigten Key nicht von `VALID` zu `INVALID`; nur der aktuelle Turn endet fail-closed.
- Mit gültigem Key, aber ohne vollständig zertifiziertes Modell bleibt die Chat-Auswahl gesperrt.
- Wenn nur einer der vier initialen Familienkandidaten die vollständige Zertifizierung besteht, darf OpenRouter mit genau den bestandenen Modellen starten; nicht bestandene Kandidaten bleiben verborgen.
- Wenn eine Modell-ID, konkrete Version oder Zertifizierungsbatterie geändert wird, bleibt das Modell bis zur erneuten vollständigen Zertifizierung durch einen geprüften Janus-Update-Stand verborgen.
- Wenn ein ausgewähltes Modell nicht mehr verfügbar, nicht mehr zertifiziert oder nicht mehr eindeutig identifizierbar ist, bleibt es sichtbar ausgewählt, aber deaktiviert; nur der aktuelle Turn endet fail-closed, bis dieselbe Auswahl wieder gültig ist oder der Nutzer bewusst neu wählt.
- Wenn `response.model` nicht exakt der bewusst ausgewählten versionierten Modell-ID entspricht, gilt der Turn als Modellfehler und endet ohne automatische Wiederholung oder Ersatzwahl.
- Wenn OpenRouter einen Provider- oder Modellfehler meldet, gibt es keinen automatischen Retry, keine doppelte Übertragung und keinen automatischen Wechsel.
- Wenn ein fachlich erfolgreicher Turn keine vollständigen Nutzungs- oder Kostenwerte enthält, bleibt der Turn erfolgreich und DeepDive zeigt jedes fehlende Feld als `nicht verfügbar`.
- Das Ersetzen oder Löschen des OpenRouter-Keys verändert keine Credentials oder Auswahlzustände anderer Provider.

## DEFINITION OF DONE

- [ ] Wenn ein Nutzer einen gültigen OpenRouter-Key sicher speichert und mindestens ein exakt versioniertes Modell vollständig zertifiziert ist, dann ist OpenRouter im bestehenden Chat-Provider-Dropdown auswählbar.
- [ ] Wenn ein Nutzer einen Key speichert oder ersetzt, dann entsperrt Janus OpenRouter erst nach erfolgreicher inhaltsfreier authentifizierter Key-Prüfung mit Status `VALID`.
- [ ] Wenn eine Key-Prüfung authentifiziert abgelehnt oder technisch nicht abgeschlossen wird, dann steht der Key auf `INVALID` beziehungsweise `UNVERIFIED` und Senden bleibt fail-closed gesperrt.
- [ ] Wenn OpenRouter auswählbar ist, dann zeigt das bestehende Modell-Dropdown ausschließlich vollständig zertifizierte Modelle und keine `latest`-Aliase, veralteten Beispiel-Slugs oder nicht bestandenen Kandidaten.
- [ ] Wenn der initiale Kandidatensatz bereitgestellt wird, dann enthält er genau je ein exakt versioniertes Modell aus Claude, GLM, DeepSeek und Qwen.
- [ ] Wenn mindestens ein Kandidat die vollständige Janus-Zertifizierung besteht, dann kann OpenRouter mit den bestandenen Modellen starten, ohne auf das Bestehen der übrigen Kandidaten zu warten.
- [ ] Wenn ein Nutzer OpenRouter und ein sichtbares Modell manuell wählt, dann verarbeitet Janus den Turn mit derselben Redaction, demselben notwendigen Kontext und denselben Skill-, Tool-, Berechtigungs- und Bestätigungsregeln wie bei anderen externen API-Key-Providern.
- [ ] Wenn ein OpenRouter-Turn tatsächliche Nutzungs- oder Kostenwerte liefert, dann zeigt und speichert DeepDive sie getrennt nach Provider, konkretem Modell und Turn.
- [ ] Wenn bei einem fachlich erfolgreichen Turn einzelne Nutzungs- oder Kostenwerte fehlen, dann bleibt der Turn erfolgreich und jedes fehlende Feld erscheint als `nicht verfügbar`, ohne lokale Schätzung.
- [ ] Wenn Key, Zertifizierung oder eindeutige Modellversion fehlt oder ein Provider-/Modellfehler eintritt, dann endet nur der aktuelle Turn fail-closed ohne automatischen Retry, doppelte Übertragung oder Modell-/Provider-Fallback.
- [ ] Wenn der OpenRouter-Key gespeichert, ersetzt oder gelöscht wird, dann bleibt er sicher im eigenen Namensraum isoliert und andere Provider-Credentials bleiben unverändert.
- [ ] Wenn OpenRouter-Inhalte verarbeitet, dann informiert die Datenschutzinformation ausdrücklich über die mögliche Weitergabe über OpenRouter an den ausgewählten Modellanbieter.
- [ ] Wenn Modell-ID, konkrete Version oder Zertifizierungsbatterie geändert wird, dann bleibt das Modell verborgen, bis ein geprüfter Janus-Update-Stand die erneute vollständige Zertifizierung ausliefert.
- [ ] Wenn kein gültiger Key oder kein zertifiziertes Modell vorhanden ist, dann bleibt OpenRouter in den Einstellungen verwaltbar, während die Chat-Auswahl sichtbar gesperrt ist.
- [ ] Wenn ein zuvor gültiger Key ungültig wird oder das ausgewählte Modell seine Verfügbarkeit oder Zertifizierung verliert, dann bleiben Provider und Modell sichtbar ausgewählt, aber deaktiviert, ohne automatische Löschung oder Ersatzwahl.
- [ ] Wenn ein Modell als vollständig zertifiziert sichtbar wird, dann bindet der ausgelieferte Zertifizierungsdatensatz exakt Modell-ID, Modellversion und Batterieversion an vollständig bestandene Pflicht-Test- und Audit-Evidenz.
- [ ] Wenn OpenRouter Usage-Daten liefert, dann ordnet DeepDive jedes vorhandene autoritative Token- und Kostenfeld dem konkreten Janus-Turn zu und kennzeichnet jedes fehlende optionale Feld einzeln als `nicht verfügbar`.
- [ ] Wenn `response.model` von der bewusst ausgewählten exakt versionierten Modell-ID abweicht, dann endet der Turn fail-closed als Modellfehler ohne Retry oder Fallback.

## TEST STRATEGY
- Credential Lifecycle: Sicheres Speichern, Ersetzen und OpenRouter-exklusives Löschen, inhaltsfreie Prüfung, Zustände `VALID`/`INVALID`/`UNVERIFIED` sowie Isolation zu anderen Provider-Keys werden geprüft
- Provider Availability: Sichtbarkeit in den Einstellungen und gesperrte oder freigegebene Chat-Auswahl bei allen Kombinationen aus Key- und Zertifizierungsstatus werden geprüft
- Candidate Set: Genau je ein exakt versionierter Kandidat aus Claude, GLM, DeepSeek und Qwen sowie Providerstart ab dem ersten vollständig bestandenen Kandidaten werden geprüft
- Certification Gate: Vollständige Pflicht-Test- und Audit-Evidenz, autoritativer Zertifizierungsdatensatz sowie Invalidierung bei fehlender oder abweichender Modell-ID, Modellversion oder Batterieversion werden geprüft
- Janus Function Parity: Redaction, notwendiger Kontext, Skills, Tools, Berechtigungen und Bestätigungsregeln werden für jedes sichtbare Modell gegen die vollständige Janus-Zertifizierung geprüft
- Failure Semantics: Fehlender oder ungültiger Key, Provider-/Modellfehler und Modellverlust beenden nur den aktuellen Turn ohne Retry, Doppelübertragung oder Fallback
- Selection State: Key- oder Modellverlust erhält die sichtbare Auswahl deaktiviert; Wiederfreigabe derselben Auswahl und bewusste Neuwahl werden ohne automatische Löschung oder Ersatzwahl geprüft
- DeepDive Truthfulness: Die festgelegten Response-/Usage-Felder werden einzeln korrekt attribuiert; fehlende Werte erscheinen als `nicht verfügbar` und werden weder berechnet, geschätzt noch lokal umgerechnet
- Model Identity: Eine Abweichung zwischen bewusst ausgewählter Modell-ID und `response.model` wird als fail-closed Modellfehler geprüft
- Privacy and Isolation: Datenschutzhinweis, Credential-Namensraum und Unverändertheit bestehender Provider werden geprüft

## OUT OF SCOPE

Vollständiger oder automatisch importierter OpenRouter-Modellkatalog; eingeschränkte oder experimentelle Modelle in der normalen Chat-Auswahl; automatische Modellwahl oder MOA-Routing zwischen OpenRouter-Modellen; Laufzeit-Zertifizierung; `latest`-Aliase; lokale Kostenschätzungen; automatische Wiederholung oder Fallback; Änderungen an bestehenden Provider-Credentials; OpenRouter als Ersatz für Embeddings; Release oder Produktionsaktivierung ohne vollständige Test- und Audit-Evidenz.

## INTERNAL COMPLEXITY BREAKDOWN

- Scope Size: 17
- Architectural Risk: 18
- State / Persistence Complexity: 16
- Cross-System Dependencies: 19
- Ambiguity Level: 10
- Total Complexity Score: 80
- Routing Decision: 5.6 Sol
- Routing Reasoning: high
- Routing Confidence: HIGH
- Dashboard Hint: CRITICAL
