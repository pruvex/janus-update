# JANUS FEATURE SPEC - DIAMANTSTANDARD v4.4.3

## SPEC REVIEW EXECUTION ROUTING

target_skill: janus-spec-review
recommended_model: 5.6 Sol
recommended_reasoning: high
new_chat: yes
complexity_score: 78
confidence: HIGH
dashboard_hint: CRITICAL
reason: Sicherheitskritische Providergrenze bleibt bis zu offizieller Dynamic-Tools-only-Unterstützung blockiert und erfordert erneute unabhängige Prüfung.

## FEATURE IDENTITY

- Feature ID: CHATGPT-OFFICIAL-DEVICE-CODE-PROVIDER-REDESIGN
- Feature Name: ChatGPT über offiziellen Codex-Device-Code
- Feature Type: Neue externe Provider- und Authentifizierungsoption
- Spec Status: DRAFT AMENDMENT - PARTIAL IMPLEMENTATION
- Decision Source: Freigegebene LATEST DECISION SUMMARY vom 2026-07-14; Task-.4-Ergänzung in `documentation/tasks/TASK-CHATGPT-DEVICE-CODE-PROVIDER.4_decision_summary.md`; gelockte Upstream-Warteentscheidung in `documentation/tasks/TASK-CHATGPT-DEVICE-CODE-PROVIDER.4_upstream_wait_decision_summary.md` vom 2026-07-16
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
- Turn Cancel Action: Ein laufender ChatGPT-Turn kann abgebrochen werden, ohne Janus-Verlauf, Entwurf, Providerwahl oder Anmeldung zu verändern
- Tool Feedback: Sichtbar bleiben ausschließlich das gewohnte Antwort-Streaming und Janus-kontrollierte Toolstatus; interne Codex-Agentenereignisse erhalten keine eigene Oberfläche

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
- ChatGPT verhält sich im Janus-Chat wie ein textbasierter API-Key-Provider: Janus stellt den benötigten redigierten Kontext zusammen, verarbeitet die Textantwort und bleibt alleinige Gesprächsquelle.
- Jeder ChatGPT-Turn verwendet einen neuen temporären App-Server-Gesprächskontext. Janus führt keinen dauerhaften oder parallelen Codex-Verlauf.
- ChatGPT kann dieselben von Janus freigegebenen Skills und Tools anfordern wie bestehende Provider. Ausschließlich Janus prüft und führt diese mit den bestehenden Berechtigungs-, Bestätigungs- und Sicherheitsregeln aus.
- Der experimentelle App-Server-Vertrag für Janus-eigene Client-Tools ist ausdrücklich zulässig, solange Janus vor der Nutzung die erwartete Laufzeitverträglichkeit eindeutig bestätigt.
- Fehlt die erwartete Client-Tool-Unterstützung, weicht der Vertrag ab oder kann die Nichtausführung Codex-eigener Aktionen nicht nachgewiesen werden, bleibt ChatGPT vollständig nicht nutzbar. Ein reduzierter textbasierter Ersatzmodus ist nicht zulässig.
- Der aktuell gebundene offizielle Runtime-Stand erfüllt diese Grenze nicht, weil mindestens das Codex-native Tool `update_plan` nicht vor dem Modelldispatch entfernt werden kann. Task `.4` bleibt deshalb blockiert und darf nicht implementiert werden.
- Janus wartet auf einen offiziellen Runtime-Stand mit nachweisbarem Dynamic-Tools-only-Modus oder vollständiger Core-Tool-Allowlist. Erst account-freie ausführbare Evidenz gegen genau diesen Stand und ein anschließend grüner Precheck dürfen Task `.4` wieder freigeben.
- Janus verfolgt weder eine eigene gepatchte oder geforkte Codex-Runtime noch eine Zulassung des unvermeidbaren nativen Planungstools als Ersatzentscheidung.
- Codex-eigene Tool-, Befehls-, Datei-, Approval- oder sonstige Agent-Aktionen werden nicht ausgeführt. Eine solche Anforderung beendet nur den betroffenen ChatGPT-Turn fail-closed mit einer verständlichen Meldung.
- Antwort-Streaming und Toolstatus folgen der bestehenden Janus-Darstellung; interne Codex-Fortschritts- und Agentenereignisse werden nicht als zweite Agentenoberfläche dargestellt.
- Vor der ersten Übermittlung von Chat-Inhalten an ChatGPT verlangt Janus eine einmalige Datenschutzbestätigung. Eine erneute Bestätigung erfolgt nur nach einer wesentlichen Änderung der angezeigten Datenschutzinformationen.
- Bei Ablehnung oder Schließen der Datenschutzbestätigung wird nichts übertragen; Entwurf und Providerwahl bleiben erhalten und es erfolgt kein automatischer Fallback.
- Ein Transportfehler oder Nutzerabbruch bleibt auf den aktuellen temporären ChatGPT-Turn begrenzt. Es gibt keine automatische Wiederholung und keinen automatischen Providerwechsel.
- Die ChatGPT-Anmeldung bleibt vollständig deaktiviert, solange Janus keine nachweislich getrennte, verschlüsselte und persistente Credential-Ablage gewährleisten kann.
- Die Produktionsfreigabe bleibt gesperrt, bis Task `.5` zusätzlich zum frischen Zwei-Konten-Nichtbeeinflussungstest die erwartete Client-Tool-Vertragskompatibilität und die harte Nichtausführung Codex-eigener Aktionen nachgewiesen hat.

## DATA / PERSISTENCE

- Credential Ownership: Janus speichert ausschließlich die von Janus selbst aufgebaute ChatGPT-Sitzung
- Credential Storage: Separat benannter, verschlüsselter und persistenter Janus-Speicher ohne gemeinsam genutzten Codex-Credential-Slot
- Credential Lifetime: Persistenz bis zum aktiven Janus-Logout oder bis die Janus-Sitzung extern ungültig wird
- Credential Deletion: Ein Janus-Logout entfernt die Janus-eigene gespeicherte Sitzung
- Existing Credential Import: Verboten; bestehende Codex-, IDE- oder Desktop-Credentials werden weder importiert noch übernommen
- Account Cardinality: Genau ein verbundenes Janus-ChatGPT-Konto zur selben Zeit
- Privacy Acknowledgement: Speicherung der bestätigten Datenschutzinformations-Version, damit nur wesentliche Änderungen eine neue Bestätigung auslösen
- Conversation Context: Verwendung des bestehenden Janus-Chatverlaufs für den benötigten Providerwechsel-Kontext ohne separates neues Kontextarchiv
- App Server Conversation: Pro Turn nur temporär; keine persistierte Codex-Thread-ID und keine zweite Gesprächshistorie
- Tool Context: Erforderliche Janus-/Skill-Anweisungen, Tool-Eingaben und Tool-Ergebnisse dürfen nur als Teil des für denselben Turn benötigten redigierten Janus-Kontexts übertragen werden
- API Key Relationship: API-Key-Daten bleiben unabhängig und sind weder Voraussetzung noch Fallback für ChatGPT

## CONSTRAINTS

- Die bestehende freie Providerwahl mitten im Chat bleibt erhalten.
- ChatGPT ist eine zusätzliche, bewusst separat gewählte Option und ersetzt keinen bestehenden Anbieter.
- Ein Authentifizierungs-, Speicher-, Modell- oder Providerfehler darf keine andere Anbieter- oder Kontositzung verändern.
- Nicht verifizierte oder veraltete Modelle dürfen nicht auswählbar sein.
- Fehlende sichere Persistenz darf nicht durch Klartextspeicherung oder eine temporäre Session-only-Anmeldung umgangen werden.
- Eine bestehende Janus-Verbindung darf durch einen fehlgeschlagenen Kontowechsel nicht verloren gehen.
- Janus bleibt alleinige Tool-, Berechtigungs-, Redaktions- und Ausführungsgrenze; ChatGPT erhält weder Sonderrechte noch Zugriff auf Codex-eigene Aktionsflächen.
- Die experimentelle Client-Tool-Abhängigkeit ist nur in der nachweislich erwarteten Vertragsform zulässig; fehlende Prüfbarkeit oder Vertragsdrift führt vor jeder ChatGPT-Nutzung zur vollständigen Nichtverfügbarkeit.
- Eine reine Prompt-Anweisung, das Verbergen interner Ereignisse oder das nachträgliche Ignorieren einer Aktion gilt nicht als Nachweis, dass Codex-eigene Aktionen nicht ausgeführt werden können.
- Ein bloßes offizielles Versionsupdate, ein vorhandenes experimentelles Client-Tool-Feld oder eine teilweise Reduzierung nativer Tools gilt nicht als Freigabe. Die vollständige Janus-only Toolgrenze muss für den exakt gebundenen Runtime-Stand erneut account-frei und ausführbar nachgewiesen werden.
- Eine von Janus gepatchte oder geforkte Codex-Runtime und die Zulassung des Codex-nativen `update_plan`-Tools sind keine erlaubten Umgehungswege.
- Unerlaubte Codex-Agentenaktionen dürfen weder stillschweigend ignoriert noch als erfolgreicher Turn behandelt werden.
- Fehler, Ablehnung und Abbruch dürfen keine automatische Wiederholung, keine doppelte Inhaltsübertragung und keinen automatischen Wechsel zu einem API-Key-Provider auslösen.
- Die blockierte bisherige Browser-/Keyring-Isolationsannahme gilt nicht als Freigabeevidenz für dieses Redesign.

## SECURITY / PRIVACY

- Authentication Boundary: Ausschließlich offiziell dokumentierter Codex-App-Server-Device-Code-Ablauf
- Credential Isolation: Keine gemeinsame Credential-Ablage und keine Sitzungsteilung mit Codex Desktop, Codex CLI oder IDE-Erweiterungen
- Storage Requirement: Janus-spezifische verschlüsselte Persistenz; bei fehlender Gewährleistung fail-closed deaktiviert
- Forbidden Integration: Keine Hermes-artige direkte Nutzung privater OAuth-Clients, Token-Endpunkte oder undokumentierter ChatGPT-Backend-Endpunkte
- Secret Exposure: Tokens, Codes und gespeicherte Credentials erscheinen weder in UI-Fehlern noch in normalen Logs, Telemetrie oder Dokumentationsartefakten
- Privacy Notice: Einmalige bestätigungspflichtige Information vor der ersten ChatGPT-Inhaltsübertragung; sie nennt aktuelle Nachricht, benötigten Verlauf, Janus-/Skill-Anweisungen sowie erforderliche Tool-Eingaben und -Ergebnisse und bleibt in den Einstellungen einsehbar
- Context Disclosure: Bei Auswahl von ChatGPT darf ausschließlich der für den Turn benötigte, von Janus zusammengestellte und redigierte Kontext an den externen Provider übertragen werden
- Tool Authority: Nur Janus darf freigegebene Skills und Tools prüfen und ausführen; Codex-eigene Tools, Befehle, Dateiänderungen und Approval-Abläufe bleiben verboten
- Experimental Client Tool Contract: Ausdrücklich akzeptierte vorläufige Abhängigkeit für Janus-Toolparität; Nutzung nur bei eindeutig bestätigter Laufzeitverträglichkeit
- Contract Drift Policy: Fehlende, veränderte oder nicht prüfbare Client-Tool-Unterstützung macht ChatGPT vollständig nicht verfügbar und aktiviert keinen reduzierten Ersatzpfad
- Agent Event Policy: Interne Codex-Agentenereignisse eröffnen keine zweite Aktionsoberfläche; jede angeforderte Codex-native Aktion beendet den betroffenen Turn fail-closed
- Upstream Capability Gate: Task `.4` bleibt blockiert, bis ein offizieller Runtime-Stand einen nachweisbaren Dynamic-Tools-only-Modus oder eine vollständige Core-Tool-Allowlist bereitstellt
- Re-entry Evidence: Vor einer erneuten Implementierungsfreigabe sind account-freie ausführbare Evidenz gegen den exakten offiziellen Runtime-Stand und ein grüner Precheck erforderlich
- Runtime Ownership Boundary: Keine von Janus gepflegte, gepatchte oder geforkte Codex-Runtime und keine Zulassung von `update_plan`
- Logout Boundary: Janus darf nur seine eigene Sitzung löschen oder ungültig machen
- Release Gate: Produktionsaktivierung erst nach bestandener automatisierter Sicherheitsprüfung, realem Zwei-Konten-Nichtbeeinflussungsnachweis, bestätigter Client-Tool-Vertragskompatibilität und belegter Nichtausführung Codex-eigener Aktionen
- Failure Policy: Jeder Zweifel an Speicherung, Isolation, Modellnutzbarkeit, Sitzungszuordnung, Client-Tool-Vertrag oder harter Sperre Codex-eigener Aktionen führt zu einem nicht-destruktiven fail-closed Zustand

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
- Fordert der App Server eine Codex-eigene Tool-, Befehls-, Datei- oder Approval-Aktion an, endet nur der aktuelle Turn mit einer nicht-sensitiven Meldung; die Aktion wird nicht ausgeführt.
- Wird die Datenschutzbestätigung geschlossen oder abgelehnt, bleibt der Entwurf erhalten und es erfolgt keine externe Übertragung oder automatische Providerwahl.
- Schlägt der ChatGPT-Transport fehl, bleiben Verlauf, Entwurf, Auswahl und Anmeldung erhalten; Janus wiederholt den Turn nicht automatisch.
- Bricht der Nutzer einen laufenden ChatGPT-Turn ab, wird nur dessen externe Verarbeitung beendet; der persistente Janus-Zustand bleibt erhalten.
- Fehlt die erwartete experimentelle Client-Tool-Unterstützung oder ist ihre Vertragskompatibilität nicht eindeutig prüfbar, bleibt ChatGPT nicht auswählbar und bietet keinen textbasierten Ersatzmodus an.
- Kann Janus nicht belegen, dass Codex-eigene Aktionen vor ihrer Ausführung gesperrt sind, bleibt ChatGPT unabhängig von Anmeldung und Modellverifikation vollständig nicht nutzbar.
- Enthält ein neuer offizieller Runtime-Stand weiterhin `update_plan` oder eine andere Codex-native Aktionsoberfläche, bleibt Task `.4` blockiert, auch wenn andere Vertrags- oder Modellprüfungen grün sind.
- Bietet ein neuer offizieller Runtime-Stand nur ein experimentelles Feld ohne vollständigen ausführbaren Ausschluss nativer Aktionen, gilt die Upstream-Bedingung als nicht erfüllt.

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
- [ ] Wenn Janus einen ChatGPT-Turn startet, dann stammt der übertragene Gesprächskontext ausschließlich aus dem benötigten redigierten Janus-Verlauf und es wird keine Codex-Thread-ID dauerhaft gespeichert.
- [ ] Wenn ChatGPT ein von Janus freigegebenes Skill- oder Toolverhalten anfordert, dann prüft und verarbeitet Janus es mit denselben Regeln wie bei den bestehenden API-Key-Providern.
- [ ] Wenn die erwartete experimentelle Client-Tool-Unterstützung zur Laufzeit exakt verträglich ist, dann kann Janus ausschließlich seine freigegebenen Skills und Tools über diese Grenze anbieten.
- [ ] Wenn die Client-Tool-Unterstützung fehlt, abweicht oder nicht eindeutig prüfbar ist, dann bleibt ChatGPT vollständig nicht nutzbar und es wird kein reduzierter textbasierter Ersatzmodus aktiviert.
- [ ] Wenn der offizielle Runtime-Stand keinen nachweisbaren Dynamic-Tools-only-Modus oder keine vollständige Core-Tool-Allowlist bietet, dann bleibt Task `.4` blockiert und ChatGPT bleibt unabhängig von Anmeldung und Modellverifikation vollständig nicht nutzbar.
- [ ] Wenn ein neuer offizieller Runtime-Stand die erforderliche Grenze anbietet, dann wird Task `.4` erst nach account-freier ausführbarer Evidenz gegen genau diesen Stand und einem grünen Precheck zur Implementierung freigegeben.
- [ ] Wenn die Upstream-Fähigkeit fehlt, dann wird weder eine Janus-gepatchte Codex-Runtime eingesetzt noch das Codex-native `update_plan` als zulässige Abweichung akzeptiert.
- [ ] Wenn der App Server eine Codex-eigene Tool-, Befehls-, Datei- oder Approval-Aktion anfordert, dann wird sie nicht ausgeführt und nur der aktuelle Turn endet fail-closed mit einer verständlichen Meldung.
- [ ] Wenn die Nichtausführung Codex-eigener Aktionen nicht vor der Produktionsaktivierung nachgewiesen ist, dann bleibt ChatGPT unabhängig von anderen grünen Evidenzen default-deny.
- [ ] Wenn ein ChatGPT-Turn läuft, dann zeigt Janus nur das bestehende Antwort-Streaming und Janus-kontrollierte Toolstatus und keine interne Codex-Agentenoberfläche.
- [ ] Wenn erstmals Chat-Inhalte an ChatGPT gesendet werden sollen, dann blockiert Janus die Übertragung bis zur Datenschutzbestätigung.
- [ ] Wenn die Datenschutzinformationen unverändert bestätigt sind, dann erfolgen spätere Providerwechsel ohne erneute Bestätigung.
- [ ] Wenn sich die Datenschutzinformationen wesentlich ändern, dann verlangt Janus vor der nächsten ChatGPT-Inhaltsübertragung eine neue Bestätigung.
- [ ] Wenn der Nutzer die Datenschutzbestätigung ablehnt oder schließt, dann wird nichts an ChatGPT übertragen und Entwurf sowie Providerwahl bleiben erhalten.
- [ ] Wenn der ChatGPT-Transport fehlschlägt, dann bleiben Verlauf, Entwurf, Providerwahl und Anmeldung erhalten und Janus führt weder automatische Wiederholung noch Provider-Fallback aus.
- [ ] Wenn der Nutzer einen laufenden ChatGPT-Turn abbricht, dann endet nur dessen externe Verarbeitung und der bestehende Janus-Zustand bleibt erhalten.
- [ ] Wenn Authentifizierungs- oder Modellfehler auftreten, dann enthalten UI, Logs und Evidenz keine Tokens, Device Codes oder gespeicherten Credentials.
- [ ] Wenn der verpflichtende Zwei-Konten-Test Login, Neustart, Kontowechsel und Janus-Logout prüft, dann bleiben Konto, Kontingent, Einstellungen und Sitzungszustand des separaten Codex-Clients in jedem Schritt unverändert.
- [ ] Wenn die Nichtbeeinflussungs- oder Speicherevidenz fehlt oder fehlschlägt, dann bleibt die Produktionsaktivierung gesperrt.
- [ ] Wenn die Client-Tool-Vertrags- oder Native-Aktionssperren-Evidenz fehlt, veraltet ist oder fehlschlägt, dann bleibt die Produktionsaktivierung gesperrt.
- [ ] Wenn vorhandene API-Key-Anbieter genutzt werden, dann verhalten sie sich vor, während und nach ChatGPT-Anmeldung, Kontowechsel und Logout unverändert.

## TEST STRATEGY

- Automated Contract Tests: Verbindungszustände, Abbruch, atomarer Kontowechsel, Janus-only Logout, Datenschutz-Gate und fail-closed Fehlerzustände
- Credential Security Tests: Janus-spezifische verschlüsselte Persistenz, getrennte Namensräume, verbotener Credential-Import und Secret-Redaktion
- Model Availability Tests: Nur aktuell verifizierte Modelle sichtbar; leere, veraltete und fehlgeschlagene Prüfungen bleiben nicht auswählbar
- Provider Regression Tests: Bestehende API-Key-Anbieter, Dropdown-Auswahl und Providerwechsel bleiben unverändert funktionsfähig
- Conversation Tests: Wechsel zu ChatGPT mitten im Chat erhält den benötigten bisherigen Kontext und zeigt den aktiven Provider korrekt an
- Provider Parity Tests: ChatGPT nutzt denselben Janus-kontrollierten Skill-/Toolpfad und dieselben Berechtigungsregeln wie API-Key-Provider
- Agent Boundary Tests: Codex-eigene Tool-, Befehls-, Datei- und Approval-Anforderungen enden fail-closed und werden weder ausgeführt noch als Erfolg behandelt
- Client Tool Contract Tests: Erwartete experimentelle Unterstützung ist exakt kompatibel; fehlende, veränderte und nicht prüfbare Verträge bleiben vollständig default-deny
- Native Action Non-Execution Tests: Belegen, dass Codex-eigene Aktionen nicht vor einer Janus-Ablehnung ausgeführt werden können; Prompt- oder reine Eventfilterung genügt nicht
- Upstream Re-entry Tests: Für jeden künftig gebundenen offiziellen Runtime-Stand account-frei belegen, dass ausschließlich Janus-Client-Tools vor dem Modelldispatch angeboten werden und kein `update_plan` oder anderes Codex-natives Aktionstool verbleibt
- Ephemeral Conversation Tests: Jeder Turn verwendet nur einen temporären App-Server-Kontext; keine Codex-Thread-ID oder zweite Historie bleibt bestehen
- Transport Failure Tests: Ablehnung, Abbruch und Transportfehler erhalten den Janus-Zustand ohne Wiederholung, doppelte Übertragung oder Provider-Fallback
- Privacy Disclosure Tests: Die versionierte Information deckt Nachricht, Verlauf, Janus-/Skill-Anweisungen, Tool-Eingaben und Tool-Ergebnisse ab und blockiert vor der ersten Übertragung
- Settings E2E Tests: Getrennt, Anmeldung läuft, verbunden, Fehler, Wiederholung, Abmelden und Konto wechseln sind sichtbar und bedienbar
- Manual Isolation Test: Zwei unterschiedliche Konten für Janus und einen separaten Codex-Client prüfen Login, Neustart, Kontowechsel, Erneuerung und Janus-Logout ohne gegenseitige Beeinflussung
- Release Evidence: Produktionsfreigabe nur mit reproduzierbaren automatisierten Ergebnissen, dokumentiert bestandenem Zwei-Konten-Test, aktuellem Client-Tool-Vertragsnachweis und Native-Aktionssperren-Nachweis

## OUT OF SCOPE

- Mehrere gleichzeitig gespeicherte oder parallel auswählbare ChatGPT-Konten
- Änderungen am bestehenden API-Key-System oder automatische API-Key-Ersatzwege
- Import, Kopie oder gemeinsame Nutzung vorhandener Codex-, IDE- oder Desktop-Credentials
- Direkte Nutzung undokumentierter OAuth-Clients, Token-Endpunkte oder ChatGPT-Backend-Endpunkte
- Verwaltung, Abmeldung oder Reparatur anderer Codex- und ChatGPT-Clients durch Janus
- Codex-eigene Tool-, Shell-, Datei-, Approval- oder sonstige Agentenausführung
- Dauerhafte App-Server-Threads, persistierte Codex-Thread-IDs oder eine parallele Codex-Gesprächshistorie
- Eine zweite Codex-Agentenoberfläche, ChatGPT-Sonderrechte oder neue ChatGPT-spezifische Janus-Berechtigungsregeln
- Automatische Wiederholung, automatischer API-Key-Provider-Fallback oder doppelte Inhaltsübertragung
- Ungeprüfte experimentelle App-Server-Versionen, Weiterbetrieb bei Vertragsdrift oder ein reduzierter textbasierter Ersatzmodus ohne Janus-Tools
- Eine von Janus gepflegte, gepatchte oder geforkte Codex-Runtime
- Zulassung von `update_plan` oder einer anderen Codex-nativen Aktionsoberfläche als Ausnahme von der Janus-only Grenze
- Bereinigung der aus dem abgebrochenen Isolationstest verbliebenen kontrollierten Test-Credentials
- Erweiterung auf andere neue OAuth-Provider
- Release, Veröffentlichung oder Aktivierung ohne die festgelegte Sicherheits- und Isolationsevidenz

## INTERNAL COMPLEXITY BREAKDOWN

- Scope Size: 17
- Architectural Risk: 20
- State / Persistence Complexity: 18
- Cross-System Dependencies: 19
- Ambiguity Level: 4
- Total Complexity Score: 78
- Routing Decision: 5.6 Sol
- Routing Reasoning: high
- Routing Confidence: HIGH
- Dashboard Hint: CRITICAL

## SPEC REVIEW METADATA

- **Review Status:** APPROVED
- **Complexity Score:** 78
- **Risk:** HIGH
- **Recommended Review Model:** 5.6 Sol
- **Skill-1 Ready:** YES
- **Split Required:** NO
- **Reviewed At:** 2026-07-16
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
- **Remaining Work:** Tasks `.4` and `.5` remain open. The Feature Spec is not DONE and production remains default-deny.

### TASK-CHATGPT-DEVICE-CODE-PROVIDER.2

- **Implementation Status:** DONE
- **Final Audit:** PASS
- **Completed At:** 2026-07-15
- **Scope:** Non-sensitive Settings lifecycle, Janus-only logout, atomic account replacement, transient/redacted device-code UI, unavailable secure-storage state without fallback, and API-key non-interference.
- **Validation:** Settings API `11 passed`; headed mocked Settings E2E `8 passed`; Python/JavaScript syntax and scoped diff checks PASS; passive account-free Settings observation PASS.
- **Evidence:** `documentation/tasks/TASK-CHATGPT-DEVICE-CODE-PROVIDER.2_final_audit.md`; `documentation/tasks/TASK-CHATGPT-DEVICE-CODE-PROVIDER.2_AUDIT_PACKAGE.md`; `documentation/tasks/TASK-CHATGPT-DEVICE-CODE-PROVIDER.2_execution_result.md`
- **Remaining Work:** Tasks `.4` and `.5` remain open. Task `.3` is completed separately; the Feature Spec is not DONE and production remains default-deny.

### TASK-CHATGPT-DEVICE-CODE-PROVIDER.3

- **Implementation Status:** DONE
- **Final Audit:** PASS
- **Completed At:** 2026-07-16
- **Scope:** Current-session `model/list` verification, verified-model-only provider visibility, fail-closed unavailability/retry, stale-selection rejection and self-healing, redaction, and API-key-provider non-interference; no ChatGPT transport or privacy/context transfer.
- **Validation:** Backend/hierarchy `17 passed`; focused headed stale-start and verified/unavailable scenarios `1 passed` each; full headed Settings E2E `10 passed`; Python compile, JavaScript syntax, scoped diff, and production transport/service-provider default-deny probe PASS; passive real-shell restart evidence PASS.
- **Evidence:** `documentation/tasks/TASK-CHATGPT-DEVICE-CODE-PROVIDER.3_final_audit.md`; `documentation/tasks/TASK-CHATGPT-DEVICE-CODE-PROVIDER.3_AUDIT_PACKAGE.md`; `documentation/tasks/TASK-CHATGPT-DEVICE-CODE-PROVIDER.3_execution_result.md`
- **Remaining Work:** Tasks `.4` and `.5` remain open. The Feature Spec is not DONE and production remains default-deny.

### TASK-CHATGPT-DEVICE-CODE-PROVIDER.4

- **Implementation Status:** BLOCKED
- **Failure Code:** `UPSTREAM_DYNAMIC_TOOLS_ONLY_MODE_ABSENT`
- **Decision At:** 2026-07-16
- **Locked Choice:** Auf offiziellen Dynamic-Tools-only- oder vollständigen Core-Tool-Allowlist-Support warten
- **Rejected Alternatives:** Keine Janus-gepatchte Runtime, keine Zulassung von `update_plan`, keine Anforderungsabschwächung und kein degradierter Ersatzpfad
- **Re-entry Gate:** Account-freie ausführbare Evidenz gegen den exakten offiziellen Runtime-Stand und anschließend grüner `janus-preimplementation-check`
- **Remaining Work:** Task `.4` bleibt blockiert; Task `.5` bleibt alleiniger späterer Produktionsfreigabe- und Evidenzschritt. Produktion bleibt default-deny.
