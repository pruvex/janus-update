# Task: Bugfix - Websearch XML-Sandwich Drift (V1.0)

## 1. Klassifizierung & Ressourcen
- **Kategorie:** D11 (Bugfix-Strategie) / C7 (Code-Gen)
- **Ort:** AI Studio -> Cursor / Windsurf
- **Modell:** Claude 4.6 Sonnet

## 2. Zielsetzung
Behebung des Formatierungsfehlers in der Websuche. Die XML-Tags werden aktuell nicht sauber geschlossen, was zu Parser-Fehlern im Backend führt.

- **IST:** Bei Preisanfragen in Janus (z.B. "Was kostet das iPhone 15?") fehlen oft die direkten Links zu Idealo oder Geizhals, obwohl Ergebnisse gefunden wurden.
- **SOLL:** Jede Preisanfrage in Janus liefert am Ende der Antwort mindestens einen klickbaren und korrekten Idealo-Link zu den Suchergebnissen.
- **NEXT:** Kopiere den Prompt und lass Sonnet in Cursor den Fix umsetzen. Teste danach in Janus (der Anwendung), ob bei Preisanfragen wieder klickbare Idealo-Links erscheinen.
  - *Falls ja:* Klicke hier im Dashboard auf 'Mark Done'.
  - *Falls nein:* Kopiere die Zusammenfassung von Sonnet und das Fehler-Log ins AI Studio (Modell: Gemini 3.1 Flash) für eine neue Diagnose.

## 3. Akzeptanz-Kriterien
- [ ] Regex im `websearch_service.py` angepasst.
- [ ] Validierung der XML-Struktur vor dem Senden.
- [ ] Testlauf in Cursor erfolgreich.

## 4. Audit-Trail
| Datum | Status | Änderung |
| :--- | :--- | :--- |
| 2026-03-29 | Planned | Ad-hoc Injection via Janus V2.1. |
