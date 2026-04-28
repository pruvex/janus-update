---
description: Führt einen vollständigen System-Gesundheitscheck und automatisches Self-Healing durch
---

## Steps

1. **Run Calibration (D20):** Aktualisiert die Datenbasis durch Matrix-Test-Kalibrierung
```powershell
Invoke-RestMethod -Uri "http://localhost:8001/api/system/run-batch-tests" -Method POST -ContentType "application/json" -Body '{"real_run": true, "runs_per_model": 5}'
```

2. **Check System Status (D25):** Zeigt den aktuellen Status und Heilungserfolge
```powershell
Invoke-RestMethod -Uri "http://localhost:8001/api/system/monitoring/summary" -Method GET
```

---

**Note:** Dieser Skill sollte einmal wöchentlich ausgeführt werden, um die statistische Basis für das Self-Healing zu sichern.
