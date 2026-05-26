JANUS FEATURE SPEC – DIAMANTSTANDARD v2
1. FEATURE NAME

Capability Empty-State Chat Response Guidance

2. CORE IDEA

Dieses Feature definiert das Verhalten von Janus im Chat, wenn Nutzer nach Fähigkeiten, Capability-Übersichten oder „Was kannst du?“ fragen, aber keine Capability-Daten verfügbar sind oder die Liste leer ist.

Statt einer leeren oder fehlerhaften Antwort liefert Janus einen klaren, erklärenden Empty-State im Chat, der den Zustand verständlich macht und mögliche Ursachen neutral einordnet.

Das Feature ist rein responsiv im Chat-Kontext und verändert keine Daten oder Systemlogik.

3. USER PROBLEM & VALUE
User Problem

Wenn keine Capability-Daten verfügbar sind, erhält der Nutzer aktuell keine verständliche Erklärung im Chat, was zu Unsicherheit über den Systemzustand führt.

User Value

Der Nutzer versteht im Chat:

dass aktuell keine Fähigkeiten angezeigt werden können
dass dies an fehlenden, nicht geladenen oder nicht initialisierten Daten liegt
dass der Zustand temporär sein kann
dass eine erneute Anfrage später sinnvoll ist
Visible Success

Der Nutzer erhält im Chat eine klare, ruhige und erklärende Antwort statt einer leeren oder technischen Reaktion.

4. TARGET SURFACE
Primary Target Surface

Type:
Chat response

Existing vs New:
existing

User Trigger

Der Nutzer stellt im Chat eine Anfrage wie:

„Was kannst du?“
„Zeig mir deine Fähigkeiten“
„Welche Capabilities hast du?“

und das Capability-System liefert:

keine Daten oder
eine leere Capability-Liste oder
einen nicht ladbaren Zustand
Success Surface Behavior
Janus antwortet im Chat mit der regulären Capability-/Help-Übersicht
sofern Daten vorhanden sind, wird die bestehende Capability-Ausgabe genutzt
keine Veränderung des bestehenden Antwortformats
Failure / Empty Surface Behavior
Janus gibt eine verständliche Empty-State-Guidance im Chat aus
enthält:
klare Aussage, dass aktuell keine Fähigkeiten angezeigt werden können
neutrale Erklärung möglicher Ursachen (nicht geladen, nicht initialisiert, keine Daten verfügbar)
beruhigender Hinweis, dass der Zustand temporär sein kann
Empfehlung, die Anfrage später erneut zu stellen
Explicit Non-Surfaces

Das Feature erscheint ausdrücklich NICHT in:

Frontend-Ansichten (nicht existent / nicht genutzt)
Modals oder Dialogen
Settings-Bereichen
Sidebar oder Panels
Notification/Toast-Systemen
eigenen Capability-Seiten oder UI-Komponenten
Buttons oder UI Controls
5. USER ACTIONS
Action 1

Name: Retry via Chat Re-Query

Action Surface:
No explicit UI control (Chat instruction only)

Existing vs New:
none

Trigger:
Der Nutzer stellt die gleiche oder eine ähnliche Capability-Anfrage später erneut im Chat.

Exact Result:

erneute Ausführung der Capability-Abfrage über den Chatkontext
wenn Daten verfügbar sind → normale Capability-Antwort
wenn weiterhin keine Daten verfügbar sind → erneut Empty-State-Guidance

Explicit Non-Effects:

kein UI-Button
keine automatische Wiederholung
keine Datenänderung
keine externe Anfrage zusätzlich zum regulären Capability-Check
keine Persistenz

Data Effects:

Creates data: no
Mutates data: no
Persists data: no
Syncs data: no
Repairs data: no
Fetches external data: no
6. FUNCTIONAL CORE
Allowed Behavior
Chatbasierte Erkennung von Capability-Anfragen
Rückgabe einer strukturierten Capability-Antwort, wenn Daten vorhanden sind
Ausgabe eines erklärenden Empty-States im Chat, wenn keine Daten verfügbar sind
rein textbasierte Nutzerführung ohne UI-Komponenten
Not Allowed Behavior
keine UI-Erweiterungen oder Buttons
keine Capability-Erzeugung
keine Systemreparatur
keine automatischen Retry-Mechanismen
keine externen Datenabrufe außerhalb des bestehenden Capability-Checks
keine Persistenz oder Statusspeicherung
7. SYSTEM BEHAVIOR
Before State

Nutzer stellt Capability-Anfrage im Chat

During State

System prüft Capability-Daten:

vorhanden → normale Antwort
nicht vorhanden → Empty-State-Guidance wird erzeugt
Success State
vollständige Capability-Übersicht wird im Chat angezeigt
bestehendes Antwortsystem bleibt unverändert
Failure State
Chat enthält klare Empty-State-Erklärung
keine technischen Details
keine UI-Elemente
Nutzer wird zu späterer erneuter Anfrage motiviert
Empty State
identisch zum Failure State
Repeated Attempt Behavior
jede erneute Chat-Anfrage wird unabhängig behandelt
kein gespeicherter Fehlerzustand
kein Eskalationsverhalten
8. DATA / PERSISTENCE
Persistence

keine Persistenz

Data Mutation

keine Datenmutation

Data Creation

keine neue Datenerzeugung

External Data / Sync

nur reguläre Capability-Abfrage im bestehenden Systemkontext

Recovery

automatische Wiederherstellung durch erneute Chat-Anfrage mit verfügbaren Daten

9. EDGE CASES / FAILURE BEHAVIOR
leere Capability-Liste → Empty-State im Chat
nicht ladbare Capability-Daten → Empty-State im Chat
wiederholte Anfragen ohne Daten → gleiches Verhalten ohne Eskalation
teilweise vorhandene Daten → normale Capability-Antwort

Nutzer darf nie:

eine technische Fehlerstruktur im Chat sehen
eine unklare oder leere Antwort erhalten
in einem nicht erklärten Zustand verbleiben
10. CONSTRAINTS / LIMITS
keine UI-Komponenten
keine Buttons oder interaktiven Controls
keine externe Systemintegration über bestehende Capability-Abfrage hinaus
keine automatische Wiederholung oder Retry-Logik
keine Persistenz
keine Datenmanipulation
11. SECURITY / PRIVACY
Sensitive Data

nicht betroffen

Permissions

unverändert

External Exposure

keine zusätzlichen externen Systeme oder Datenflüsse

Security Boundary

keine Daten werden gespeichert, verändert oder außerhalb des Capability-Kontexts übertragen

12. INTEGRATION CONTEXT

Betroffene abstrakte Systembereiche:

Chat Response Layer
Capability Query Handler
Help/Capability Intent Detection

Nicht betroffen:

UI Frameworks
Frontend Views (nicht existent im Scope)
Settings-System
Persistence Layer
Notification/Toast-System
13. COMPLEXITY LEVEL

Level: Low

Begründung:
Reine Chat-Response-Logik basierend auf Vorhandensein von Capability-Daten, ohne UI oder State Management Erweiterungen.

Zentrale Risiken:

konsistente Formulierung des Empty-States im Chat
klare Abgrenzung zwischen Daten vorhanden vs nicht vorhanden
14. TEST STRATEGY REQUIREMENT

Die spätere Umsetzung muss prüfbar machen:

Capability-Anfrage im Chat mit vorhandenen Daten → korrekte Ausgabe der Capability-Übersicht
Capability-Anfrage im Chat ohne Daten → Empty-State-Guidance wird ausgegeben
keine UI-Elemente werden erzeugt
keine Persistenz oder Zustandsspeicherung erfolgt

Nicht-Regression:

bestehende Capability-Antworten bleiben unverändert
bestehende Chat-Logik wird nicht beeinflusst
15. DEFINITION OF DONE

Das Feature gilt nur als fertig, wenn:

Capability-Anfragen im Chat korrekt zwischen Success- und Empty-State unterscheiden
Empty-State ist klar, verständlich und nutzerzentriert formuliert
keine UI-Komponenten oder Controls existieren
keine Datenveränderung oder Persistenz erfolgt
wiederholte Anfragen bleiben konsistent im Verhalten
16. EXPLICIT OUT OF SCOPE

Nicht Teil dieses Features:

Frontend-UI oder Views
Buttons oder Retry Controls
neue Capability-Seiten
automatische Wiederholungslogik
externe Dokumentationsintegration
Telemetrie oder Logging-Erweiterung
Datenmodelländerungen
17. OPEN QUESTIONS
17.1 BLOCKING QUESTIONS

Keine blockierenden Fragen offen.

17.2 NON-BLOCKING QUESTIONS

Keine

18. IMPLEMENTATION CONTRACT (ABSTRACT ONLY)

Diese Spec definiert ausschließlich das Chat-Verhalten von Janus bei Capability-Anfragen ohne verfügbare Daten.

Alle späteren Implementierungen müssen sicherstellen:

keine UI-Abhängigkeiten entstehen
keine neuen Interaktionsmechanismen eingeführt werden
keine Persistenz oder Zustandsspeicherung erfolgt
Empty-State bleibt rein textbasiert im Chat
Capability-Antworten werden strikt datenbasiert oder als erklärter Empty-State ausgegeben

Jede Abweichung von diesem Verhalten gilt als Spezifikationsverletzung.