# BACKLOG-034: system.routing wird aus Tool-Liste entfernt

## 1. Problembeschreibung
Gemini ruft `system.routing` gar nicht auf. Der Skill-Selector wählt es aus, aber der Tool-Filter entfernt es aus der eingeschränkten Tool-Liste, die an den LLM-Provider übergeben wird.

## 2. Symptome
- Skill-Selector wählt `system.routing` aus: `total=['memory.read', 'system.routing', 'system.local_business', 'system.country_info']`
- Tool-Filter entfernt es: `Eingeschraenkte Toolliste aktiv (3/231)` (nur 3 statt 4)
- Gemini-Sanitize zeigt nur: `system.local_business`, `system.country_info`, `memory.read` - `system.routing` fehlt
- Ergebnis: Gemini antwortet ohne Tool-Call, keine Attribution möglich

## 3. Ursache
Filter-Logik in `backend/llm_providers/shared/utils.py` (Zeile 606-609) prüft `allowed_skill_ids`. `system.routing` wird aus der `allowed`-Liste entfernt, obwohl es vom Skill-Selector ausgewählt wurde.

```python
skill_id = str(tool_manager.get_skill_id(tool_name) or "").strip()
if skill_id in allowed and skill_id not in seen_skill_ids:
    seen_skill_ids.add(skill_id)
    filtered.append(tool_def)
```

## 4. Umsetzungsschritte
1. Prüfen wo `allowed_skill_ids` gesetzt wird (vermutlich im Orchestrator oder Skill-Selector)
2. Identifizieren warum `system.routing` nicht in `allowed` enthalten ist
3. Fix: sicherstellen dass `system.routing` in `allowed_skill_ids` enthalten ist wenn vom Skill-Selector ausgewählt
4. Validierung: Tool-Liste enthält `system.routing`, Gemini ruft es auf

## 5. Acceptance Criteria
- [ ] `system.routing` wird nicht aus Tool-Liste entfernt
- [ ] Gemini erhält `system.routing` in der Tool-Liste
- [ ] Gemini ruft `system.routing` auf bei Geo-Distanz-Fragen
- [ ] Attribution "Quelle: OSRM" wird angezeigt

## 6. Tests / Validierung
- Manual Test (Gemini): "Wie weit ist Berlin von Köln?" → Tool-Call zu system.routing
- Log prüfen: `Eingeschraenkte Toolliste aktiv (4/231)` statt `3/231`
- Gemini-Sanitize zeigt: `system_routing` in der Liste

## 7. Status
- **Status:** IMPLEMENTED (v2 - Dual Fix)
- **Reason:** Zweiter Fix implementiert nach Validation FAIL
- **Next Step:** Manual Re-Validierung mit Gemini
- **Assigned Model:** SWE 1.6
- **Implementation v1:** `wf.relevant_skill_ids` wird zu `gateway_kwargs['allowed_skill_ids']` kopiert (execution_dispatcher.py Zeile 852-854)
- **Implementation v2:** `top_k` von 5 auf 10 erhöht in llm_gateway.py (Zeile 132, 142, 143) um system.routing nicht zu filtern

## 8. Dependencies
- BACKLOG-032 (Attribution fehlt - blockiert durch dieses Problem)
- BACKLOG-033 (Mapping funktioniert - COMPLETED)
