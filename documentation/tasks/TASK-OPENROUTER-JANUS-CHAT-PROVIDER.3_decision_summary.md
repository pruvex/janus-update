# LATEST DECISION SUMMARY - TASK-OPENROUTER-JANUS-CHAT-PROVIDER.3

Feature Name: OpenRouter - sofortige Invalidierung bei eindeutiger authentifizierter Anfrageablehnung

Primary Goal: Den bereits freigegebenen OpenRouter-Key-Vertrag aus Spec-Zeile 112 für Task `.3` entscheidungsfest machen: Lehnt OpenRouter einen zuvor `VALID` bestätigten, exakt gebundenen Key während einer authentifizierten Chat-Anfrage eindeutig als nicht autorisiert ab, wechselt genau dieser Key sofort zu `INVALID`.

User Problem: Ohne einen eindeutigen Vertrag könnte Janus einen nachweislich nicht mehr autorisierten Key fälschlich weiter als `VALID` behandeln oder technische Providerfehler irrtümlich als Credential-Fehler werten.

User Value: Janus sperrt einen tatsächlich abgelehnten Key sofort und fail-closed, bewahrt aber einen weiterhin gültigen Key bei technischen Störungen vor falscher Invalidierung.

Primary Target Surface: Bestehender OpenRouter-Chatturn und der bestehende gespeicherte OpenRouter-Key-Status.

Existing or New Surface: Bestehende Oberflächen und Zustände; keine neue sichtbare Oberfläche.

Existence Confirmation: Repository und bindende OpenRouter-Spec bestätigen Chatpfad, Key-Status sowie `VALID` / `INVALID` / `UNVERIFIED`.

User Trigger: Der Nutzer sendet einen OpenRouter-Chatturn mit einem zuvor `VALID` bestätigten Key.

Success Behavior:

- Eine eindeutige authentifizierte Nichtautorisierungs-Ablehnung während der Anfrage setzt sofort ausschließlich den exakt für diese Anfrage gebundenen Key auf `INVALID`.
- Die Invalidierung ist eine authority-owned Einbahnoperation. Sie kann niemals `VALID` vergeben, hochstufen, erhalten, wiederherstellen oder auf einen anderen Key übertragen.
- Der gespeicherte Key wird nicht automatisch gelöscht. Andere Provider-Credentials und spätere Ersatz-Keys bleiben unverändert.
- Provider und Modell bleiben gemäß bestehender Spec sichtbar ausgewählt, aber deaktiviert; Senden bleibt gesperrt, bis die Auswahl wieder gültig ist oder der Nutzer bewusst wechselt.

Failure Behavior:

- Der aktuelle Turn endet fail-closed ohne Retry, Replay, Doppelübertragung, Modellwechsel oder Provider-Fallback.
- Netzwerk-, Timeout-, Rate-Limit-, Provider-, Modell-, malformed-response-, Stream- und sonstige technische Fehler verändern einen zuvor `VALID` bestätigten Key nicht.
- Eine mehrdeutige oder nicht eindeutig authentifizierte Ablehnung gilt nicht als Invalidierungsnachweis und bleibt zustandsneutral.

User Action Surface: Keine neue Aktion. Die Statusänderung folgt automatisch aus der eindeutigen authentifizierten Ablehnung; Speichern, Ersetzen, erneutes Prüfen und Löschen bleiben die bestehenden bewussten Settings-Aktionen.

Data / Persistence:

- Nur der nicht geheime Validierungsstatus des exakt gebundenen OpenRouter-Keys wechselt zu `INVALID`.
- Raw-Key-Speicherung, Key-Fingerprint-Bindung und bestehender OpenRouter-Namensraum bleiben erhalten.
- Ein zwischen Anfrage und Invalidierung ersetzter oder anders gebundener Key darf nicht invalidiert werden.

Security / Privacy:

- Die Invalidierung bleibt allein bei der bestehenden Janus-owned Credential-Autorität.
- Der Anfragepfad erhält keine Fähigkeit, `VALID` zu vergeben, hochzustufen, zu erhalten oder wiederherzustellen.
- Nur eindeutige authentifizierte Ablehnung ist zulässiger Auslöser; technische oder mehrdeutige Fehler bleiben fail-closed und zustandsneutral.
- Fehlermeldungen und Evidenz bleiben nicht geheim und dürfen weder Raw-Key noch key-abgeleitete Identifikatoren offenlegen.
- Die Entscheidung erzeugt keine zweite `VALID`-Autorität und ändert weder Zertifizierungs-, Modell- noch Provider-Fallback-Regeln.

Edge Cases:

- Wurde der Key vor Abschluss des fehlgeschlagenen Turns ersetzt, darf die Ablehnung des alten Keys den neuen Key nicht verändern.
- Wiederholte Meldung derselben eindeutigen Ablehnung bleibt idempotent bei `INVALID` und löst keinen weiteren Provideraufruf aus.
- Rate Limit, Providerstörung oder Modellfehler dürfen nicht als Authentifizierungsablehnung umklassifiziert werden.
- Teilweise Stream-Ausgabe wird nicht als erfolgreicher Turn abgeschlossen und nicht erneut übertragen.

Out of Scope:

- Änderung oder Umdeutung der OpenRouter-Feature-Spec
- Neue Key-Zustände oder neue Settings-/Chat-Oberflächen
- Automatische Revalidierung, Retry, Replay, Credential-Löschung oder Credential-Fallback
- Fähigkeit des Runtime-Pfads, `VALID` zu schreiben, zu erhalten oder wiederherzustellen
- Konkrete Codearchitektur, Funktionsnamen, HTTP-Status-Mapping oder Implementierung
- Änderungen an Tasks `.1`, `.2`, `.4`, `.5` oder `.6`

Routing Decision: FULL FEATURE PIPELINE

Routing Reason: Security-relevanter Delta-Vertrag innerhalb einer bestehenden externen Providerintegration; die Produktentscheidung ist gelockt und muss nun widerspruchsfrei in genau Task `.3` übernommen werden.

Recommended Next Skill: `janus-task-breakdown`

Decision Status: LOCKED

## Decision Handoff

- Target Skill: `janus-task-breakdown`
- Target Task: `TASK-OPENROUTER-JANUS-CHAT-PROVIDER.3`
- Canonical State: `HANDOFF`
- Required Artifacts:
  - `documentation/SPEC/OPENROUTER_JANUS_CHAT_PROVIDER_FEATURE_SPEC.md`
  - `documentation/tasks/TASK-OPENROUTER-JANUS-CHAT-PROVIDER.3_decision_summary.md`
  - `documentation/tasks/TASK-OPENROUTER-JANUS-CHAT-PROVIDER.3_task_breakdown.md`
  - `documentation/tasks/TASK-OPENROUTER-JANUS-CHAT-PROVIDER.3_precheck.md`
- Decision: Preserve Spec line 112 and bind exactly one authority-owned, exact-key-safe invalidation path for unambiguous authenticated request rejection, with no capability to grant, upgrade, preserve, or restore `VALID`.
- Scope Rule: Refine the Task only; do not implement, run precheck, access credentials, call OpenRouter, or perform Git actions in the handoff step.
