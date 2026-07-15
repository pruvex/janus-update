# TASK BREAKDOWN HANDOFF

## Identity

- Source Spec: `documentation/SPEC/CHATGPT_OFFICIAL_DEVICE_CODE_PROVIDER_REDESIGN_FEATURE_SPEC.md`
- Source Task: `documentation/tasks/TASK-CHATGPT-DEVICE-CODE-PROVIDER.md`
- Backlog Item: N/A
- Target Task: `TASK-CHATGPT-DEVICE-CODE-PROVIDER.1`
- Decision: TASK DESIGN COMPLETE
- Released Tasks: Genau Task `.1`
- Parked Tasks: Tasks `.2` bis `.5`

## Source Of Truth

- Die freigegebene Ersatz-Spec ist die verbindliche Produktquelle.
- Der kompilierte Task `.1` ist die verbindliche Ausführungsgrenze.
- Frühere Browser-Callback-, Shared-Keyring- und Credential-Import-Annahmen sind ausdrücklich keine Freigabeevidenz.
- Chatverlauf, frühere Implementierungsideen und nicht gebundene Debug-Artefakte erzeugen keine zusätzlichen Anforderungen.

## Refined Target

- Atomic Goal: Den offiziellen Device-Code-Lifecycle innerhalb des bestehenden Codex-App-Server-Seams mit einer ausschließlich Janus gehörenden verschlüsselten persistenten Credential-Grenze implementierbar machen und vor nachfolgenden Tasks isoliert beweisen.
- Primary Product File: `backend/llm_providers/codex_app_server.py`
- Primary Test Files: `backend/tests/test_codex_app_server.py`, `tests/electron/codex-runtime-boundary.test.cjs`
- Execution Evidence File: `documentation/test-results/TASK-CHATGPT-DEVICE-CODE-PROVIDER.1_isolation_evidence.md`
- File Boundary Rule: Zusätzliche Produktmodule dürfen im Precheck nicht stillschweigend ergänzt werden. Wenn die sichere Speichergrenze innerhalb der gebundenen Datei-/Modulgrenze nicht umsetzbar ist, lautet das Ergebnis `BLOCKED` und der Task geht zurück zur Verfeinerung.

## Scope Boundary

- In Scope: Device-Code-Start und Abbruch, Janus-eigene sichere Persistenz, Neustartpersistenz, Refresh-Grenze, Janus-only Logout, Secret-Redaktion, Default-Deny und erster kontrollierter Zwei-Konten-Nachweis.
- Out Of Scope: Settings-UX, Provider-/Modell-Dropdown, Modellermittlung, Chat-Transport, Datenschutzdialog, atomarer UI-Kontowechsel, Produktionsaktivierung, Release und Bereinigung alter Test-Credentials.
- Non-Effect: API-Key-Anbieter sowie Codex Desktop, Codex CLI und IDE-Erweiterungen dürfen weder gelesen noch verändert, abgemeldet oder zur Credential-Quelle gemacht werden.

## Mandatory Precheck Proofs

- Der tatsächlich gebündelte und für Janus vorgesehene Codex-Runtime-Build unterstützt den offiziell dokumentierten `chatgptDeviceCode`-Modus ohne privaten OAuth-Client oder undokumentierten Backend-Endpunkt.
- Der gebundene Runtime-/Lifecycle-Pfad kann eine separat benannte, verschlüsselte und persistente Janus-Credential-Ablage nutzen, ohne den Credential-Slot eines anderen Codex-Clients zu teilen.
- Die geplante Ablage importiert, kopiert oder initialisiert keine bestehenden Codex-Credentials und kann Refresh sowie Logout auf die Janus-Sitzung begrenzen.
- Fehlt sichere Isolation oder fällt die Speicherfähigkeit aus, blockiert der Lifecycle vor Login, Account-Read mit Credentials und Refresh.
- Die Produktionsfreigabe bleibt nach Task `.1` weiterhin default-deny; der Task darf keine endgültige Freigabekennung setzen.
- Automatisierte Tests können alle sensitiven Werte durch Fakes ersetzen und prüfen, dass UI-Fehler, Logs und Evidenz keine Tokens, Device Codes oder Credentials enthalten.
- Während des Prechecks erfolgen keine Login-, Logout-, Refresh-, Revocation-, Keyring-, Credential- oder Cleanup-Aktionen.

## Binary Acceptance

- PASS nur wenn der offizielle Device-Code-Modus im gebundenen Runtime-Build nachgewiesen und ohne private Providerwege nutzbar ist.
- PASS nur wenn die Janus-Credential-Ablage verschlüsselt, persistent und von anderen Codex-Clients getrennt ist.
- PASS nur wenn fehlende sichere Speicherung alle credential-bezogenen Lifecycle-Aktionen vor Prozess- oder Netzwerkwirkung fail-closed blockiert.
- PASS nur wenn Janus-Neustart, Refresh und Logout ausschließlich die Janus-Sitzung betreffen.
- PASS nur wenn automatisierte Redaktions- und Nichtimport-Gates reproduzierbar sind.
- PASS der späteren kontrollierten Execution-Evidenz nur wenn ein separates Codex-Konto nach Janus-Login, Janus-Neustart und Janus-Logout bei Konto, Kontingent, Einstellungen und Sitzungszustand unverändert bleibt.
- Jede Abweichung ergibt `BLOCKED`; sie darf weder durch manuelle Freigabe noch durch einen API-Key-, Klartext- oder Session-only-Fallback übergangen werden.

## Planned Validation

- Fokus-Python-Tests für Device-Code-Vertrag, Default-Deny, Persistenz, Refresh, Logout, Nichtimport und Redaktion.
- Electron-Grenztests für gebündelte Runtime, Umgebungsgrenzen, Credential-Namensraum und Secret-Vermeidung.
- Syntax-/Compile-Prüfung der geänderten Runtime-Dateien.
- Scoped `git diff --check` für Task-`.1`-Dateien.
- Kontrollierter Zwei-Konten-Test erst während Execution, nach grünen automatisierten Gates und nach separater expliziter User-Freigabe für die externen Kontoaktionen.

## Model And Risk

- Execution Model: 5.6 Sol
- Reasoning: high
- Fallback: 5.6 Terra / high nur mit dokumentiertem Grund `SOL_UNAVAILABLE_FOR_CHATGPT_CODEX_ACCOUNT`
- Risk: HIGH
- Main Risk: Wiederholung der bereits beobachteten Cross-Client-Refresh- oder Credential-Kollision.
- Stop Rule: Jede unklare Credential-Eigentümerschaft, jeder geteilte Slot oder jeder Bedarf an privaten OAuth-/Backend-Endpunkten blockiert den Task vor Implementierung.

## Precheck Handoff

```text
@janus-preimplementation-check
Spec: documentation/SPEC/CHATGPT_OFFICIAL_DEVICE_CODE_PROVIDER_REDESIGN_FEATURE_SPEC.md
Task: documentation/tasks/TASK-CHATGPT-DEVICE-CODE-PROVIDER.md
Backlog Item: N/A
Target Task: TASK-CHATGPT-DEVICE-CODE-PROVIDER.1
Target Subtask: N/A
Mode: SINGLE_TASK_PRECHECK
Execution Model: 5.6 Sol
Rules: VALIDATE_ONE_TARGET_TASK_NO_IMPLEMENTATION_NO_CODE_CHANGES_RELEASE_EXECUTION_HANDOFF_ONLY_IF_SCOPE_FILES_TESTS_RISKS_ARE_CLEAR
Expected Output: PRE_CHECK_PASSED_PLUS_EXECUTION_HANDOFF_OR_PRE_CHECK_BLOCKED
```
