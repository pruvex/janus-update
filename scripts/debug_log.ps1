$json = '{"mode":"fast"}'
$result = Invoke-RestMethod -Uri 'http://localhost:8001/api/skills/debug-log' -Method Post -ContentType 'application/json' -Body $json
$result | ConvertTo-Json -Depth 10
