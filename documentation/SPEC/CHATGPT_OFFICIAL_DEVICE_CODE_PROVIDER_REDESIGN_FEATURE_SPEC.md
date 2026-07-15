# JANUS FEATURE SPEC - DIAMANTSTANDARD v4.4.3

## SPEC REVIEW EXECUTION ROUTING

target_skill: janus-spec-review
recommended_model: 5.6 Sol
recommended_reasoning: high
new_chat: yes
complexity_score: 76
confidence: HIGH
dashboard_hint: CRITICAL
reason: Sicherheitskritische Authentifizierung mit externer Provider-Grenze, persistenter Sitzung und verpflichtender Nichtbeeinflussungsevidenz.

## FEATURE IDENTITY

- Feature ID: CHATGPT-OFFICIAL-DEVICE-CODE-PROVIDER-REDESIGN
- Feature Name: ChatGPT über offiziellen Codex-Device-Code
- Feature Type: Neue externe Provider- und Authentifizierungsoption
- Spec Status: APPROVED - PARTIAL IMPLEMENTATION
- Decision Source: Freigegebene LATEST DECISION SUMMARY vom 2026-07-14
- Relationship: Ersatzdesign für die blockierten Browser- und gemeinsam genutzten Credential-Annahmen der bisherigen ChatGPT-Integration
- Routing Decision: FULL FEATURE PIPELINE

## USER VALUE

Janus-Nutzer können ihr ChatGPT-Konto als eigenständige Nutzungsoption zusätzlich zu vorhandenen API-Key-Anbietern verbinden. Die Anmeldung bleibt von anderen Codex- und ChatGPT-Clients getrennt, übersteht Janus-Neustarts und ermöglicht den gewohnten Providerwechsel mitten im Chat, ohne eine unsichere Ersatzlösung oder einen API-Key-Fallback einzuführen.

## TARGET SURFACE

- Primary Surface: Bestehender Anbieter- und Zugangsdatenbereich der Janus-Einstellungen
- Secondary Surface: Bestehendes Provider- und Modell-Dropdown in der Chat-Sidebar
- Existing or New: Bestehende Oberflächen mit einem separaten ChatGPT-Verbindungsbereich und einem konditionalen ChatGPT-Provider-Eintrag
- Existence Confirmation: confirmed by user
- Explicit Non-Surfaces: Keine Verwaltung anderer Codex-Clients und keine Änderung der bestehenden API-Key-Eingaben

## USER ACTION SURFACE

- Primary Action: Über „Mit ChatGPT anmelden“ den offiziellen Device-Code-Anmeldevorgang starten
- Login Feedback: Janus zeigt den laufenden Anmeldestatus sowie verständliche Abbruch- und Fehlerzustände
- Cancel Action: Eine laufende Anmeldung kann abgebrochen werden, ohne eine bestehende Janus-ChatGPT-Verbindung zu verändern
- Logout Action: „Abmelden“ beendet ausschließlich die Janus-eigene ChatGPT-Verbindung
- Account Switch Action: „Konto wechseln“ ersetzt das verbundene Konto erst nach erfolgreicher neuer Anmeldung
- Retry Action: Verbindungsstatus und aktuell nutzbare Modelle können nicht-destruktiv erneut geprüft werden
- Provider Action: ChatGPT und ein verifiziert nutzbares Modell können im bestehenden Dropdown ausgewählt und mitten im Chat gewechselt werden

## SYSTEM BEHAVIOR

- Im getrennten Zustand bietet Janus in den Einstellungen eine eigenständige ChatGPT-Anmeldung an; API-Key-Anbieter bleiben davon unabhängig.
- Die Anmeldung verwendet ausschließlich den offiziell dokumentierten Codex-Device-Code-Ablauf für eigene Clients.
- Nach erfolgreicher Anmeldung bleibt die Janus-Verbindung über Anwendungsneustarts hinweg bestehen, bis der Nutzer sie aktiv in Janus beendet oder die Janus-Sitzung extern ungültig wird.
- Ein Janus-Logout beendet und entfernt nur die Janus-eigene Verbindung. Andere Codex-, ChatGPT- und API-Key-Sitzungen bleiben unverändert.
- Beim Kontowechsel bleibt das bisherige Janus-Konto vollständig nutzbar, bis die neue Anmeldung erfolgreich abgeschlossen ist. Abbruch oder Fehler erhalten den bisherigen Zustand.
- ChatGPT erscheint nur dann als auswählbarer Provider, wenn eine gültige Janus-Verbindung besteht und mindestens ein aktuell nutzbares Modell verifiziert wurde.
- Unter ChatGPT werden ausschließlich Modelle angezeigt, deren Nutzbarkeit für die aktive Janus-Sitzung aktuell bestätigt ist.
- Kann Janus die nutzbaren Modelle nicht verifizieren, bleibt das Konto verbunden, ChatGPT ist aber nicht auswählbar. Es werden keine veralteten Modelle angeboten und die Einstellungen bieten „Erneut versuchen“ an.
- Beim Wechsel zu ChatGPT innerhalb eines bestehenden Chats übergibt Janus den für die nahtlose Fortsetzung benötigten bisherigen Gesprächskontext. Der aktive Provider bleibt sichtbar.
- Vor der ersten Übermittlung von Chat-Inhalten an ChatGPT verlangt Janus eine einmalige Datenschutzbestätigung. Eine erneute Bestätigung erfolgt nur nach einer wesentlichen Änderung der angezeigten Datenschutzinformationen.
- Die ChatGPT-Anmeldung bleibt vollständig deaktiviert, solange Janus keine nachweislich getrennte, verschlüsselte und persistente Credential-Ablage gewährleisten kann.
- Die Produktionsfreigabe bleibt gesperrt, bis die Janus-Sitzung einen frischen Zwei-Konten-Nichtbeeinflussungstest gegen einen parallel angemeldeten Codex-Client bestanden hat.

## DATA / PERSISTENCE

- Credential Ownership: Janus speichert ausschließlich die von Janus selbst aufgebaute ChatGPT-Sitzung
- Credential Storage: Separat benannter, verschlüsselter und persistenter Janus-Speicher ohne gemeinsam genutzten Codex-Credential-Slot
- Credential Lifetime: Persistenz bis zum aktiven Janus-Logout oder bis die Janus-Sitzung extern ungültig wird
- Credential Deletion: Ein Janus-Logout entfernt die Janus-eigene gespeicherte Sitzung
- Existing Credential Import: Verboten; bestehende Codex-, IDE- oder Desktop-Credentials werden weder importiert noch übernommen
- Account Cardinality: Genau ein verbundenes Janus-ChatGPT-Konto zur selben Zeit
- Privacy Acknowledgement: Speicherung der bestätigten Datenschutzinformations-Version, damit nur wesentliche Änderungen eine neue Bestätigung auslösen
- Conversation Context: Verwendung des bestehenden Janus-Chatverlaufs für den benötigten Providerwechsel-Kontext ohne separates neues Kontextarchiv
- API Key Relationship: API-Key-Daten bleiben unabhängig und sind weder Voraussetzung noch Fallback für ChatGPT

## CONSTRAINTS

- Die bestehende freie Providerwahl mitten im Chat bleibt erhalten.
- ChatGPT ist eine zusätzliche, bewusst separat gewählte Option und ersetzt keinen bestehenden Anbieter.
- Ein Authentifizierungs-, Speicher-, Modell- oder Providerfehler darf keine andere Anbieter- oder Kontositzung verändern.
- Nicht verifizierte oder veraltete Modelle dürfen nicht auswählbar sein.
- Fehlende sichere Persistenz darf nicht durch Klartextspeicherung oder eine temporäre Session-only-Anmeldung umgangen werden.
- Eine bestehende Janus-Verbindung darf durch einen fehlgeschlagenen Kontowechsel nicht verloren gehen.
- Die blockierte bisherige Browser-/Keyring-Isolationsannahme gilt nicht als Freigabeevidenz für dieses Redesign.

## SECURITY / PRIVACY

- Authentication Boundary: Ausschließlich offiziell dokumentierter Codex-App-Server-Device-Code-Ablauf
- Credential Isolation: Keine gemeinsame Credential-Ablage und keine Sitzungsteilung mit Codex Desktop, Codex CLI oder IDE-Erweiterungen
- Storage Requirement: Janus-spezifische verschlüsselte Persistenz; bei fehlender Gewährleistung fail-closed deaktiviert
- Forbidden Integration: Keine Hermes-artige direkte Nutzung privater OAuth-Clients, Token-Endpunkte oder undokumentierter ChatGPT-Backend-Endpunkte
- Secret Exposure: Tokens, Codes und gespeicherte Credentials erscheinen weder in UI-Fehlern noch in normalen Logs, Telemetrie oder Dokumentationsartefakten
- Privacy Notice: Einmalige bestätigungspflichtige Information vor der ersten ChatGPT-Inhaltsübertragung; dauerhaft in den Einstellungen einsehbar
- Context Disclosure: Bei Auswahl von ChatGPT können aktuelle Nachricht und benötigter bisheriger Gesprächskontext an den externen Provider übertragen werden
- Logout Boundary: Janus darf nur seine eigene Sitzung löschen oder ungültig machen
- Release Gate: Produktionsaktivierung erst nach bestandener automatisierter Sicherheitsprüfung und realem Zwei-Konten-Nichtbeeinflussungsnachweis
- Failure Policy: Jeder Zweifel an Speicherung, Isolation, Modellnutzbarkeit oder Sitzungszuordnung führt zu einem nicht-destruktiven fail-closed Zustand

## EDGE CASES

- Wird die erste Anmeldung abgebrochen oder schlägt sie fehl, bleibt Janus getrennt und zeigt einen nicht-sensitiven Fehler mit Wiederholungsmöglichkeit.
- Wird ein Kontowechsel abgebrochen oder schlägt er fehl, bleibt das bisherige Janus-Konto verbunden und auswählbar.
- Wird Janus während einer noch laufenden Anmeldung beendet, entsteht keine teilweise verbundene Sitzung; eine vorherige gültige Verbindung bleibt unverändert.
- Wird die Janus-Sitzung extern widerrufen oder kann sie nicht mehr erneuert werden, wird nur ChatGPT in Janus nicht verfügbar und eine erneute Anmeldung angeboten.
- Fällt die Modellprüfung aus, bleibt die Anmeldung bestehen, aber ChatGPT und alle unbestätigten Modelle sind nicht auswählbar.
- Verliert ein bereits ausgewähltes Modell seine bestätigte Nutzbarkeit, blockiert Janus die nächste Übermittlung an dieses Modell und verlangt eine neue gültige Auswahl.
- Gibt es keine nutzbaren Modelle, erscheint ChatGPT nicht als auswählbarer Provider, obwohl der verbundene Kontostatus in den Einstellungen sichtbar bleibt.
- Ein erneuter Klick während einer laufenden Anmeldung startet keinen zweiten parallelen Anmeldevorgang.
- Ein Janus-Logout, Kontowechsel oder Sitzungsfehler darf weder API-Key-Anbieter noch externe Codex- oder ChatGPT-Clients abmelden.

## DEFINITION OF DONE

- [ ] Wenn Janus getrennt ist und sichere persistente Isolation verfügbar ist, dann kann der Nutzer die offizielle Device-Code-Anmeldung in den Einstellungen starten, abbrechen und erfolgreich abschließen.
- [ ] Wenn sichere persistente Isolation nicht nachweislich verfügbar ist, dann bleibt die ChatGPT-Anmeldung deaktiviert und Janus zeigt einen verständlichen Grund ohne unsicheren Ersatzweg.
- [ ] Wenn eine Janus-Anmeldung erfolgreich war und Janus neu gestartet wird, dann bleibt ausschließlich die Janus-Verbindung erhalten und ein parallel angemeldeter Codex-Client bleibt vollständig unverändert.
- [ ] Wenn der Nutzer Janus-Logout ausführt, dann wird nur die Janus-eigene ChatGPT-Sitzung beendet und andere Codex-, ChatGPT- sowie API-Key-Sitzungen bleiben unverändert.
- [ ] Wenn ein Kontowechsel abgebrochen wird oder fehlschlägt, dann bleibt das vorherige Janus-Konto verbunden und nutzbar.
- [ ] Wenn ein Kontowechsel erfolgreich ist, dann wird erst anschließend das vorherige Janus-Konto durch das neue ersetzt.
- [ ] Wenn eine gültige Janus-Verbindung und verifiziert nutzbare Modelle vorliegen, dann erscheint ChatGPT im bestehenden Provider-Dropdown ausschließlich mit diesen Modellen.
- [ ] Wenn die Modellnutzbarkeit nicht verifiziert werden kann, dann ist ChatGPT nicht auswählbar, es erscheinen keine veralteten Modelle und die Einstellungen bieten eine nicht-destruktive Wiederholung an.
- [ ] Wenn der Nutzer mitten im Chat zu ChatGPT wechselt, dann kann die Unterhaltung mit dem benötigten bisherigen Kontext fortgesetzt werden und der aktive Provider bleibt sichtbar.
- [ ] Wenn erstmals Chat-Inhalte an ChatGPT gesendet werden sollen, dann blockiert Janus die Übertragung bis zur Datenschutzbestätigung.
- [ ] Wenn die Datenschutzinformationen unverändert bestätigt sind, dann erfolgen spätere Providerwechsel ohne erneute Bestätigung.
- [ ] Wenn sich die Datenschutzinformationen wesentlich ändern, dann verlangt Janus vor der nächsten ChatGPT-Inhaltsübertragung eine neue Bestätigung.
- [ ] Wenn Authentifizierungs- oder Modellfehler auftreten, dann enthalten UI, Logs und Evidenz keine Tokens, Device Codes oder gespeicherten Credentials.
- [ ] Wenn der verpflichtende Zwei-Konten-Test Login, Neustart, Kontowechsel und Janus-Logout prüft, dann bleiben Konto, Kontingent, Einstellungen und Sitzungszustand des separaten Codex-Clients in jedem Schritt unverändert.
- [ ] Wenn die Nichtbeeinflussungs- oder Speicherevidenz fehlt oder fehlschlägt, dann bleibt die Produktionsaktivierung gesperrt.
- [ ] Wenn vorhandene API-Key-Anbieter genutzt werden, dann verhalten sie sich vor, während und nach ChatGPT-Anmeldung, Kontowechsel und Logout unverändert.

## TEST STRATEGY

- Automated Contract Tests: Verbindungszustände, Abbruch, atomarer Kontowechsel, Janus-only Logout, Datenschutz-Gate und fail-closed Fehlerzustände
- Credential Security Tests: Janus-spezifische verschlüsselte Persistenz, getrennte Namensräume, verbotener Credential-Import und Secret-Redaktion
- Model Availability Tests: Nur aktuell verifizierte Modelle sichtbar; leere, veraltete und fehlgeschlagene Prüfungen bleiben nicht auswählbar
- Provider Regression Tests: Bestehende API-Key-Anbieter, Dropdown-Auswahl und Providerwechsel bleiben unverändert funktionsfähig
- Conversation Tests: Wechsel zu ChatGPT mitten im Chat erhält den benötigten bisherigen Kontext und zeigt den aktiven Provider korrekt an
- Settings E2E Tests: Getrennt, Anmeldung läuft, verbunden, Fehler, Wiederholung, Abmelden und Konto wechseln sind sichtbar und bedienbar
- Manual Isolation Test: Zwei unterschiedliche Konten für Janus und einen separaten Codex-Client prüfen Login, Neustart, Kontowechsel, Erneuerung und Janus-Logout ohne gegenseitige Beeinflussung
- Release Evidence: Produktionsfreigabe nur mit reproduzierbaren automatisierten Ergebnissen und dokumentiert bestandenem Zwei-Konten-Test

## OUT OF SCOPE

- Mehrere gleichzeitig gespeicherte oder parallel auswählbare ChatGPT-Konten
- Änderungen am bestehenden API-Key-System oder automatische API-Key-Ersatzwege
- Import, Kopie oder gemeinsame Nutzung vorhandener Codex-, IDE- oder Desktop-Credentials
- Direkte Nutzung undokumentierter OAuth-Clients, Token-Endpunkte oder ChatGPT-Backend-Endpunkte
- Verwaltung, Abmeldung oder Reparatur anderer Codex- und ChatGPT-Clients durch Janus
- Bereinigung der aus dem abgebrochenen Isolationstest verbliebenen kontrollierten Test-Credentials
- Erweiterung auf andere neue OAuth-Provider
- Release, Veröffentlichung oder Aktivierung ohne die festgelegte Sicherheits- und Isolationsevidenz

## INTERNAL COMPLEXITY BREAKDOWN

- Scope Size: 17
- Architectural Risk: 19
- State / Persistence Complexity: 18
- Cross-System Dependencies: 18
- Ambiguity Level: 4
- Total Complexity Score: 76
- Routing Decision: 5.6 Sol
- Routing Reasoning: high
- Routing Confidence: HIGH
- Dashboard Hint: CRITICAL

## SPEC REVIEW METADATA

- **Review Status:** APPROVED
- **Complexity Score:** 76
- **Risk:** HIGH
- **Recommended Review Model:** 5.6 Sol
- **Skill-1 Ready:** YES
- **Split Required:** NO
- **Reviewed At:** 2026-07-14
- **Review Confidence:** HIGH
- **Review Source:** janus-spec-review

## PARTIAL IMPLEMENTATION METADATA

### TASK-CHATGPT-DEVICE-CODE-PROVIDER.1

- **Implementation Status:** DONE
- **Final Audit:** PASS
- **Completed At:** 2026-07-15
- **Scope:** Official App Server device-code lifecycle, Janus-only encrypted credential persistence, redaction, restart persistence, Janus-only logout, and controlled two-account non-interference evidence.
- **Validation:** Backend lifecycle `22 passed`; Electron runtime-boundary `9 passed`; headed Settings regression `4 passed`; Python compile and scoped diff check PASS; controlled two-account evidence PASS.
- **Evidence:** `documentation/tasks/TASK-CHATGPT-DEVICE-CODE-PROVIDER.1_final_audit.md`; `documentation/tasks/TASK-CHATGPT-DEVICE-CODE-PROVIDER.1_AUDIT_PACKAGE.md`; `documentation/test-results/TASK-CHATGPT-DEVICE-CODE-PROVIDER.1_isolation_evidence.md`
- **Remaining Work:** Tasks `.2` through `.5` remain open. The Feature Spec is not DONE and production remains default-deny.
