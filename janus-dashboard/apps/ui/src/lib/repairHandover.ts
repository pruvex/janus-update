import type { BacklogItem } from '@shared/types'
import type { RepairIssue } from './repairIssues'
import { getParentTaskReference, hasValue } from './repairIssues'

const valueOrFallback = (value: string | null | undefined, fallback = 'nicht angegeben') => {
  return hasValue(value) ? value.trim() : fallback
}

const buildTaskContext = (item: BacklogItem, issue: RepairIssue): string => {
  return `Task:
- ID: ${item.id}
- Titel: ${item.title}
- Parent Task Reference: ${getParentTaskReference(item)}
- Kategorie: ${valueOrFallback(item.type)}
- Status: ${valueOrFallback(item.status)}
- Issue Type: ${issue.type}
- Recommended Skill: ${issue.recommendedSkill}
- Wichtigkeit: ${valueOrFallback(item.importance)}
- Umsetzungsrisiko: ${valueOrFallback(item.implementation_risk)}
- Aufwand: ${valueOrFallback(item.effort)}
- Umsetzungsreife: ${valueOrFallback(item.readiness)}
- Empfehlung: ${valueOrFallback(item.recommendation)}
- Entry Point: ${valueOrFallback(item.entry_point)}
- Routing Reason: ${valueOrFallback(item.routing_reason)}
- Routing Confidence: ${valueOrFallback(item.routing_confidence)}
- Routing Blocker: ${valueOrFallback(item.routing_blocker)}
- Handoff: ${valueOrFallback(item.handoff)}
- Recommended Next Skill: ${valueOrFallback(item.recommended_next_skill)}`
}

const buildSourceOfTruthRule = (): string => {
  return `Source-of-Truth-Regel:
- Das Dashboard ist read-only und darf keine Reparaturzustände setzen.
- Repariere die kanonische Backlog-Quelle: documentation/backlog/BACKLOG.md.
- Führe danach im Ordner janus-dashboard aus: npm run sync:backlog.
- Die Repair-Card darf erst verschwinden, wenn data/backlog.snapshot.json nach dem Sync keine Issue-Bedingung mehr enthält.
- Kein UI-only Fix, kein manuelles Done, kein lokaler Dashboard-State.`
}

const buildRoutingMissingHandover = (issue: RepairIssue): string => {
  return `HANDOVER – ROUTING REPAIR

${buildTaskContext(issue.item, issue)}

Issue:
- routing_missing

Objective:
Nutze @[/BACKLOG SKILL 3 – EXECUTION HANDOFF], um fehlende Routing- und Handoff-Informationen deterministisch zu reparieren.

Requirements:
- Implementation Entry Point bestimmen
- Routing Reason setzen
- Routing Confidence setzen
- Recommended Next Skill bestimmen
- Handoff-Artefakt erzeugen oder korrekt referenzieren
- Status/Section-Konsistenz in documentation/backlog/BACKLOG.md erhalten

Required successful state after repair:
- entry_point ist gesetzt und nicht ROUTING_MISSING
- routing_reason ist gesetzt
- routing_confidence ist gesetzt
- recommended_next_skill ist gesetzt
- routing_missing wird im Snapshot nicht mehr aus den Feldern abgeleitet

${buildSourceOfTruthRule()}`
}

const buildRoutingBlockedHandover = (issue: RepairIssue): string => {
  return `HANDOVER – ROUTING BLOCKER REPAIR

${buildTaskContext(issue.item, issue)}

Issue:
- routing_blocked

Objective:
Nutze @[/BACKLOG SKILL 3 – EXECUTION HANDOFF], um den Routing-Blocker aufzulösen oder den Blocker auditierbar zu präzisieren.

Requirements:
- Routing Blocker prüfen
- Fehlende Informationen oder Artefakte benennen
- Wenn lösbar: Entry Point, Routing Reason, Routing Confidence, Recommended Next Skill und Handoff setzen
- Wenn nicht lösbar: Item konsistent lassen und konkrete nächste Informationsanforderung dokumentieren
- Keine Implementierung starten

Required successful state after repair:
- entry_point ist nicht mehr ROUTING_BLOCKED, falls der Blocker lösbar war
- routing_blocker ist entfernt oder präzise aktualisiert
- recommended_next_skill ist eindeutig, falls pipeline-bereit

${buildSourceOfTruthRule()}`
}

const buildNeedsInfoHandover = (issue: RepairIssue): string => {
  return `HANDOVER – NEEDS INFO REPAIR

${buildTaskContext(issue.item, issue)}

Issue:
- needs_info

Objective:
Nutze @[/BACKLOG SKILL 1 – INTAKE TRIAGE], um fehlende Informationen zu ermitteln und das Backlog-Item pipeline-fähig zu machen oder auditierbar blockiert zu lassen.

Requirements:
- Fehlende Nutzerentscheidung, Repro, Scope-Information oder Akzeptanzkriterien bestimmen
- Keine Anforderungen erfinden
- Bei ausreichender Information Status und Felder konsistent aktualisieren
- Bei weiterhin fehlender Information konkrete Frage/Anforderung im Backlog festhalten

Required successful state after repair:
- status ist nicht mehr NEEDS INFO, wenn alle Pflichtinformationen vorhanden sind
- readiness/recommendation sind konsistent aktualisiert
- routing kann anschließend über BACKLOG SKILL 3 vorbereitet werden

${buildSourceOfTruthRule()}`
}

const buildBlockedHandover = (issue: RepairIssue): string => {
  return `HANDOVER – BLOCKED ITEM REPAIR

${buildTaskContext(issue.item, issue)}

Issue:
- blocked

Objective:
Nutze ${issue.recommendedSkill}, um den Blocker deterministisch zu analysieren und nur dann zu entfernen, wenn die echte Ursache behoben ist.

Requirements:
- Blocker-Ursache aus Backlog-Feldern und Artefakten bestimmen
- Keine manuelle UI-Auflösung verwenden
- Wenn Requirements fehlen: an BACKLOG SKILL 1 zurückführen
- Wenn Routing/Handoff fehlt: an BACKLOG SKILL 3 zurückführen
- Wenn Implementierungs-/Audit-Fehler vorliegt: Skill 5 Debug-Flow verwenden
- Nach echter Reparatur Backlog-Status und relevante Felder konsistent aktualisieren

Required successful state after repair:
- status ist nicht mehr BLOCKED, falls der Blocker behoben ist
- blocker/recommendation/readiness spiegeln den echten Zustand wider
- nächste Pipeline-Stufe ist eindeutig ableitbar

${buildSourceOfTruthRule()}`
}

export function buildRepairHandover(issue: RepairIssue): string {
  switch (issue.type) {
    case 'ROUTING_MISSING':
      return buildRoutingMissingHandover(issue)
    case 'ROUTING_BLOCKED':
      return buildRoutingBlockedHandover(issue)
    case 'NEEDS_INFO':
      return buildNeedsInfoHandover(issue)
    case 'BLOCKED':
      return buildBlockedHandover(issue)
    default:
      return buildNeedsInfoHandover(issue)
  }
}
