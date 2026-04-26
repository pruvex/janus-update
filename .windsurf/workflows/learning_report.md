---
description: Trigger the weekly D14 Evolution Report (Learning Engine) on port 8001
---

## Steps

1. Execute the learning report endpoint:
```powershell
curl.exe -X GET "http://localhost:8001/api/system/learning-report?format=markdown"
```

2. Display the output in the chat for analysis of trends and system improvement recommendations.
