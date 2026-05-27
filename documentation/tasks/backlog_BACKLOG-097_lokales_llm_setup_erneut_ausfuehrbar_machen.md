# BACKLOG-097 Task Spec - Lokales LLM Setup erneut ausfuehrbar machen

## Source Backlog Item

- [BACKLOG-097](../backlog/BACKLOG.md)

## Problem / Goal

Der Button `Lokales LLM einrichten` soll nicht nur einmal nach der ersten Einrichtung nutzbar sein. Nutzer muessen spaeter erneut einen Hardwarecheck starten koennen, damit neue Hardware, neue installierte Modelle und die aktuelle Ollama-Liste in die Empfehlungen einfliessen.

## Scope

- Re-Scan-Trigger fuer den lokalen LLM-Setup-Flow
- Frischer Hardwarecheck beim erneuten Start
- Abgleich mit der aktuellen Ollama-Modellliste
- Wiederverwendung der aktuellen lokalen Installationen und gespeicherten Nodes

## Acceptance Criteria

- Der Setup-Button laesst sich nach bereits erfolgter Einrichtung erneut nutzen.
- Ein erneuter Lauf fuehrt einen aktuellen Hardwarecheck aus.
- Die Empfehlungsliste basiert auf der aktuellen Ollama-Modellliste.
- Bereits installierte lokale Modelle und gespeicherte Nodes bleiben erhalten.
- Die UI macht erkennbar, dass ein erneuter Scan moeglich ist.

## Verification Plan

- Manuell pruefen, dass der Button nach Erstsetup nicht blockiert bleibt.
- Den Flow erneut ausloesen und bestaetigen, dass der Hardwarecheck neu laeuft.
- Pruefen, dass Empfehlungen zur aktuellen Modellliste passen.
- Verifizieren, dass bestehende lokale Installationen im Ergebnis weiter beruecksichtigt werden.

## Out Of Scope

- Neue Hardware-Erkennungslogik jenseits des erneuten Scans
- Aenderungen an der Ollama-Quelle selbst
- Allgemeine Rework-Arbeit an anderen Settings-Bereichen

## SPEC IMPLEMENTATION METADATA

- Implementation Status: DONE
- Final Audit: PASS
- Completion Date: 2026-05-27
- Validation Evidence: `python -m py_compile backend/services/ollama_manager.py`; `python -m pytest backend/tests/test_ollama_manager_recommendations.py -q`; manual Janus confirmation; `documentation/logs/janus_backend.log`; `documentation/logs/janus_frontend.log`
