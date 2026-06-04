# BACKLOG-101 - DeepDive Restore Cross-Provider Cost Visibility And Cache Savings

- Backlog Item: `BACKLOG-101`
- Status: `IN PROGRESS`
- Entry Point: `SPEC_PIPELINE_START`
- Created: `2026-06-03`

## Problem

Nach dem Spec-14-Umbau fuer Gemini-Kostenforensik ist die DeepDive-Oberflaeche in ihrer Kostenwahrheit fuer Gemini staerker geworden, zeigt aber die zuvor vorhandene provideruebergreifende Transparenz nicht mehr gleichwertig. Insbesondere muessen GPT/OpenAI-Verbrauch, Verbrauch pro Modell und Cache-/Savings-Sicht wieder sichtbar und mit der neuen Gemini-Forensik vereinbar sein.

## Ziel

Die bestehende DeepDive-Oberflaeche soll wieder eine zusammenhaengende Kostenansicht fuer mindestens GPT/OpenAI und Gemini liefern, inklusive:

- Verbrauch pro Provider
- Verbrauch pro Modell
- sichtbare Cache-/Savings-Kennzahlen
- Erhalt der neuen Gemini-Forensik aus Spec 14

## Bound Scope

- Bestehende DeepDive-/Kostenansicht
- `frontend/js/cost-visualizer.js`
- `frontend/src/styles.css`
- `frontend/index.html`
- zugehoerige Backend-Aggregationen nur soweit noetig, um die frueher sichtbaren Metriken wieder korrekt zu liefern

## Non-Goals

- keine komplette Websearch-Neuarchitektur
- keine allgemeine Billing-Plattform
- keine neue Produktoberflaeche ausserhalb des bestehenden DeepDive

## Why Spec Pipeline

Der Punkt ist zwar als Regression ausgeloest, aber der Scope ist nicht atomar: Frontend-DeepDive, Cross-Provider-Kostenaggregation, Modell-Splits, Cache-Savings und die neue Gemini-Forensik muessen bewusst zusammengefuehrt werden. Das ist groesser als ein lokaler Bugfix und sollte als eigener Spec-Strang sauber entschieden und validiert werden.
