# BACKLOG-096 Task Spec - Chat-Header-Modellwahl beim neuen Chat im selben Fenster beibehalten

## Source Backlog Item

BACKLOG-096 - Chat-Header-Modellwahl beim neuen Chat im selben Fenster beibehalten

## Problem / Goal

Wenn ein Chatfenster im Header explizit ein Provider-/Modellpaar statt `wie Sidebar` nutzt, soll ein neu gestarteter Chat im selben Fenster diese Auswahl behalten. Nur Fenster ohne explizite Header-Wahl sollen weiterhin der Sidebar-Auswahl folgen.

## Scope

- Fensterlokale Modell- und Provider-Auswahl beim Start eines neuen Chats erhalten
- Default-Verhalten `wie Sidebar` nur fuer unveraenderte Fenster beibehalten
- Keine Aenderung an der bereits implementierten Neustart-Persistenz zwischen Janus-Sessions

## Acceptance Criteria

- Ein neuer Chat im selben Fenster behält die zuvor explizit gesetzte Header-Modellwahl.
- Die Auswahl springt nur dann auf `wie Sidebar`, wenn im Fenster keine explizite Header-Wahl gesetzt ist.
- Andere Chatfenster bleiben unveraendert.

## Verification Plan

- Manuell in Janus ein Chatfenster mit explizit gewaehltem Provider/Modell testen.
- Im selben Fenster einen neuen Chat starten und die Header-Auswahl pruefen.
- Ein zweites Fenster mit `wie Sidebar` gegenpruefen.

## Out Of Scope

- Neue Modelloptionen
- Aenderungen an der Sidebar-Auswahl selbst
- Neustart-Persistenz zwischen Janus-Sessions
