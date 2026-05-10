import { useState } from 'react'
import type { BacklogItem } from '@shared/types'
import type { EstimatedTimeInsight } from '../lib/executionAnalytics'
import { Copy } from 'lucide-react'

interface KanbanCardProps {
  item: BacklogItem
  viewType?: 'active' | 'history'
  estimatedTime?: EstimatedTimeInsight | null
}

const TYPE_COLORS: Record<string, { bg: string; text: string }> = {
  'BUG': { bg: 'bg-orange-500/20', text: 'text-orange-400' },
  'CHANGE': { bg: 'bg-blue-500/20', text: 'text-blue-400' },
  'ENHANCEMENT': { bg: 'bg-green-500/20', text: 'text-green-400' },
  'IMPROVEMENT': { bg: 'bg-teal-500/20', text: 'text-teal-400' },
  'TECH_DEBT': { bg: 'bg-gray-500/20', text: 'text-gray-400' },
  'UNCLEAR': { bg: 'bg-purple-500/20', text: 'text-purple-400' },
  'SPEC FEATURE': { bg: 'bg-cyan-500/20', text: 'text-cyan-400' },
}

const IMPORTANCE_COLORS: Record<string, string> = {
  'CRITICAL': 'text-red-400',
  'HIGH': 'text-orange-400',
  'MEDIUM': 'text-yellow-400',
  'LOW': 'text-gray-400',
}

const isPresent = (value: string | null | undefined): value is string => {
  return Boolean(value && value.trim() && value.trim().toLowerCase() !== 'none' && value.trim().toLowerCase() !== 'null')
}

const valueOrFallback = (value: string | null | undefined, fallback = 'nicht angegeben') => {
  return isPresent(value) ? value.trim() : fallback
}

const formatSpecReviewExecutionMode = (value: string | null | undefined) => {
  const mode = valueOrFallback(value, '').toUpperCase()
  if (mode === 'SWE_1_6') {
    return 'SWE 1.6'
  }
  if (mode === 'GPT_5_5') {
    return 'GPT-5.5'
  }
  return 'Modell fehlt'
}

const getSpecReviewButtonLabel = (item: BacklogItem) => {
  if (item.type === 'SPEC FEATURE' && item.entry_point === 'SPEC_REVIEW_GATE') {
    return `Spec Review ausführen mit ${formatSpecReviewExecutionMode(item.raw_fields?.['Spec Review Execution Mode'])}`
  }
  return 'Edit Handover'
}

const getTypeColor = (item: BacklogItem) => {
  if (item.type === 'SPEC FEATURE' && item.entry_point === 'SPEC_REVIEW_GATE') {
    const hint = valueOrFallback(item.raw_fields?.['Spec Review Dashboard Hint'], '').toUpperCase()
    if (hint === 'CRITICAL') {
      return { bg: 'bg-red-500/20', text: 'text-red-400' }
    }
    if (hint === 'CAUTION') {
      return { bg: 'bg-yellow-500/20', text: 'text-yellow-400' }
    }
    if (hint === 'SAFE') {
      return { bg: 'bg-green-500/20', text: 'text-green-400' }
    }
  }
  return TYPE_COLORS[item.type] || TYPE_COLORS['UNCLEAR']
}

const buildBacklogContext = (task: BacklogItem): string => {
  return `Backlog-Kontext:
- Backlog Item: ${task.id}
- Titel: ${task.title}
- Typ: ${valueOrFallback(task.type)}
- Status: ${valueOrFallback(task.status)}
- Wichtigkeit: ${valueOrFallback(task.importance)}
- Umsetzungsrisiko: ${valueOrFallback(task.implementation_risk)}
- Aufwand: ${valueOrFallback(task.effort)}
- Umsetzungsreife: ${valueOrFallback(task.readiness)}
- Empfehlung: ${valueOrFallback(task.recommendation)}
- Entry Point: ${valueOrFallback(task.entry_point)}
- Routing reason: ${valueOrFallback(task.routing_reason)}
- Routing confidence: ${valueOrFallback(task.routing_confidence)}
- Handoff: ${valueOrFallback(task.handoff)}
- Recommended next skill: ${valueOrFallback(task.recommended_next_skill)}
- Target Task: ${valueOrFallback(task.target_task)}
- Precheck artifact: ${valueOrFallback(task.precheck_artifact)}`
}

const buildExecutionTelemetryContract = (task: BacklogItem): string => {
  return `Execution-Telemetrie:
- Schreibe KEINEN Pending-/Start-Record beim Kopieren dieses Handovers.
- Wenn die Task-Ausführung nach realer Skill-Ausführung, Validierung und erfolgreichem Abschluss completed ist, persistiere genau einen completed-only Record.
- Ziel: janus-dashboard/data/task-execution-history.json
- Script: npm run record:task-execution -- --input <completed-execution-record.json>
- source: skill_lifecycle
- task_id: ${task.id}
- task_title: ${task.title}
- task_type: ${valueOrFallback(task.type)}
- importance: ${valueOrFallback(task.importance)}
- effort: ${valueOrFallback(task.effort)}
- risk: ${valueOrFallback(task.implementation_risk)}
- routing_confidence_before: ${valueOrFallback(task.routing_confidence)}
- Forbidden: UI-Timer, Clipboard-Zeit, manuelle Dauer-Schätzung oder Dashboard-only Completion.`
}

const buildBlockedPrompt = (task: BacklogItem, reason: string): string => {
  return `BACKLOG HANDOFF NICHT PIPELINE-BEREIT

Grund:
- ${reason}

${buildBacklogContext(task)}

Nächster Schritt:
@[/BACKLOG SKILL 3 – EXECUTION HANDOFF] mit folgendem Backlog Item erneut ausführen:
Mode: SELECTED_HANDOFF
Backlog Item: ${task.id}

Ziel:
- Korrektes Entry-Point-Routing validieren
- Handoff-Artefakt erzeugen oder reparieren
- Recommended next skill eindeutig setzen`
}

const buildSkill1Prompt = (task: BacklogItem): string => {
  if (!isPresent(task.handoff)) {
    return buildBlockedPrompt(task, 'Entry Point verlangt Skill 1, aber es ist kein Spec-Handoff gesetzt.')
  }

  return `@[/SKILL 1 – SPEC TO TASK COMPILER] mit folgender Spec-Datei:
Spec: ${task.handoff.trim()}

${buildBacklogContext(task)}

${buildExecutionTelemetryContract(task)}

Arbeitsregel:
- Nutze die genannte Spec-Datei als verbindliche Single Source of Truth.
- Ignoriere widersprüchliche oder zusätzliche Chat-Kontexte.
- Erzeuge daraus pipeline-fähige atomare Tasks.

Nächster erwarteter Output:
- Skill-1 Task-Datei
- eindeutiger Next Step zu Skill 2 mit Spec- und Task-Artefakt`
}

const buildSpecReviewPrompt = (task: BacklogItem): string => {
  if (!isPresent(task.handoff)) {
    return buildBlockedPrompt(task, 'Spec Review verlangt eine Spec-Datei, aber es ist kein Spec-Handoff gesetzt.')
  }

  const executionMode = formatSpecReviewExecutionMode(task.raw_fields?.['Spec Review Execution Mode'])

  return `@[/SPEC SKILL 1 – REVIEW GATE] mit folgender Spec-Datei:
Spec: ${task.handoff.trim()}
Mode: REVIEW_ONLY
Execution Model: ${executionMode}

Spec-Kontext:
- Spec Item: ${task.id}
- Titel: ${task.title}
- Status: ${valueOrFallback(task.status)}
- Review Status: ${valueOrFallback(task.raw_fields?.['Review Status'])}
- Spec Review Execution Mode: ${valueOrFallback(task.raw_fields?.['Spec Review Execution Mode'])}
- Spec Review Complexity Score: ${valueOrFallback(task.raw_fields?.['Spec Review Complexity Score'])}
- Spec Review Dashboard Hint: ${valueOrFallback(task.raw_fields?.['Spec Review Dashboard Hint'])}
- Spec Review Confidence: ${valueOrFallback(task.raw_fields?.['Spec Review Confidence'])}
- Spec Review Reason: ${valueOrFallback(task.raw_fields?.['Spec Review Reason'])}
- Skill-1 Ready: ${valueOrFallback(task.raw_fields?.['Skill-1 Ready'])}
- Complexity Score: ${valueOrFallback(task.raw_fields?.['Complexity Score'])}
- Risk: ${valueOrFallback(task.raw_fields?.Risk)}

Arbeitsregel:
- Nutze die genannte Spec-Datei als verbindliche Single Source of Truth.
- Ignoriere widersprüchliche oder zusätzliche Chat-Kontexte.
- Nutze für den Review das Modell aus "Execution Model"; nicht selbst ableiten.
- Erzeuge keine Tasks und keine Implementation.
- Prüfe die Spec diamantstandard-konform und schreibe/aktualisiere den Block "SPEC REVIEW METADATA" am Ende der Spec-Datei.

Erwarteter erfolgreicher Zustand:
- Wenn die Spec Skill-1-ready ist: Review Status APPROVED oder APPROVED_WITH_NOTES und Skill-1 Ready YES.
- Danach Dashboard aktualisieren und denselben Kartenbutton erneut verwenden, um den Handover an SKILL 1 zu kopieren.
- Wenn nicht ready: konkrete Refinements, Blocking Question oder Split Recommendation ausgeben.`
}

const buildSkill2Prompt = (task: BacklogItem): string => {
  if (!isPresent(task.handoff)) {
    return buildBlockedPrompt(task, 'Entry Point verlangt Skill 2, aber es ist kein Task-/Spec-Handoff gesetzt.')
  }

  return `@[/SKILL 2 – TASK BREAKDOWN ENGINE] mit folgenden Artefakten:
Spec: ${valueOrFallback(task.raw_fields?.Spec)}
Tasks: ${task.handoff.trim()}

${buildBacklogContext(task)}

${buildExecutionTelemetryContract(task)}

Arbeitsregel:
- Nutze ausschließlich die genannten Artefakte als Requirements-Quellen.
- Validiere/refine Tasks gegen Spec und Backlog-Kontext.
- Gib genau den nächsten Target Task mit Assigned Model frei.

Falls Spec fehlt:
- Nicht raten.
- Mit TASK ARTIFACTS INVALID oder konkreter Artefakt-Anforderung blockieren.`
}

const buildSkill3Prompt = (task: BacklogItem): string => {
  if (!isPresent(task.handoff)) {
    return buildBlockedPrompt(task, 'Entry Point verlangt Skill 3, aber es ist kein Task-Handoff gesetzt.')
  }

  const targetTaskLine = isPresent(task.target_task) ? `Target Task: ${task.target_task.trim()}\n` : ''

  return `@[/SKILL 3 – PRE-IMPLEMENTATION VERIFICATION] mit folgenden Artefakten:
${targetTaskLine}Task: ${task.handoff.trim()}
Backlog Item: ${task.id}

${buildBacklogContext(task)}

${buildExecutionTelemetryContract(task)}

Arbeitsregel:
- Validiere ausschließlich diesen Handoff-Task.
- Nutze die Backlog-Referenz nur zur Konsistenzprüfung.
- Keine Implementierung, keine Codeänderung, keine Scope-Erweiterung.
- Wenn mehrere Tasks in der Datei stehen und Target Task fehlt: PRE-CHECK ARTIFACTS INVALID.

Erwarteter nächster Output:
- PRE-CHECK PASSED oder blockierender Befund
- Copy-Paste-Prompt für Skill 4 mit Assigned Model`
}

const buildSkill4Prompt = (task: BacklogItem): string => {
  if (!isPresent(task.handoff)) {
    return buildBlockedPrompt(task, 'Entry Point verlangt Skill 4, aber es ist kein Task-Handoff gesetzt.')
  }

  if (!isPresent(task.precheck_artifact)) {
    return buildBlockedPrompt(task, 'Execution-ready Handoff ist unvollständig, weil kein Precheck-Artefakt gesetzt ist.')
  }

  return `@[/SKILL 4 – EXECUTIONER] mit folgenden Artefakten:
Target Task: ${valueOrFallback(task.target_task)}
Task: ${task.handoff.trim()}
Pre-Check: ${task.precheck_artifact.trim()}
Backlog Item: ${task.id}

${buildBacklogContext(task)}

${buildExecutionTelemetryContract(task)}

Arbeitsregel:
- Implementiere ausschließlich den genannten Target Task.
- Führe keine späteren Tasks im selben Lauf aus.
- Verwende das im Task/Pre-Check festgelegte Assigned Model.

Erwarteter nächster Output:
- Implementierungsnachweis
- Tests/Validierung
- Compact Audit Handover für Skill 6 nach Abschluss aller Tasks`
}

const buildPipelineHandoverPrompt = (task: BacklogItem): string => {
  const recommendedSkill = valueOrFallback(task.recommended_next_skill, '').toUpperCase()
  const entryPoint = valueOrFallback(task.entry_point, '').toUpperCase()

  if (entryPoint === 'ROUTING_BLOCKED') {
    return buildBlockedPrompt(task, valueOrFallback(task.routing_blocker, 'Routing wurde von Backlog Skill 3 blockiert.'))
  }

  if (recommendedSkill === 'SPEC SKILL 1' || entryPoint === 'SPEC_REVIEW_GATE') {
    return buildSpecReviewPrompt(task)
  }

  if (recommendedSkill === 'SKILL 1' || entryPoint === 'SPEC_PIPELINE_START') {
    return buildSkill1Prompt(task)
  }

  if (recommendedSkill === 'SKILL 2' || entryPoint === 'TASK_BREAKDOWN') {
    return buildSkill2Prompt(task)
  }

  if (recommendedSkill === 'SKILL 3' || entryPoint === 'PRE_IMPLEMENTATION_VERIFICATION') {
    return buildSkill3Prompt(task)
  }

  if (recommendedSkill === 'SKILL 4' || entryPoint === 'EXECUTION_READY') {
    return buildSkill4Prompt(task)
  }

  return buildBlockedPrompt(task, 'Kein eindeutiger Entry Point oder Recommended next skill vorhanden.')
}

export function KanbanCard({ item, viewType = 'active', estimatedTime = null }: KanbanCardProps) {
  const [copied, setCopied] = useState(false)

  const handleCopyHandover = async () => {
    const markdown = buildPipelineHandoverPrompt(item)
    try {
      await navigator.clipboard.writeText(markdown)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch (err) {
      console.error('Failed to copy to clipboard:', err)
    }
  }

  const typeColor = getTypeColor(item)
  const importanceColor = IMPORTANCE_COLORS[item.importance] || IMPORTANCE_COLORS['LOW']
  const handoverButtonLabel = getSpecReviewButtonLabel(item)
  const showSpecReviewRouting = item.type === 'SPEC FEATURE' && item.entry_point === 'SPEC_REVIEW_GATE'

  // Determine which date to display
  const getDateDisplay = () => {
    if (viewType === 'history' && item.completed_at) {
      const date = new Date(item.completed_at)
      return {
        label: 'Bearbeitet',
        date: date.toLocaleDateString('de-DE', { day: '2-digit', month: '2-digit', year: 'numeric' })
      }
    }
    if (viewType === 'active') {
      // For active items, use routing_decided_at or handoff_created as creation date
      const dateStr = item.routing_decided_at || item.handoff_created
      if (dateStr) {
        const date = new Date(dateStr)
        return {
          label: 'Erstellt',
          date: date.toLocaleDateString('de-DE', { day: '2-digit', month: '2-digit', year: 'numeric' })
        }
      }
    }
    return null
  }

  const dateDisplay = getDateDisplay()

  return (
    <div className="bg-card border border-border rounded-lg p-3 hover:border-accent transition-colors w-full min-w-0">
      {/* Top row: ID and Type Badge */}
      <div className="flex items-start justify-between mb-2">
        <span className="text-[10px] font-mono text-muted-foreground break-all">#{item.id}</span>
        <span className={`px-1.5 py-0.5 rounded text-[10px] font-medium ${typeColor.bg} ${typeColor.text} flex-shrink-0`}>
          {item.type}
        </span>
      </div>

      {/* Title */}
      <h3 className="font-semibold text-foreground text-xs mb-2 line-clamp-3 leading-tight break-words overflow-wrap-anywhere">
        {item.title}
      </h3>

      {/* Metrics grid */}
      <div className="grid grid-cols-2 gap-1.5 mb-2">
        <div>
          <p className="text-[9px] text-muted-foreground uppercase tracking-wider">Importance</p>
          <p className={`text-[10px] font-medium ${importanceColor}`}>{item.importance}</p>
        </div>
        <div>
          <p className="text-[9px] text-muted-foreground uppercase tracking-wider">Effort</p>
          <p className="text-[10px] font-medium text-foreground">{item.effort}</p>
        </div>
        <div>
          <p className="text-[9px] text-muted-foreground uppercase tracking-wider">Risk</p>
          <p className="text-[10px] font-medium text-foreground">{item.implementation_risk}</p>
        </div>
        <div>
          <p className="text-[9px] text-muted-foreground uppercase tracking-wider">Status</p>
          <p className="text-[10px] font-medium text-foreground">{item.status}</p>
        </div>
      </div>

      {/* Routing info */}
      {item.entry_point && (
        <div className="mb-2">
          <p className="text-[9px] text-muted-foreground uppercase tracking-wider">Entry Point</p>
          <p className="text-[10px] text-muted-foreground truncate break-all">{item.entry_point}</p>
        </div>
      )}

      {showSpecReviewRouting && (
        <div className="mb-2 grid grid-cols-3 gap-1.5">
          <div>
            <p className="text-[9px] text-muted-foreground uppercase tracking-wider">Review Model</p>
            <p className="text-[10px] font-medium text-foreground">{formatSpecReviewExecutionMode(item.raw_fields?.['Spec Review Execution Mode'])}</p>
          </div>
          <div>
            <p className="text-[9px] text-muted-foreground uppercase tracking-wider">Spec Score</p>
            <p className="text-[10px] font-medium text-foreground">{valueOrFallback(item.raw_fields?.['Spec Review Complexity Score'])}</p>
          </div>
          <div>
            <p className="text-[9px] text-muted-foreground uppercase tracking-wider">Hint</p>
            <p className="text-[10px] font-medium text-foreground">{valueOrFallback(item.raw_fields?.['Spec Review Dashboard Hint'])}</p>
          </div>
        </div>
      )}

      {estimatedTime && (
        <div className="mb-2">
          <p className="text-[9px] text-muted-foreground uppercase tracking-wider">Estimated Time</p>
          <p className="text-[10px] font-medium text-foreground">{estimatedTime.label}</p>
        </div>
      )}

      {/* Date display */}
      {dateDisplay && (
        <div className="mb-2">
          <p className="text-[9px] text-muted-foreground uppercase tracking-wider">{dateDisplay.label}</p>
          <p className="text-[10px] text-muted-foreground">{dateDisplay.date}</p>
        </div>
      )}

      {/* Edit Handover Button */}
      {viewType !== 'history' && (
        <button
          onClick={handleCopyHandover}
          className="w-full flex items-center justify-center gap-1.5 px-2 py-1.5 rounded bg-accent hover:bg-accent/80 text-accent-foreground text-[10px] font-medium transition-colors"
        >
          <Copy className="w-3 h-3" />
          {copied ? 'Copied!' : handoverButtonLabel}
        </button>
      )}
    </div>
  )
}
