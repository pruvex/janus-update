# BACKLOG-098 Task Spec - Janus Mail Backend Bootstrap und Connection State

## Source Backlog Item

BACKLOG-098 - Janus Mail Backend Bootstrap und Connection State

## Problem / Goal

Janus Mail braucht ein minimales Backend-Fundament mit Mail-Schemas, einem Mail-Router und einem klaren Gmail-Connection-State, damit die neue Mail-Surface verlaesslich starten kann.

## Scope

Ein backendseitiger Mail-Bootstrap fuer Connection-State, Router-Registrierung und erste testbare Mail-Statusantworten.

## Files

- `backend/data/schemas_mail.py`
- `backend/services/mail/__init__.py`
- `backend/services/mail/mail_service.py`
- `backend/api/routers/mail.py`
- `backend/main.py`
- `backend/tests/test_mail_service.py`

## Acceptance Criteria

- Der Mail-Router ist im Backend registriert und erreichbar.
- Der Mail-Status unterscheidet mindestens connected, disconnected, missing_scope und sync_error.
- Fehler im Gmail-Statuspfad brechen den Backend-Start nicht.
- Backend-Tests decken Erfolgs- und Fehlerpfade fuer den Statusvertrag ab.

## Verification Plan

- Backend-Tests pruefen Status-Mapping und Router-Responses.
- Ein Router-Test bestaetigt, dass kein pseudo-inbox payload bei fehlender Verbindung geliefert wird.

## Out Of Scope

- Threadliste und Nachrichtendetails
- Suche
- Senden, Antworten, Archivieren, Trash, Restore
- Anhange
- AI-Zusammenfassungen und Drafts
