from backend.services.backlog.parser import parse_backlog_text


SAMPLE_BACKLOG = """# Janus Backlog

## READY

### BACKLOG-020 – Chatfenster-Resize-Problem

- **Typ:** BUG
- **Status:** READY
- **Quelle:** Screenshot
- **Erstellt:** 2026-05-09
- **Aktualisiert:** 2026-05-09
- **Wichtigkeit:** HIGH
- **Umsetzungsrisiko:** MEDIUM
- **Aufwand:** S
- **Umsetzungsreife:** READY
- **Empfehlung:** DO NOW
- **Entry Point:** PRE_IMPLEMENTATION_VERIFICATION
- **Routing reason:** Kleiner klarer UI-Bugfix.
- **Routing confidence:** HIGH
- **Routing decided by:** BACKLOG SKILL 3
- **Routing decided at:** 2026-05-09
- **Kurzbeschreibung:** Resize springt auf falsche Größe.
- **Betroffener Bereich:** Frontend / UI
- **Akzeptanzkriterien:**
  - [ ] Frei resizebar
- **Fehlende Informationen:**
  - Keine

## DONE

### BACKLOG-019 – Hardcoded gpt-5-mini verursacht Fallback-Warnung

- **Typ:** TECH_DEBT
- **Status:** DONE
- **Completed in version:** 0.4.17-beta.23
- **Completed by task:** documentation/tasks/backlog_BACKLOG-019_hardcoded_gpt5mini_fix.md
- **Completed at:** 2026-05-09
- **Final audit:** PASS
- **Validation evidence:** Manual Janus test PASS
"""


def test_parse_backlog_text_extracts_dashboard_fields():
    result = parse_backlog_text(SAMPLE_BACKLOG, source="sample")

    assert result.source == "sample"
    assert len(result.items) == 2

    item = result.items[0]
    assert item.id == "BACKLOG-020"
    assert item.title == "Chatfenster-Resize-Problem"
    assert item.section == "READY"
    assert item.type == "BUG"
    assert item.status == "READY"
    assert item.importance == "HIGH"
    assert item.implementation_risk == "MEDIUM"
    assert item.entry_point == "PRE_IMPLEMENTATION_VERIFICATION"
    assert item.routing_confidence == "HIGH"
    assert item.summary == "Resize springt auf falsche Größe."
    assert item.affected_area == "Frontend / UI"


def test_parse_backlog_text_builds_counts():
    result = parse_backlog_text(SAMPLE_BACKLOG, source="sample")

    assert result.counts.total == 2
    assert result.counts.active == 1
    assert result.counts.history == 1
    assert result.counts.ready == 1
    assert result.counts.done == 1
    assert result.counts.routing_missing == 0


def test_parse_backlog_text_counts_missing_routing_for_active_items():
    text = """# Janus Backlog

## READY

### BACKLOG-001 – Missing Routing

- **Typ:** BUG
- **Status:** READY
- **Kurzbeschreibung:** Test
- **Betroffener Bereich:** Test
"""
    result = parse_backlog_text(text, source="sample")

    assert result.counts.total == 1
    assert result.counts.active == 1
    assert result.counts.routing_missing == 1
