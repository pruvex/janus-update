# BACKLOG-099 Task Spec - Chat-Inhalt geht nach Neustart verloren und wird als Zahl wiederhergestellt

## Source Backlog Item

BACKLOG-099 - Chat-Inhalt geht nach Neustart verloren und wird als Zahl wiederhergestellt

## Problem / Goal

Der Chatverlauf stellt nach einem Neustart eine zuvor korrekt gespeicherte User-Eingabe nicht mehr als Originaltext dar, sondern nur noch als isolierte Zahl wie `3`. Ziel ist, die Persistenz und Wiederherstellung so zu korrigieren, dass der originale User-Text nach Restart, Reload oder Reopen konsistent sichtbar bleibt.

## Scope

- Restart-/Reload-Wiederherstellung fuer persistierte User-Nachrichten im Chatverlauf untersuchen.
- Ursache fuer die falsche Darstellung als isolierte Zahl beheben.
- Sicherstellen, dass die Korrektur fuer GPT- und Gemini-Chats gleich wirkt.
- Bestehende Mail-/Chat-Flows bei Reload und Reopen nicht verschlechtern.

## Acceptance Criteria

- Nach Neustart bleibt die originale User-Eingabe im Chatverlauf sichtbar.
- Der Verlauf zeigt keine isolierte Nummer statt des eigentlichen Textes.
- Das Verhalten ist bei GPT und Gemini identisch korrigiert.
- Der Fix bricht bestehende Chat- oder Mail-Flows nicht.

## Verification Plan

- Reproduktionsfall mit natuerlicher Mail-/Ordner-Anfrage im Chat ausfuehren.
- Janus neu starten und pruefen, dass der originale User-Text im Verlauf erhalten bleibt.
- Den gleichen Ablauf mindestens einmal mit GPT- und einmal mit Gemini-Chat pruefen.
- Reopen-/Reload-Flow auf bestehende Chatdarstellung gegenpruefen.

## Out Of Scope

- Neue Mailfunktionen oder Mail-UI-Aenderungen
- Allgemeine Chat-Performance-Optimierungen
- Aenderungen an Modellrouting oder Providerlogik
