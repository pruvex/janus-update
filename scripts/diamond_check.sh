#!/bin/bash
TASK_FOLDER="documentation/tasks"
LESSONS_FILE="docs/lessons_learned.md"
ERRORS=0
echo "🔹 Diamond-Check: Task Integrity & Lessons Learned"
if [ ! -f "$LESSONS_FILE" ]; then
  mkdir -p "$(dirname $LESSONS_FILE)"; echo "# Janus Lessons Learned" > "$LESSONS_FILE"; ERRORS=$((ERRORS+1))
fi
if [ -d "$TASK_FOLDER" ]; then
  for TASK in $TASK_FOLDER/*.md; do
    if ! grep -q "Audit Trail" "$TASK"; then echo "⚠️ Audit-Trail fehlt: $TASK"; ERRORS=$((ERRORS+1)); fi
  done
else
  mkdir -p "$TASK_FOLDER"; ERRORS=$((ERRORS+1))
fi
[ $ERRORS -eq 0 ] && echo "✅ Diamond-Check OK" || echo "⚠️ $ERRORS Fehler gefunden."
