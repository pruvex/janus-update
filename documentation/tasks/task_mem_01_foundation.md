**Modell:** Kimi K2.5 (Windsurf)
**Ort:** Windsurf

**IST:** Memory nutzt hardcodierte Integer (`core_priority`) und ein starres Schema, das keine Metadaten für moderne Skills unterstützt.
**SOLL:** Schema V2.1.0 ist aktiv (Float-Priority, TTL, Tags). Migration ist fehlerfrei durchgelaufen inkl. Backfill-Logik für Altdaten.

**NEXT:**
1. **Lies:** `documentation/features/memory_v2.md` Section 3 (Schema) & 3.3 (Migration).
2. **Models:** Update `backend/data/models.py` (neue Spalten: priority, memory_type, ttl, tags, source_skill, user_editable, canonical_key).
3. **Schemas:** Update `backend/data/schemas.py` (Pydantic Modelle für API).
4. **Migration:** 
   - `alembic revision --autogenerate -m "memory_v2_priority_system"` 
   - Editiere das Skript: Nutze `op.batch_alter_table` für SQLite Kompatibilität!
   - Füge die Backfill-SQL aus Section 3.3 ein (mapping core_priority -> float priority).
5. **Execution:** `alembic upgrade head`.
6. **Verifikation:** `SELECT priority, memory_type FROM memories LIMIT 5;` - prüfe ob 0.95 für alte Core-Facts gesetzt wurde.
7. **Bericht:** Beende mit einem DIAMOND-REPORT.

**VERBOTENE AKTIONEN:** 
- Lösche KEINE alten Spalten (`is_core_fact`, `core_priority`) in dieser Phase (Migration Safety).
- Ändere NICHTS an der `alembic/env.py`.
