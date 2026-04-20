# Janus Skill Implementation Checklist

Immer wenn ein neuer Skill erstellt oder ein bestehender Skill optimiert wird, muss diese Checkliste geprüft und im Agenten-Prompt mitgeführt werden.

## Pflicht-Checkliste

- **Schema-Definition**
  - Pydantic-Modell in `backend/data/schemas.py` ergänzt oder aktualisiert.

- **Katalog-Eintrag**
  - `backend/skills/<domain>/<action>.json` erstellt oder aktualisiert.
  - Enthält mindestens Version, `sandbox_level`, `latency_class`, `timeout_ms`, `tags`, `capabilities`, `is_agent_ready`, `max_calls_per_turn`, `depends_on` und Beispiele.

- **Policy**
  - Risiko-Level passend gesetzt, z. B. `read_only` oder `confirm_required`.

- **Renderer**
  - Prüfen, ob der Output deterministisch renderbar ist.
  - Wenn ja:
    - Renderer in `backend/renderers/implementations/` implementieren.
    - Renderer in `backend/renderers/registry.py` registrieren.
    - Im Skill-JSON `"deterministic_renderer": true` setzen.
  - Wenn nein:
    - Begründung in `documentation/SKILL_AUDIT_LOG.md` dokumentieren.

- **Tests**
  - Contract-Test ergänzt.
  - Renderer-Test ergänzt, falls deterministischer Renderer implementiert wurde.

- **Audit**
  - Eintrag in `documentation/SKILL_AUDIT_LOG.md` ergänzt oder aktualisiert.

## Pflichtsatz für Agenten-Prompts

Diesen Satz bei Skill-Optimierungen immer an den Prompt anhängen:

```text
Prüfe bei jedem Skill, den du optimierst, ob er gemäß unseren 'Diamond-Standards' (siehe /documentation/RULES_FOR_NEW_SKILLS.md) einen Renderer benötigt. Wenn ja, implementiere ihn direkt mit, anstatt die Optimierung und die Renderer-Migration in zwei Schritten zu machen.
```

## Arbeitsregel

- **Optimierung = Renderer-Prüfung**
- `documentation/SKILL_AUDIT_LOG.md` ist die laufende Referenz für Renderer-Entscheidungen.
- Der Verweis auf `documentation/RULES_FOR_NEW_SKILLS.md` soll in zukünftigen Coding-Agent-Prompts standardmäßig enthalten sein.
