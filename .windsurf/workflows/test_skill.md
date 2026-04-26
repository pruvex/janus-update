---
description: Test Skill — Führt den deterministischen Stabilitäts-Test für einen Skill aus
---

# Test Skill

Führt den deterministischen Stabilitäts-Test für einen Skill aus.

## Steps
1. Prompt: "Welchen Skill möchtest du testen? (z.B. system.weather)"
2. Execute: `curl.exe -X GET "http://localhost:8001/api/system/run-skill-tests/{{skill_id}}?skill_type=tool"`
3. Zeige das `health_summary` im Chat.
