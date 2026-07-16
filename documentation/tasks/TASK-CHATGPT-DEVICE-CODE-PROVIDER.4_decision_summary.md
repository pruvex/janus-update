# LATEST DECISION SUMMARY

Feature Name: ChatGPT als textbasierter Janus-Provider mit Janus-kontrollierten Skills und Tools

Primary Goal: ChatGPT soll sich im Janus-Chat wie ein bestehender API-Key-Provider verhalten, waehrend Authentifizierung und Modellzugang ueber den offiziellen Codex App Server erfolgen. Dafuer darf Task `.4` den experimentellen clientseitigen Tool-Vertrag verwenden, solange er schemafest, fail-closed und bis Task `.5` produktiv deaktiviert bleibt.

User Problem: Der offizielle App Server ist agentisch und kann eigene Tool-, Befehls-, Datei- oder Approval-Aktionen erzeugen. Diese zweite Aktions- und Berechtigungsoberflaeche darf Janus nicht umgehen oder ersetzen.

User Value: Nutzer erhalten ChatGPT-Kontozugang mit dem gewohnten Janus-Chat, Providerwechsel, Streaming sowie denselben Janus-Skills und -Tools, ohne Codex-eigene Aktionen oder Sonderrechte einzufuehren.

Primary Target Surface: Bestehender Janus-Chat mit Provider- und Modellauswahl sowie bestehendem Datenschutzdialog.

Existing or New Surface: Bestehende Oberflaechen; ChatGPT wird als zusaetzlicher Provider eingebunden.

Existence Confirmation: confirmed by user

User Trigger: Der Nutzer waehlt ChatGPT mit einem aktuell verifizierten Modell und sendet eine Nachricht, auch nach einem Providerwechsel mitten im bestehenden Chat.

Success Behavior:

- Janus uebergibt denselben fuer den Turn benoetigten, Janus-zusammengestellten und redigierten Kontext wie bei API-Key-Providern.
- Die Antwort erscheint im gewohnten Janus-Streaming; sichtbar sind nur Text und Janus-kontrollierte Toolstatus.
- ChatGPT darf dieselben von Janus freigegebenen Skills und Tools anfordern wie andere Provider. Janus allein prueft und fuehrt sie mit seinen bestehenden Berechtigungs-, Bestaetigungs- und Sicherheitsregeln aus.
- Die experimentelle App-Server-Schnittstelle fuer Janus-eigene Client-Tools ist fuer Task `.4` zulaessig, sofern Janus die erwartete Protokollversion eindeutig prueft und die Funktion ohne exakt passenden Vertrag nicht anbietet.
- Fuer jeden Turn verwendet Janus nur einen temporaeren App-Server-Thread. Janus bleibt alleinige Quelle des Gespraechsverlaufs und speichert keine Codex-Thread-ID.

Failure Behavior:

- Codex-eigene Tool-, Shell-, Datei-, Approval- oder sonstige Agent-Aktionen sind verboten. Fordert der App Server eine solche Aktion an, endet nur dieser Turn fail-closed mit einer verstaendlichen Meldung.
- Fehlt die erwartete experimentelle Janus-Tool-Schnittstelle, weicht ihr Vertrag ab oder kann Janus die Sperre Codex-eigener Aktionen nicht nachweisen, bleibt ChatGPT vollstaendig nicht nutzbar; es gibt keinen text-only Ersatzpfad.
- Es gibt weder automatische Wiederholung noch automatischen Fallback auf einen API-Key-Provider.
- Ein ChatGPT-Transportfehler betrifft nur den aktuellen Turn; Verlauf, Entwurf, Providerwahl und Anmeldung bleiben erhalten.
- Das Abbrechen beendet nur den laufenden temporaeren Turn und erhaelt Janus-Verlauf, Entwurf, Providerwahl und Anmeldung.

User Action Surface: Provider-/Modellauswahl, versionierte Datenschutzbestaetigung vor der ersten Inhaltsuebertragung und Abbrechen des laufenden Turns. ChatGPT erhaelt keine eigene sichtbare Agentenoberflaeche.

Data / Persistence:

- Der bestehende Janus-Verlauf bleibt die einzige Gespraechsquelle; es entsteht kein zweites dauerhaftes Codex-Gespraech.
- Die bestehende versionierte Datenschutzbestaetigung bleibt gespeichert; eine wesentliche Textaenderung verlangt vor der naechsten Uebertragung erneut eine Bestaetigung.
- Bei Ablehnung oder Schliessen des Dialogs wird nichts uebertragen. Entwurf und Providerauswahl bleiben erhalten.

Security / Privacy:

- Vor der ersten ChatGPT-Uebertragung nennt die Information ausdruecklich die aktuelle Nachricht, den benoetigten Gespraechsverlauf, Janus-/Skill-Anweisungen sowie erforderliche Tool-Eingaben und -Ergebnisse.
- Janus bleibt alleinige Tool-, Berechtigungs-, Redaktions- und Ausfuehrungsgrenze; ChatGPT erhaelt keine Sonderrechte.
- Der experimentelle Client-Tool-Vertrag ist eine ausdruecklich akzeptierte, vorlaeufige Abhaengigkeit. Seine konkrete Laufzeitversion muss nachweisbar passen; Vertragsdrift fuehrt fail-closed zur Nichtverfuegbarkeit.
- API-Key-Provider und ihre Zugangsdaten bleiben unbeeinflusst und sind weder Voraussetzung noch Fallback.
- Die Produktionsaktivierung bleibt bis zum separaten Evidenz-Task `.5` default-deny. Task `.5` muss sowohl den passenden Client-Tool-Vertrag als auch die harte Nichtausfuehrung Codex-eigener Aktionen belegen.

Edge Cases:

- Ungueltige oder veraltete Modellverifikation blockiert weiterhin vor dem Senden.
- Geschlossene oder abgelehnte Datenschutzbestaetigung verursacht keine externe Uebertragung.
- Unerlaubte Codex-Agentenaktion, Transportfehler und Nutzerabbruch bleiben auf den aktuellen ChatGPT-Turn begrenzt.
- Fehlende, veraenderte oder nicht pruefbare experimentelle Tool-Unterstuetzung macht ChatGPT nicht nutzbar und aktiviert keinen reduzierten Ersatzmodus.
- Interne Codex-Fortschritts-, Befehls-, Datei- und Approval-Ereignisse erscheinen nicht im Janus-Chat.

Out of Scope:

- Codex-eigene Tool-, Shell-, Datei- oder Approval-Ausfuehrung
- Dauerhafte Codex-Threads oder parallele Gespraechshistorie
- ChatGPT-Sonderrechte, neue Janus-Berechtigungsregeln oder zweite Agentenoberflaeche
- Automatische Wiederholung, Provider-Fallback oder doppelte Inhaltsuebertragung
- Aenderung vorhandener API-Key-Provider
- Produktionsaktivierung oder Task `.5`
- Ungepruefte Nutzung einer beliebigen App-Server-Version oder Weiterbetrieb bei Protokolldrift

Routing Decision: FULL FEATURE PIPELINE

Routing Reason: Externe Providergrenze, ausdruecklich akzeptierter experimenteller Client-Tool-Vertrag, Kontext-/Tool-Datenweitergabe und fail-closed Sicherheitsverhalten erfordern eine gepruefte Spec-Aenderung.

Recommended Next Skill: `janus-spec-generator`
