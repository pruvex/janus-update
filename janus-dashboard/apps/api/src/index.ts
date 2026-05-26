import Fastify from 'fastify'
import cors from '@fastify/cors'
import { existsSync, readFileSync, readdirSync, statSync } from 'fs'
import { fileURLToPath } from 'url'
import { dirname, join } from 'path'
import type { BacklogCounts, BacklogItem, BacklogPriorityAssessment, BacklogRecommendationResponse, BacklogResponse, TaskExecutionHistoryResponse, TaskExecutionRecord, TestResultRecord, TestResultsResponse, TestOverviewResponse, TestSpecOverview, TestSuiteCategory, TestSuiteResponse } from '../../../shared/types/index.js'

const __filename = fileURLToPath(import.meta.url)
const __dirname = dirname(__filename)

const LOCAL_API_PORT = 3001
const DATA_FILE_PATH = join(__dirname, '../../../data/backlog.snapshot.json')
const TASK_EXECUTION_HISTORY_PATH = join(__dirname, '../../../data/task-execution-history.json')
const BACKLOG_FILE_PATH = join(__dirname, '../../../../documentation/backlog/BACKLOG.md')
const SPEC_DIRECTORY_PATH = join(__dirname, '../../../../documentation/SPEC')
const TEST_SPEC_DIRECTORY_PATH = join(__dirname, '../../../../documentation/TEST_SPEC')
const TEST_RUNS_DIRECTORY_PATH = join(__dirname, '../../../../documentation/test-runs')
const TEST_RESULTS_DIRECTORY_PATH = join(__dirname, '../../../../documentation/test-results')

const ITEM_HEADING_PATTERN = /^###\s+(BACKLOG-\d+)\s+(?:–|—|â€“|Ã¢â‚¬â€œ|-)\s+(.+?)\s*$/
const SECTION_PATTERN = /^##\s+(.+?)\s*$/
const FIELD_PATTERN = /^-\s+\*\*(.+?):\*\*\s*(.*)$/
const SPEC_REVIEW_METADATA_HEADING = /^##\s+SPEC REVIEW METADATA\s*$/i
const SPEC_IMPLEMENTATION_METADATA_HEADING = /^##\s+SPEC IMPLEMENTATION METADATA\s*$/i
const SPEC_REVIEW_EXECUTION_ROUTING_HEADING = /^(?:##\s+)?[^\w#]*\s*SPEC REVIEW EXECUTION ROUTING\s*$/i

const FIELD_ALIASES: Record<string, keyof BacklogItem> = {
  'Typ': 'type',
  'Status': 'status',
  'Wichtigkeit': 'importance',
  'Umsetzungsrisiko': 'implementation_risk',
  'Aufwand': 'effort',
  'Umsetzungsreife': 'readiness',
  'Empfehlung': 'recommendation',
  'Entry Point': 'entry_point',
  'Routing reason': 'routing_reason',
  'Routing confidence': 'routing_confidence',
  'Routing decided by': 'routing_decided_by',
  'Routing decided at': 'routing_decided_at',
  'Routing blocker': 'routing_blocker',
  'Handoff': 'handoff',
  'Recommended next skill': 'recommended_next_skill',
  'Handoff created': 'handoff_created',
  'Precheck artifact': 'precheck_artifact',
  'Target Task': 'target_task',
  'Completed in version': 'completed_in_version',
  'Completed by task': 'completed_by_task',
  'Completed at': 'completed_at',
  'Abgeschlossen': 'completed_at',
  'Final audit': 'final_audit',
  'Validation evidence': 'validation_evidence',
  'Changelog': 'changelog',
}

const COUNT_KEYS: Record<string, keyof Pick<BacklogCounts, 'needs_info' | 'ready' | 'in_progress' | 'done' | 'blocked'>> = {
  'NEEDS INFO': 'needs_info',
  'READY': 'ready',
  'IN PROGRESS': 'in_progress',
  'DONE': 'done',
  'BLOCKED': 'blocked',
}

const IMPORTANCE_SCORE: Record<string, number> = {
  CRITICAL: 40,
  HIGH: 30,
  MEDIUM: 18,
  LOW: 8,
}

const RISK_SCORE: Record<string, number> = {
  LOW: 10,
  MEDIUM: 0,
  HIGH: -10,
}

const EFFORT_SCORE: Record<string, number> = {
  XS: 16,
  S: 12,
  M: 6,
  L: -4,
  XL: -12,
}

const STATUS_SCORE: Record<string, number> = {
  'IN PROGRESS': 18,
  READY: 14,
  'NEEDS INFO': -35,
  BLOCKED: -45,
}

const RECOMMENDATION_SCORE: Record<string, number> = {
  'DO NOW': 24,
  SCHEDULE: 8,
  'NEEDS INFO FIRST': -20,
  DEFER: -15,
  'DO NOT START': -40,
  COMPLETED: -80,
}

const ENTRY_POINT_SCORE: Record<string, number> = {
  EXECUTION_READY: 18,
  PRE_IMPLEMENTATION_VERIFICATION: 14,
  SPEC_PIPELINE_START: 12,
  TASK_BREAKDOWN: 10,
  SPEC_REVIEW_GATE: 6,
  ROUTING_BLOCKED: -40,
}

const CONFIDENCE_SCORE: Record<string, number> = {
  HIGH: 8,
  MEDIUM: 4,
  LOW: 0,
}

const fastify = Fastify({
  logger: true,
})

await fastify.register(cors as any, {
  origin: '*',
})

function createBacklogItem(id: string, title: string): BacklogItem {
  return {
    id,
    title,
    section: '',
    type: '',
    status: '',
    importance: '',
    implementation_risk: '',
    effort: '',
    readiness: '',
    recommendation: '',
    entry_point: '',
    routing_reason: '',
    routing_confidence: '',
    routing_decided_by: null,
    routing_decided_at: null,
    routing_blocker: null,
    handoff: '',
    recommended_next_skill: '',
    handoff_created: null,
    precheck_artifact: null,
    target_task: null,
    completed_in_version: null,
    completed_by_task: null,
    completed_at: null,
    final_audit: null,
    validation_evidence: null,
    changelog: null,
    is_test_blocker: false,
    raw_fields: {},
  }
}

function createSpecItem(filePath: string, relativePath: string, text: string): BacklogItem {
  const metadata = parseSpecReviewMetadata(text)
  const implementationMetadata = parseSpecImplementationMetadata(text)
  const executionRouting = parseSpecExecutionRouting(text)
  const family = inferSpecFamily(relativePath, text)
  const reviewStatus = (metadata['Review Status'] || '').toUpperCase()
  const skillReady = (metadata['Skill-1 Ready'] || '').toUpperCase()
  const implementationStatus = (implementationMetadata['Implementation Status'] || '').toUpperCase()
  const finalAudit = (implementationMetadata['Final Audit'] || implementationMetadata['Audit Result'] || '').toUpperCase()
  const executionMode = normalizeSpecExecutionMode(executionRouting.execution_mode)
  const routingComplexityScore = normalizeSpecComplexityScore(executionRouting.complexity_score)
  const dashboardHint = normalizeSpecDashboardHint(executionRouting.dashboard_hint)
  const routingConfidence = normalizeSpecConfidence(executionRouting.confidence)
  const isSkillReady = skillReady === 'YES' && (reviewStatus === 'APPROVED' || reviewStatus === 'APPROVED_WITH_NOTES')
  const isImplementationComplete = implementationStatus === 'DONE' || implementationStatus === 'COMPLETE'
  const isImplementationDone = isImplementationComplete && (finalAudit === 'PASS' || finalAudit === 'PASS WITH FIXES')
  const item = createBacklogItem(`SPEC-${slugifySpecId(relativePath)}`, extractSpecTitle(text, relativePath))
  const fileStat = statSync(filePath)

  item.type = 'SPEC FEATURE'
  item.status = isImplementationDone ? 'DONE' : isSkillReady ? 'READY' : 'TO REVIEW'
  item.importance = 'MEDIUM'
  item.implementation_risk = isSkillReady ? normalizeSpecRisk(metadata.Risk) : normalizeSpecRisk(dashboardHint)
  item.effort = normalizeSpecEffort(metadata['Complexity Score'] || routingComplexityScore)
  item.readiness = isImplementationDone ? 'COMPLETED' : isSkillReady ? 'READY' : 'NEEDS REVIEW'
  item.recommendation = isImplementationDone ? 'COMPLETED' : isSkillReady ? 'DO NOW' : `SPEC REVIEW AUSFÜHREN MIT ${formatSpecExecutionMode(executionMode)}`
  item.entry_point = isImplementationDone ? 'COMPLETED' : isSkillReady ? 'SPEC_PIPELINE_START' : 'SPEC_REVIEW_GATE'
  item.routing_reason = isImplementationDone
    ? 'Spec wurde nach erfolgreichem Skill-6-Final-Audit abgeschlossen.'
    : isSkillReady
    ? 'Spec wurde durch SPEC SKILL 1 geprüft und ist Skill-1-ready.'
    : executionRouting.reason || 'Spec liegt in documentation/SPEC, aber der SPEC SKILL 1 Review ist noch nicht abgeschlossen.'
  item.routing_confidence = isSkillReady ? normalizeSpecConfidence(metadata['Review Confidence']) : routingConfidence
  item.routing_decided_by = 'janus-dashboard spec scanner'
  item.routing_decided_at = formatDate(fileStat.mtime)
  item.handoff = normalizePathForPrompt(relativePath)
  item.recommended_next_skill = isImplementationDone ? '' : isSkillReady ? 'SKILL 1' : 'SPEC SKILL 1'
  item.handoff_created = formatDate(fileStat.mtime)
  item.completed_at = isImplementationDone ? implementationMetadata['Completed At'] || implementationMetadata['Implementation Date'] || implementationMetadata['Audit Date'] || formatDate(fileStat.mtime) : null
  item.completed_by_task = isImplementationDone ? implementationMetadata['Completed By'] || 'SKILL 6 – DIAMANTSTANDARD FINAL AUDIT' : null
  item.final_audit = isImplementationDone ? finalAudit : null
  item.validation_evidence = isImplementationDone ? implementationMetadata['Validation Evidence'] || null : null
  item.raw_fields = {
    Spec: normalizePathForPrompt(relativePath),
    'Spec Document Kind': family.kind,
    'Spec Feature Group Id': family.groupId,
    'Spec Feature Group Label': family.groupLabel,
    'Spec Pair Key': family.pairKey,
    'Spec Sequence Order': String(family.sequenceOrder),
    'Spec Pair Order': String(family.pairOrder),
    'Review Status': reviewStatus || 'TO REVIEW',
    'Skill-1 Ready': skillReady || 'NO',
    'Complexity Score': metadata['Complexity Score'] || '',
    Risk: metadata.Risk || '',
    'Recommended Review Model': metadata['Recommended Review Model'] || '',
    'Reviewed At': metadata['Reviewed At'] || '',
    'Review Source': metadata['Review Source'] || '',
    'Spec Review Target Skill': executionRouting.target_skill || '',
    'Spec Review Execution Mode': executionMode,
    'Spec Review Complexity Score': routingComplexityScore,
    'Spec Review Dashboard Hint': dashboardHint,
    'Spec Review Confidence': routingConfidence,
    'Spec Review Reason': executionRouting.reason || '',
    'Implementation Status': isImplementationDone ? 'DONE' : implementationStatus || '',
    'Final Audit': finalAudit || '',
    'Completed At': implementationMetadata['Completed At'] || implementationMetadata['Implementation Date'] || implementationMetadata['Audit Date'] || '',
    'Completed By': implementationMetadata['Completed By'] || '',
    'Validation Evidence': implementationMetadata['Validation Evidence'] || '',
  }

  return item
}

function inferSpecFamily(relativePath: string, text: string): {
  kind: 'FEATURE_SPEC' | 'TEST_SPEC'
  groupId: string
  groupLabel: string
  pairKey: string
  pairOrder: number
  sequenceOrder: number
} {
  const normalizedPath = relativePath.replace(/\\/g, '/')
  const fileName = normalizedPath.split('/').pop() || normalizedPath
  const numericPrefix = Number.parseInt(/^(\d+)_/.exec(fileName)?.[1] || '', 10)
  const isTestSpec = /^#\s+JANUS TESTSPEC\b/i.test(text) || numericPrefix >= 7
  const sourceFeatureSpec = /^-\s+Source Feature Spec:\s*(.+?)\s*$/im.exec(text)?.[1]?.trim() || ''
  const sourceFileName = sourceFeatureSpec.split(/[\\/]/).pop() || ''
  const sourcePrefix = Number.parseInt(/^(\d+)_/.exec(sourceFileName)?.[1] || '', 10)
  const pairOrder = Number.isFinite(sourcePrefix)
    ? sourcePrefix
    : Number.isFinite(numericPrefix)
    ? numericPrefix <= 3 ? numericPrefix : numericPrefix - 6
    : 999
  const pairKey = String(pairOrder).padStart(2, '0')
  const groupId = normalizedPath.toLowerCase().includes('personalization')
    || normalizedPath.toLowerCase().includes('contextual_memory')
    || normalizedPath.toLowerCase().includes('proactive_companion')
    || sourceFeatureSpec.toLowerCase().includes('personalization')
    ? 'personalization-memory-companion'
    : normalizedPath.split('/')[0].replace(/[^a-z0-9]+/gi, '-').toLowerCase()
  const groupLabel = groupId === 'personalization-memory-companion'
    ? 'Personalization + Memory Companion'
    : groupId.replace(/[-_]+/g, ' ').replace(/\b\w/g, (char) => char.toUpperCase())

  return {
    kind: isTestSpec ? 'TEST_SPEC' : 'FEATURE_SPEC',
    groupId,
    groupLabel,
    pairKey,
    pairOrder,
    sequenceOrder: pairOrder * 10 + (isTestSpec ? 1 : 0),
  }
}

function parseSpecReviewMetadata(text: string): Record<string, string> {
  return parseSpecKeyValueBlock(text, SPEC_REVIEW_METADATA_HEADING)
}

function parseSpecImplementationMetadata(text: string): Record<string, string> {
  return parseSpecKeyValueBlock(text, SPEC_IMPLEMENTATION_METADATA_HEADING)
}

function parseSpecExecutionRouting(text: string): Record<string, string> {
  return parseSpecKeyValueBlock(text, SPEC_REVIEW_EXECUTION_ROUTING_HEADING, true)
}

function parseSpecKeyValueBlock(text: string, headingPattern: RegExp, canonicalizeKeys = false): Record<string, string> {
  const values: Record<string, string> = {}
  const lines = text.split(/\r?\n/)
  const startIndex = lines.findIndex((line) => headingPattern.test(line.trim()))

  if (startIndex === -1) {
    return values
  }

  for (let index = startIndex + 1; index < lines.length; index += 1) {
    const line = lines[index].trim()
    if (/^##\s+/.test(line) || /^[^\w#]*\s*[A-Z0-9 _-]+(?:BLOCK|SECTION|METADATA)\s*$/i.test(line)) {
      break
    }

    if (!line || line.startsWith('```') || line === '{' || line === '}') {
      continue
    }

    const fieldMatch = FIELD_PATTERN.exec(line)
    if (fieldMatch) {
      const key = normalizeSpecBlockKey(fieldMatch[1], canonicalizeKeys)
      values[key] = normalizeSpecBlockValue(fieldMatch[2])
      continue
    }

    const keyValueMatch = /^[-\s]*["']?([^:"']+)["']?\s*:\s*["']?(.+?)["']?,?\s*$/.exec(line)
    if (keyValueMatch) {
      const key = normalizeSpecBlockKey(keyValueMatch[1], canonicalizeKeys)
      values[key] = normalizeSpecBlockValue(keyValueMatch[2])
      continue
    }

    const keyOnlyMatch = /^[-\s]*["']?([^:"']+)["']?\s*:\s*$/.exec(line)
    if (keyOnlyMatch) {
      const nextValue = findNextSpecBlockValue(lines, index + 1)
      if (nextValue) {
        const key = normalizeSpecBlockKey(keyOnlyMatch[1], canonicalizeKeys)
        values[key] = normalizeSpecBlockValue(nextValue)
      }
    }
  }

  return values
}

function normalizeSpecBlockKey(value: string, canonicalizeKeys: boolean): string {
  if (!canonicalizeKeys) {
    return value.trim()
  }

  const key = value
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '_')
    .replace(/^_+|_+$/g, '')

  if (key === 'routing_reason') {
    return 'reason'
  }

  return key
}

function normalizeSpecBlockValue(value: string): string {
  return value.trim().replace(/^["']|["'],?$/g, '').replace(/,$/, '').trim()
}

function findNextSpecBlockValue(lines: string[], startIndex: number): string {
  for (let index = startIndex; index < lines.length; index += 1) {
    const candidate = lines[index].trim()
    if (!candidate || candidate.startsWith('```') || candidate === '{' || candidate === '}') {
      continue
    }
    if (/^##\s+/.test(candidate) || /^[-\s]*["']?([^:"']+)["']?\s*:\s*$/.test(candidate)) {
      return ''
    }
    return candidate
  }

  return ''
}

function extractSpecTitle(text: string, relativePath: string): string {
  const heading = text.split(/\r?\n/).find((line) => /^#\s+/.test(line.trim()))
  if (heading) {
    const title = heading.replace(/^#\s+/, '').trim()
    if (!/^JANUS (?:FEATURE SPEC|TESTSPEC)\b/i.test(title)) {
      return title
    }
  }

  const explicitName = text
    .split(/\r?\n/)
    .map((line) => /^-\s+\*?\*?(?:Feature Name|Spec Name|TestSpec Name)\*?\*?:\s*(.+?)\s*$/.exec(line.trim()))
    .find((match): match is RegExpExecArray => Boolean(match))?.[1]

  if (explicitName) {
    return explicitName.trim()
  }

  return relativePath.split(/[\\/]/).pop()?.replace(/\.md$/i, '').replace(/[-_]+/g, ' ') || relativePath
}

function slugifySpecId(relativePath: string): string {
  return relativePath
    .replace(/\.md$/i, '')
    .toUpperCase()
    .replace(/[^A-Z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '')
}

function normalizeSpecRisk(value: string | undefined): string {
  const risk = value?.trim().toUpperCase()
  if (risk === 'CRITICAL' || risk === 'HIGH') {
    return 'HIGH'
  }
  if (risk === 'MEDIUM' || risk === 'CAUTION') {
    return 'MEDIUM'
  }
  return 'LOW'
}

function normalizeSpecEffort(value: string | undefined): string {
  const score = Number.parseInt(value || '', 10)
  if (!Number.isFinite(score)) {
    return 'M'
  }
  if (score <= 20) {
    return 'XS'
  }
  if (score <= 40) {
    return 'S'
  }
  if (score <= 60) {
    return 'M'
  }
  if (score <= 80) {
    return 'L'
  }
  return 'XL'
}

function normalizeSpecConfidence(value: string | undefined): string {
  const confidence = value?.trim().toUpperCase()
  if (confidence === 'LOW' || confidence === 'MEDIUM' || confidence === 'HIGH') {
    return confidence
  }
  return 'MEDIUM'
}

function normalizeSpecExecutionMode(value: string | undefined): string {
  const mode = value?.trim().toUpperCase()
  if (mode === 'SWE_1_6' || mode === 'GPT_5_5') {
    return mode
  }
  return ''
}

function formatSpecExecutionMode(value: string): string {
  if (value === 'SWE_1_6') {
    return 'SWE 1.6'
  }
  if (value === 'GPT_5_5') {
    return 'GPT-5.5'
  }
  return 'MODELL FEHLT'
}

function normalizeSpecComplexityScore(value: string | undefined): string {
  const score = Number.parseInt(value || '', 10)
  if (!Number.isFinite(score)) {
    return ''
  }
  return String(Math.min(100, Math.max(0, score)))
}

function normalizeSpecDashboardHint(value: string | undefined): string {
  const hint = value?.trim().toUpperCase()
  if (hint === 'SAFE' || hint === 'CAUTION' || hint === 'CRITICAL') {
    return hint
  }
  return ''
}

function formatDate(date: Date): string {
  return date.toISOString().slice(0, 10)
}

function normalizePathForPrompt(relativePath: string): string {
  return `documentation/SPEC/${relativePath.replace(/\\/g, '/')}`
}

function readSpecItems(): BacklogItem[] {
  if (!existsSync(SPEC_DIRECTORY_PATH)) {
    return []
  }

  const items: BacklogItem[] = []
  const stack = ['']

  while (stack.length > 0) {
    const currentRelativeDirectory = stack.pop() || ''
    const absoluteDirectory = join(SPEC_DIRECTORY_PATH, currentRelativeDirectory)
    const entries = readdirSync(absoluteDirectory, { withFileTypes: true })

    for (const entry of entries) {
      const relativePath = currentRelativeDirectory ? join(currentRelativeDirectory, entry.name) : entry.name
      const absolutePath = join(SPEC_DIRECTORY_PATH, relativePath)

      if (entry.isDirectory()) {
        stack.push(relativePath)
        continue
      }

      if (!entry.isFile() || !entry.name.toLowerCase().endsWith('.md')) {
        continue
      }

      items.push(createSpecItem(absolutePath, relativePath, readFileSync(absolutePath, 'utf-8')))
    }
  }

  return items.sort((left, right) => left.id.localeCompare(right.id))
}

function isContinuationLine(line: string): boolean {
  const stripped = line.trim()
  if (!stripped) {
    return false
  }
  if (stripped.startsWith('###') || stripped.startsWith('##')) {
    return false
  }
  if (FIELD_PATTERN.test(stripped)) {
    return false
  }
  return line.startsWith(' ') || stripped.startsWith('-')
}

function normalizeItems(items: BacklogItem[]) {
  for (const item of items) {
    item.status = item.status ? item.status.toUpperCase() : ''
    item.section = item.section ? item.section.toUpperCase() : ''
    if (COUNT_KEYS[item.status]) {
      item.section = item.status
    }
    item.entry_point = item.entry_point ? item.entry_point.toUpperCase() : ''
    item.routing_confidence = item.routing_confidence ? item.routing_confidence.toUpperCase() : ''
    item.recommended_next_skill = item.recommended_next_skill ? item.recommended_next_skill.toUpperCase() : ''
  }
}

function buildCounts(items: BacklogItem[]): BacklogCounts {
  const counts: BacklogCounts = {
    total: items.length,
    active: 0,
    history: 0,
    needs_info: 0,
    ready: 0,
    in_progress: 0,
    done: 0,
    blocked: 0,
    routing_missing: 0,
    routing_blocked: 0,
  }

  for (const item of items) {
    const status = item.status || ''
    const countKey = COUNT_KEYS[status]
    if (countKey) {
      counts[countKey] += 1
    }
    if (status === 'DONE') {
      counts.history += 1
    } else {
      counts.active += 1
    }
    if (!item.entry_point && status !== 'DONE') {
      counts.routing_missing += 1
    }
    if (item.entry_point === 'ROUTING_BLOCKED') {
      counts.routing_blocked += 1
    }
  }

  return counts
}

function valueScore(value: string | null | undefined, table: Record<string, number>, fallback = 0): number {
  const key = (value || '').trim().toUpperCase()
  return table[key] ?? fallback
}

function hasCompletionEvidence(item: BacklogItem): boolean {
  const evidenceText = [
    item.completed_at,
    item.completed_by_task,
    item.completed_in_version,
    item.final_audit,
    item.validation_evidence,
  ]
    .filter(Boolean)
    .join(' ')
    .toUpperCase()

  return (
    item.status !== 'DONE' &&
    (
      evidenceText.includes('PASS') ||
      evidenceText.includes('DONE') ||
      evidenceText.includes('COMPLETE') ||
      evidenceText.includes('TEST-RUN-')
    )
  )
}

function ageScore(item: BacklogItem): number {
  const rawDate = item.routing_decided_at || item.handoff_created
  if (!rawDate) {
    return 0
  }

  const timestamp = Date.parse(rawDate)
  if (!Number.isFinite(timestamp)) {
    return 0
  }

  const ageDays = Math.floor((Date.now() - timestamp) / (24 * 60 * 60 * 1000))
  if (ageDays >= 30) return 8
  if (ageDays >= 14) return 5
  if (ageDays >= 7) return 3
  return 0
}

function buildAssessmentReason(item: BacklogItem, score: number, completionEvidence: boolean): string {
  if (completionEvidence) {
    return 'Hat Abschluss-/Validierungshinweise, steht aber noch in Active. Erst Status und Dokumentation pruefen.'
  }
  if (item.status === 'BLOCKED' || item.entry_point === 'ROUTING_BLOCKED') {
    return 'Blockiert: Ursache klaeren, bevor Umsetzung gestartet wird.'
  }
  if (item.status === 'NEEDS INFO') {
    return 'Es fehlen Pflichtinformationen; zuerst Intake/Triage abschliessen.'
  }
  if ((item.recommendation || '').toUpperCase() === 'DO NOW') {
    return 'Hoechste fachliche Empfehlung plus pipeline-faehige Routing-Daten.'
  }
  if (score >= 70) {
    return 'Hoher Nutzwert bei vertretbarem Risiko und klarer Routing-Spur.'
  }
  if (score >= 45) {
    return 'Solide vorbereitet, aber nicht der staerkste Hebel im Active-Pool.'
  }
  return 'Nachrangig gegenueber besser bewerteten Active-Items.'
}

function buildRecommendedAction(item: BacklogItem, completionEvidence: boolean): string {
  if (completionEvidence) {
    return `Pruefe Abschlussnachweise fuer ${item.id}; falls korrekt, per Skill 7 auf DONE dokumentieren.`
  }
  if (item.status === 'BLOCKED' || item.entry_point === 'ROUTING_BLOCKED') {
    return `Klaere Blocker fuer ${item.id}, bevor Implementierung beginnt.`
  }
  if (item.status === 'NEEDS INFO') {
    return `Fuehre BACKLOG SKILL 1 Intake fuer ${item.id} aus.`
  }

  const skill = (item.recommended_next_skill || '').trim()
  if (skill) {
    return `Starte ${skill} fuer ${item.id}.`
  }

  return `Priorisiere ${item.id} nach Backlog-Review.`
}

function buildPriorityAssessments(items: BacklogItem[]): BacklogPriorityAssessment[] {
  const activeItems = items.filter((item) => item.status !== 'DONE')

  const ranked = activeItems
    .map((item) => {
      const completionEvidence = hasCompletionEvidence(item)
      let score =
        valueScore(item.importance, IMPORTANCE_SCORE) +
        valueScore(item.implementation_risk, RISK_SCORE) +
        valueScore(item.effort, EFFORT_SCORE) +
        valueScore(item.status, STATUS_SCORE) +
        valueScore(item.recommendation, RECOMMENDATION_SCORE) +
        valueScore(item.entry_point, ENTRY_POINT_SCORE) +
        valueScore(item.routing_confidence, CONFIDENCE_SCORE) +
        ageScore(item)

      if (item.is_test_blocker) {
        score += 10
      }
      if (!item.handoff && item.status !== 'NEEDS INFO') {
        score -= 12
      }
      if (completionEvidence) {
        score = Math.min(score, 12)
      }

      score = Math.max(0, Math.min(100, Math.round(score)))

      let label: BacklogPriorityAssessment['label'] = 'WAIT'
      if (completionEvidence) {
        label = 'VERIFY DONE'
      } else if (item.status === 'BLOCKED' || item.entry_point === 'ROUTING_BLOCKED') {
        label = 'BLOCKED'
      } else if (item.status === 'NEEDS INFO') {
        label = 'REVIEW'
      } else if (score >= 75) {
        label = 'DO NEXT'
      } else if (score >= 45) {
        label = 'READY'
      }

      return {
        taskId: item.id,
        score,
        rank: 0,
        label,
        reason: buildAssessmentReason(item, score, completionEvidence),
        recommendedAction: buildRecommendedAction(item, completionEvidence),
        recommendedSkill: item.recommended_next_skill || '',
        completionEvidence,
      }
    })
    .sort((left, right) => {
      if (left.completionEvidence !== right.completionEvidence) {
        return left.completionEvidence ? 1 : -1
      }
      return right.score - left.score
    })

  return ranked.map((assessment, index) => ({
    ...assessment,
    rank: index + 1,
  }))
}

function readBacklogRecommendations(): BacklogRecommendationResponse {
  const backlog = readBacklogData()
  const assessments = buildPriorityAssessments(backlog.items)
  return {
    schema: 'janus-dashboard.backlog-recommendations.v1',
    source: backlog.source,
    generated_at: new Date().toISOString(),
    active_count: assessments.length,
    recommended_next: assessments[0] || null,
    assessments,
  }
}

function parseBacklogText(text: string, source: string): BacklogResponse {
  const items: BacklogItem[] = []
  let currentSection = ''
  let currentItem: BacklogItem | null = null
  let currentField: keyof BacklogItem | null = null

  for (const rawLine of text.split(/\r?\n/)) {
    const line = rawLine.replace(/\s+$/, '')
    const sectionMatch = SECTION_PATTERN.exec(line)
    if (sectionMatch && !line.startsWith('###')) {
      if (currentItem) {
        items.push(currentItem)
        currentItem = null
      }
      currentSection = sectionMatch[1].trim()
      currentField = null
      continue
    }

    const itemMatch = ITEM_HEADING_PATTERN.exec(line)
    if (itemMatch) {
      if (currentItem) {
        items.push(currentItem)
      }
      currentItem = createBacklogItem(itemMatch[1].trim(), itemMatch[2].trim())
      currentItem.section = currentSection
      currentField = null
      continue
    }

    if (!currentItem) {
      continue
    }

    const fieldMatch = FIELD_PATTERN.exec(line)
    if (fieldMatch) {
      const fieldName = fieldMatch[1].trim()
      const value = fieldMatch[2].trim()
      const attrName = FIELD_ALIASES[fieldName]
      currentItem.raw_fields[fieldName] = value
      if (attrName && attrName !== 'raw_fields') {
        ;(currentItem[attrName] as string | null) = value
        currentField = attrName
      } else {
        currentField = null
      }
      continue
    }

    if (currentField && isContinuationLine(line)) {
      const previous = currentItem[currentField]
      const continuation = line.trim()
      if (continuation) {
        ;(currentItem[currentField] as string | null) = previous ? `${previous}\n${continuation}` : continuation
      }
    }
  }

  if (currentItem) {
    items.push(currentItem)
  }

  normalizeItems(items)
  return {
    source,
    items,
    counts: buildCounts(items),
  }
}

function readBacklogData(): BacklogResponse {
  try {
    const snapshot = JSON.parse(readFileSync(DATA_FILE_PATH, 'utf-8')) as BacklogResponse
    const snapshotMtime = statSync(DATA_FILE_PATH).mtimeMs
    const backlogMtime = statSync(BACKLOG_FILE_PATH).mtimeMs
    if (backlogMtime > snapshotMtime) {
      fastify.log.warn('Backlog snapshot is stale, returning live parsed backlog data')
      const text = readFileSync(BACKLOG_FILE_PATH, 'utf-8')
      const parsedBacklog = parseBacklogText(text, BACKLOG_FILE_PATH)
      const items = [...parsedBacklog.items, ...readSpecItems()]
      return {
        ...parsedBacklog,
        items,
        counts: buildCounts(items),
        snapshot_path: DATA_FILE_PATH,
        is_stale: true,
      }
    }
    const items = [...snapshot.items, ...readSpecItems()]
    return {
      ...snapshot,
      items,
      counts: buildCounts(items),
      snapshot_path: DATA_FILE_PATH,
      is_stale: false,
    }
  } catch (error) {
    fastify.log.warn({ error }, 'Falling back to live parsed backlog data')
    const text = readFileSync(BACKLOG_FILE_PATH, 'utf-8')
    const parsedBacklog = parseBacklogText(text, BACKLOG_FILE_PATH)
    const items = [...parsedBacklog.items, ...readSpecItems()]
    return {
      ...parsedBacklog,
      items,
      counts: buildCounts(items),
      snapshot_path: DATA_FILE_PATH,
      is_stale: true,
    }
  }
}

function isTaskExecutionRecord(record: unknown): record is TaskExecutionRecord {
  if (!record || typeof record !== 'object') {
    return false
  }

  const candidate = record as Partial<TaskExecutionRecord>
  return (
    typeof candidate.execution_id === 'string' &&
    typeof candidate.task_id === 'string' &&
    typeof candidate.task_type === 'string' &&
    typeof candidate.skill_used === 'string' &&
    typeof candidate.importance === 'string' &&
    typeof candidate.effort === 'string' &&
    typeof candidate.risk === 'string' &&
    typeof candidate.started_at === 'string' &&
    typeof candidate.finished_at === 'string' &&
    typeof candidate.duration_minutes === 'number' &&
    Number.isFinite(candidate.duration_minutes) &&
    candidate.duration_minutes >= 0 &&
    typeof candidate.successful === 'boolean' &&
    typeof candidate.reopened === 'boolean' &&
    typeof candidate.source === 'string'
  )
}

function readTaskExecutionHistory(): TaskExecutionHistoryResponse {
  try {
    const data = JSON.parse(readFileSync(TASK_EXECUTION_HISTORY_PATH, 'utf-8')) as Partial<TaskExecutionHistoryResponse>
    const records = Array.isArray(data.records) ? data.records.filter(isTaskExecutionRecord) : []

    return {
      schema: data.schema || 'janus-dashboard.task_execution_history.v1',
      updated_at: data.updated_at || null,
      source: TASK_EXECUTION_HISTORY_PATH,
      records,
    }
  } catch (error) {
    fastify.log.warn({ error }, 'Task execution history unavailable, returning empty completed history')
    return {
      schema: 'janus-dashboard.task_execution_history.v1',
      updated_at: null,
      source: TASK_EXECUTION_HISTORY_PATH,
      records: [],
    }
  }
}

function isTestResultRecord(record: unknown): record is TestResultRecord {
  if (!record || typeof record !== 'object') {
    return false
  }

  const candidate = record as Partial<TestResultRecord>
  const validStatus = typeof candidate.status === 'string' && ['PASS', 'FAIL', 'PARTIAL', 'BLOCKED', 'RUNNING'].includes(candidate.status)
  const summary = candidate.summary as Partial<TestResultRecord['summary']> | undefined
  const artifacts = candidate.artifacts as Partial<TestResultRecord['artifacts']> | undefined

  return (
    candidate.schemaVersion === 'janus.test-result.v1' &&
    typeof candidate.testRunId === 'string' &&
    /^TEST-RUN-\d{4}-\d{2}-\d{2}-\d{3}$/.test(candidate.testRunId) &&
    validStatus &&
    typeof summary?.total === 'number' &&
    typeof summary?.passed === 'number' &&
    typeof summary?.failed === 'number' &&
    typeof summary?.blocked === 'number' &&
    typeof summary?.manualGateRequired === 'number' &&
    Array.isArray(candidate.results) &&
    candidate.results.every((result) => (
      result &&
      typeof result === 'object' &&
      typeof result.testCaseId === 'string' &&
      typeof result.result === 'string' &&
      typeof result.classification === 'string' &&
      typeof result.evidencePath === 'string'
    )) &&
    typeof artifacts?.resultDirectory === 'string' &&
    typeof artifacts?.resultJson === 'string' &&
    Array.isArray(artifacts?.evidenceFiles) &&
    typeof candidate.updatedAt === 'string'
  )
}

function readTestResults(): TestResultsResponse {
  if (!existsSync(TEST_RESULTS_DIRECTORY_PATH)) {
    return {
      schema: 'janus-dashboard.test-results.v1',
      source: TEST_RESULTS_DIRECTORY_PATH,
      records: [],
    }
  }

  const records: TestResultRecord[] = []
  const entries = readdirSync(TEST_RESULTS_DIRECTORY_PATH, { withFileTypes: true })

  for (const entry of entries) {
    if (!entry.isFile() || !entry.name.endsWith('_results.json')) {
      continue
    }

    const resultPath = join(TEST_RESULTS_DIRECTORY_PATH, entry.name)
    try {
      const parsed = JSON.parse(readFileSync(resultPath, 'utf-8')) as unknown
      if (isTestResultRecord(parsed)) {
        records.push(parsed)
      } else {
        fastify.log.warn({ resultPath }, 'Ignoring invalid machine-readable test result')
      }
    } catch (error) {
      fastify.log.warn({ error, resultPath }, 'Ignoring unreadable machine-readable test result')
    }
  }

  records.sort((left, right) => {
    const rightTime = Date.parse(right.updatedAt) || 0
    const leftTime = Date.parse(left.updatedAt) || 0
    return rightTime - leftTime
  })

  return {
    schema: 'janus-dashboard.test-results.v1',
    source: TEST_RESULTS_DIRECTORY_PATH,
    records,
  }
}

interface TestSpecMetadata {
  specId: string
  fileName: string
  path: string
  categoryId: string
  categoryLabel: string
  categoryOrder: number
  title: string
  capability: string
  description: string
  reliableBehavior: string
  matchKeys: string[]
}

type TestRunPlan = Record<string, any> & {
  testRunId?: string
  tests?: Array<{ id?: string; type?: string; provider?: string }>
}

const TEST_SUITE_CATEGORIES = [
  {
    id: '01_core_system',
    label: 'Core System',
    description: 'Intent Engine, Routing, Planner und Architekturverhalten.',
  },
  {
    id: '02_security_safety',
    label: 'Security & Safety',
    description: 'Security, Privacy, Prompt-Injection und riskante Aktionen.',
  },
  {
    id: '03_tools_skills',
    label: 'Tools & Skills',
    description: 'Filesystem, APIs, Skill-Auswahl und Tool-Evidence.',
  },
  {
    id: '04_memory_context',
    label: 'Memory & Context',
    description: 'Memory, Kalender, Kontext, Privacy und Personalisierung.',
  },
  {
    id: '05_ux_behavior',
    label: 'UX & Behavior',
    description: 'Antwortqualitaet, Help, Evidence Honesty und Nutzerfuehrung.',
  },
  {
    id: '06_efficiency_cost',
    label: 'Efficiency & Cost',
    description: 'Latenz, Tokenverbrauch, Caching und Modell-Disziplin.',
  },
  {
    id: '07_regression_suite',
    label: 'Regression Suite',
    description: 'Gezielte Nachtests fuer reparierte Bugs und stabile Releases.',
  },
] as const

type TestSuiteCategoryDefinition = (typeof TEST_SUITE_CATEGORIES)[number]

function categoryDefinitionFor(relativePath: string): TestSuiteCategoryDefinition {
  const firstSegment = relativePath.split(/[\\/]/)[0]
  return TEST_SUITE_CATEGORIES.find((category) => category.id === firstSegment) || TEST_SUITE_CATEGORIES[0]
}

function collectMarkdownFiles(directoryPath: string): string[] {
  if (!existsSync(directoryPath)) {
    return []
  }

  const files: string[] = []
  for (const entry of readdirSync(directoryPath, { withFileTypes: true })) {
    const absolutePath = join(directoryPath, entry.name)
    if (entry.isDirectory()) {
      files.push(...collectMarkdownFiles(absolutePath))
      continue
    }
    if (entry.isFile() && entry.name.toLowerCase().endsWith('.md')) {
      files.push(absolutePath)
    }
  }
  return files
}

function readTestSpecMetadata(): TestSpecMetadata[] {
  if (!existsSync(TEST_SPEC_DIRECTORY_PATH)) {
    return []
  }

  return collectMarkdownFiles(TEST_SPEC_DIRECTORY_PATH)
    .filter((absolutePath) => {
      const fileName = absolutePath.split(/[\\/]/).pop() || ''
      const relativePath = absolutePath.slice(TEST_SPEC_DIRECTORY_PATH.length + 1).replace(/\\/g, '/')
      const firstSegment = relativePath.split('/')[0]
      return fileName !== 'TEST_SPEC_OVERVIEW.md' && fileName !== '00_security_tests_overview.md' && firstSegment !== '_archive' && firstSegment !== '_legacy'
    })
    .map((absolutePath) => {
      const fileName = absolutePath.split(/[\\/]/).pop() || ''
      const relativePath = absolutePath.slice(TEST_SPEC_DIRECTORY_PATH.length + 1).replace(/\\/g, '/')
      const category = categoryDefinitionFor(relativePath)
      const text = readFileSync(absolutePath, 'utf-8')
      const identity = parseTestSpecIdentity(text)
      const title = identity['TestSpec Name'] || extractSpecTitle(text, fileName)
      const capability = identity['Capability Name'] || title
      const primaryGoal = identity['Primary Test Goal'] || ''
      const userValue = identity['User Value'] || ''
      const objective = extractMarkdownSectionText(text, 'TEST OBJECTIVE')
      const successBehavior = extractUserExperienceValue(text, 'Success Behavior')
      const description = firstNonEmpty(objective, primaryGoal, userValue, 'Keine Beschreibung in der TestSpec hinterlegt.')
      const reliableBehavior = firstNonEmpty(successBehavior, userValue, primaryGoal, objective)
      const path = `documentation/TEST_SPEC/${relativePath}`

      return {
        specId: relativePath.replace(/\.md$/i, '').replace(/[\\/]/g, '__'),
        fileName,
        path,
        categoryId: category.id,
        categoryLabel: category.label,
        categoryOrder: TEST_SUITE_CATEGORIES.findIndex((definition) => definition.id === category.id) + 1,
        title,
        capability,
        description: compactWhitespace(description),
        reliableBehavior: compactWhitespace(reliableBehavior),
        matchKeys: [fileName, path, relativePath, title, capability].map(normalizeMatchKey).filter(Boolean),
      }
    })
    .sort((left, right) => left.categoryOrder - right.categoryOrder || left.fileName.localeCompare(right.fileName))
}

function parseTestSpecIdentity(text: string): Record<string, string> {
  return parseSpecKeyValueBlock(text, /^##\s+TEST IDENTITY\s*$/i)
}

function extractMarkdownSectionText(text: string, heading: string): string {
  const lines = text.split(/\r?\n/)
  const headingPattern = new RegExp(`^##\\s+${escapeRegExp(heading)}\\s*$`, 'i')
  const startIndex = lines.findIndex((line) => headingPattern.test(line.trim()))

  if (startIndex === -1) {
    return ''
  }

  const sectionLines: string[] = []
  for (let index = startIndex + 1; index < lines.length; index += 1) {
    const line = lines[index]
    if (/^##\s+/.test(line.trim())) {
      break
    }
    if (!line.trim() || line.trim().startsWith('|')) {
      continue
    }
    sectionLines.push(line.replace(/^-\s+/, '').trim())
  }

  return sectionLines.join(' ')
}

function extractUserExperienceValue(text: string, key: string): string {
  const section = extractMarkdownSectionText(text, 'USER EXPERIENCE CONTRACT')
  const match = new RegExp(`${escapeRegExp(key)}:\\s*(.+?)(?:\\s+-\\s+[A-Z][^:]+:|$)`, 'i').exec(section)
  return match?.[1]?.trim() || ''
}

function firstNonEmpty(...values: string[]): string {
  return values.find((value) => value && value.trim())?.trim() || ''
}

function compactWhitespace(value: string): string {
  return value.replace(/\s+/g, ' ').trim()
}

function escapeRegExp(value: string): string {
  return value.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
}

function normalizeMatchKey(value: string | undefined): string {
  return (value || '')
    .toLowerCase()
    .replace(/\\/g, '/')
    .replace(/\.md$/i, '')
    .replace(/[^a-z0-9]+/g, ' ')
    .trim()
}

function readTestRunPlans(): Map<string, TestRunPlan> {
  const plans = new Map<string, TestRunPlan>()

  if (!existsSync(TEST_RUNS_DIRECTORY_PATH)) {
    return plans
  }

  for (const entry of readdirSync(TEST_RUNS_DIRECTORY_PATH, { withFileTypes: true })) {
    if (!entry.isFile() || !entry.name.endsWith('_plan.json')) {
      continue
    }

    const planPath = join(TEST_RUNS_DIRECTORY_PATH, entry.name)
    try {
      const parsed = JSON.parse(readFileSync(planPath, 'utf-8')) as TestRunPlan
      const runId = parsed.testRunId || /^(.+?)_plan\.json$/i.exec(entry.name)?.[1]
      if (runId) {
        plans.set(runId, parsed)
      }
    } catch (error) {
      fastify.log.warn({ error, planPath }, 'Ignoring unreadable test plan')
    }
  }

  return plans
}

function resolvePlanTestSpecPath(plan: TestRunPlan | undefined): string {
  if (!plan) {
    return ''
  }

  const candidate =
    plan.testSpecPath ||
    plan.sourceSpec ||
    plan.source_spec ||
    plan.inputTestSpecPath ||
    plan.input_testspec_path ||
    plan.test_spec_path ||
    plan.testspec_path ||
    plan.testSpec ||
    plan.TestSpec

  return typeof candidate === 'string' ? candidate : ''
}

function findSpecForResult(record: TestResultRecord, plan: TestRunPlan | undefined, specs: TestSpecMetadata[]): TestSpecMetadata | null {
  const planPath = normalizeMatchKey(resolvePlanTestSpecPath(plan))
  if (planPath) {
    const byPath = specs.find((spec) => spec.matchKeys.some((key) => planPath === key || planPath.endsWith(key)))
    if (byPath) {
      return byPath
    }
  }

  const titleKey = normalizeMatchKey(record.title || plan?.title)
  if (!titleKey) {
    return null
  }

  return specs.find((spec) => spec.matchKeys.some((key) => key === titleKey || key.includes(titleKey) || titleKey.includes(key))) || null
}

function calculateProviderPassRate(record: TestResultRecord, plan: TestRunPlan | undefined): Record<string, number> {
  const providerByTestId = new Map<string, string>()
  for (const test of plan?.tests || []) {
    if (test.id && test.provider) {
      providerByTestId.set(test.id, test.provider)
    }
  }

  return calculateGroupedPassRate(record, (testCaseId) => providerByTestId.get(testCaseId) || inferProviderFromTestCaseId(testCaseId))
}

function calculateTypePassRate(record: TestResultRecord, plan: TestRunPlan | undefined): Record<string, number> {
  const typeByTestId = new Map<string, string>()
  for (const test of plan?.tests || []) {
    if (test.id && test.type) {
      typeByTestId.set(test.id, test.type)
    }
  }

  return calculateGroupedPassRate(record, (testCaseId) => typeByTestId.get(testCaseId) || 'unknown')
}

function inferProviderFromTestCaseId(testCaseId: string): string {
  if (/-GEMINI$/i.test(testCaseId)) {
    return 'Gemini'
  }
  if (/-GPT$/i.test(testCaseId)) {
    return 'GPT'
  }
  return 'Shared'
}

function calculateGroupedPassRate(record: TestResultRecord, groupForTestCase: (testCaseId: string) => string): Record<string, number> {
  const groups = new Map<string, { total: number; passed: number }>()

  for (const result of record.results) {
    const group = groupForTestCase(result.testCaseId)
    if (!groups.has(group)) {
      groups.set(group, { total: 0, passed: 0 })
    }
    const aggregate = groups.get(group)!
    aggregate.total += 1
    if (result.result === 'PASS') {
      aggregate.passed += 1
    }
  }

  return Object.fromEntries(
    Array.from(groups.entries())
      .sort(([left], [right]) => left.localeCompare(right))
      .map(([group, aggregate]) => [group, aggregate.total > 0 ? (aggregate.passed / aggregate.total) * 100 : 0]),
  )
}

function getPlannedTestCount(plan: TestRunPlan | undefined): number {
  return Array.isArray(plan?.tests) ? plan.tests.length : 0
}

function isFullTestRun(record: TestResultRecord, plan: TestRunPlan | undefined): boolean {
  const plannedTotal = getPlannedTestCount(plan)
  return plannedTotal === 0 || record.summary.total >= plannedTotal
}

function calculateImpact(spec: TestSpecMetadata, record: TestResultRecord | null, passRate: number): Pick<TestSpecOverview, 'impactLevel' | 'impactScore' | 'impactReason'> {
  const categoryBase: Record<string, number> = {
    '02_security_safety': 95,
    '01_core_system': 90,
    '03_tools_skills': 86,
    '04_memory_context': 84,
    '05_ux_behavior': 78,
    '06_efficiency_cost': 68,
    '07_regression_suite': 72,
  }
  const reasons: string[] = []
  let score = categoryBase[spec.categoryId] || 60

  if (spec.categoryId === '02_security_safety') reasons.push('high safety/privacy impact')
  if (spec.categoryId === '01_core_system') reasons.push('core routing/architecture coverage')
  if (spec.categoryId === '03_tools_skills') reasons.push('tool and API reliability coverage')
  if (spec.categoryId === '04_memory_context') reasons.push('personal context and privacy coverage')
  if (spec.categoryId === '05_ux_behavior') reasons.push('direct user experience coverage')
  if (spec.categoryId === '06_efficiency_cost') reasons.push('cost, latency, and token discipline coverage')
  if (spec.categoryId === '07_regression_suite') reasons.push('bug recurrence protection')

  if (!record) {
    score += 14
    reasons.push('not validated yet')
  } else if (record.status === 'FAIL') {
    score += 22
    reasons.push('latest run failed')
  } else if (record.status === 'BLOCKED' || record.status === 'PARTIAL') {
    score += 16
    reasons.push('latest run needs follow-up')
  } else if (record.status === 'PASS' && passRate === 100) {
    score -= 12
    reasons.push('currently green')
  }

  if (record && record.summary.failed > 0) {
    score += Math.min(16, record.summary.failed * 2)
    reasons.push(`${record.summary.failed} open failures`)
  }

  const normalizedScore = Math.max(0, Math.min(100, Math.round(score)))
  const impactLevel = normalizedScore >= 90 ? 'critical' : normalizedScore >= 78 ? 'high' : normalizedScore >= 60 ? 'medium' : 'low'

  return {
    impactLevel,
    impactScore: normalizedScore,
    impactReason: reasons.slice(0, 3).join(', ') || 'general suite coverage',
  }
}

function buildSpecOverview(spec: TestSpecMetadata, record: TestResultRecord | null, plan: TestRunPlan | undefined): TestSpecOverview {
  const plannedTotal = getPlannedTestCount(plan)
  const executedTotal = record?.summary.total || 0
  const total = Math.max(executedTotal, plannedTotal)
  const passed = record?.summary.passed || 0
  const passRate = total > 0 ? (passed / total) * 100 : 0
  const isPartialRun = Boolean(record && plannedTotal > 0 && executedTotal < plannedTotal)
  const effectiveStatus = record ? (isPartialRun ? 'PARTIAL' : record.status) : 'NOT_RUN'
  const impactRecord = record && isPartialRun ? { ...record, status: 'PARTIAL' } : record
  const impact = calculateImpact(spec, impactRecord, passRate)

  return {
    specId: spec.specId,
    fileName: spec.fileName,
    path: spec.path,
    categoryId: spec.categoryId,
    categoryLabel: spec.categoryLabel,
    categoryOrder: spec.categoryOrder,
    title: spec.title,
    capability: spec.capability,
    description: spec.description,
    reliableBehavior: spec.reliableBehavior,
    impactLevel: impact.impactLevel,
    impactScore: impact.impactScore,
    impactReason: impact.impactReason,
    recommendedNext: false,
    status: effectiveStatus,
    latestRunId: record?.testRunId || null,
    latestRunTitle: record?.title || null,
    latestUpdatedAt: record?.updatedAt || null,
    passRate,
    total,
    plannedTotal,
    executedTotal,
    isPartialRun,
    passed,
    failed: record?.summary.failed || 0,
    blocked: record?.summary.blocked || 0,
    manualGateRequired: record?.summary.manualGateRequired || 0,
    providerPassRate: record ? calculateProviderPassRate(record, plan) : {},
    typePassRate: record ? calculateTypePassRate(record, plan) : {},
    failedTestCases: record ? record.results.filter((result) => result.result === 'FAIL' || result.result === 'BLOCKED').map((result) => result.testCaseId) : [],
    resultJson: record?.artifacts.resultJson || null,
  }
}

function readTestOverview(): TestOverviewResponse {
  const specs = readTestSpecMetadata()
  const testResults = readTestResults()
  const plans = readTestRunPlans()
  const latestFullBySpec = new Map<string, TestResultRecord>()
  const latestAnyBySpec = new Map<string, TestResultRecord>()

  for (const record of testResults.records) {
    const plan = plans.get(record.testRunId)
    const spec = findSpecForResult(record, plan, specs)
    if (!spec) {
      continue
    }

    const existingAny = latestAnyBySpec.get(spec.path)
    if (!existingAny || (Date.parse(record.updatedAt) || 0) > (Date.parse(existingAny.updatedAt) || 0)) {
      latestAnyBySpec.set(spec.path, record)
    }

    if (isFullTestRun(record, plan)) {
      const existingFull = latestFullBySpec.get(spec.path)
      if (!existingFull || (Date.parse(record.updatedAt) || 0) > (Date.parse(existingFull.updatedAt) || 0)) {
        latestFullBySpec.set(spec.path, record)
      }
    }
  }

  const testSpecs = specs.map((spec) => {
    const record = latestFullBySpec.get(spec.path) || latestAnyBySpec.get(spec.path) || null
    return buildSpecOverview(spec, record, record ? plans.get(record.testRunId) : undefined)
  })
  const recommendedNext = selectRecommendedNext(testSpecs)
  if (recommendedNext) {
    recommendedNext.recommendedNext = true
  }

  testSpecs.sort((left, right) => {
    if (left.recommendedNext && !right.recommendedNext) return -1
    if (right.recommendedNext && !left.recommendedNext) return 1
    if (left.impactScore !== right.impactScore) return right.impactScore - left.impactScore
    if (left.status === 'NOT_RUN' && right.status !== 'NOT_RUN') return 1
    if (right.status === 'NOT_RUN' && left.status !== 'NOT_RUN') return -1
    if (left.passRate !== right.passRate) return left.passRate - right.passRate
    return left.fileName.localeCompare(right.fileName)
  })

  const validatedSpecs = testSpecs.filter((spec) => spec.status !== 'NOT_RUN').length
  const perfectSpecs = testSpecs.filter((spec) => spec.passRate === 100 && spec.status === 'PASS').length
  const notRunSpecs = testSpecs.filter((spec) => spec.status === 'NOT_RUN').length
  const attentionSpecs = testSpecs.length - perfectSpecs - notRunSpecs
  const totalValidatedCases = testSpecs.reduce((sum, spec) => sum + spec.total, 0)
  const totalPassedCases = testSpecs.reduce((sum, spec) => sum + spec.passed, 0)
  const latestUpdatedValues = testSpecs
    .map((spec) => spec.latestUpdatedAt)
    .filter((value): value is string => Boolean(value))
    .sort()
  const latestUpdatedAt = latestUpdatedValues.length > 0 ? latestUpdatedValues[latestUpdatedValues.length - 1] : null

  return {
    schema: 'janus-dashboard.testspec-overview.v1',
    source: TEST_SPEC_DIRECTORY_PATH,
    summary: {
      totalTestSpecs: testSpecs.length,
      validatedSpecs,
      perfectSpecs,
      attentionSpecs,
      notRunSpecs,
      overallPassRate: totalValidatedCases > 0 ? (totalPassedCases / totalValidatedCases) * 100 : 0,
      latestUpdatedAt,
    },
    testSpecs,
  }
}

function selectRecommendedNext(testSpecs: TestSpecOverview[]): TestSpecOverview | null {
  const candidates = testSpecs.filter((spec) => spec.status !== 'PASS' || spec.passRate < 100)
  const pool = candidates.length > 0 ? candidates : testSpecs

  return pool
    .slice()
    .sort((left, right) => {
      if (left.impactScore !== right.impactScore) return right.impactScore - left.impactScore
      if (left.status === 'FAIL' && right.status !== 'FAIL') return -1
      if (right.status === 'FAIL' && left.status !== 'FAIL') return 1
      if (left.passRate !== right.passRate) return left.passRate - right.passRate
      return left.fileName.localeCompare(right.fileName)
    })[0] || null
}

function buildTestSuiteCategory(category: TestSuiteCategoryDefinition, testSpecs: TestSpecOverview[]): TestSuiteCategory {
  const categorySpecs = testSpecs
    .filter((spec) => spec.categoryId === category.id)
    .sort((left, right) => {
      if (left.recommendedNext && !right.recommendedNext) return -1
      if (right.recommendedNext && !left.recommendedNext) return 1
      if (left.impactScore !== right.impactScore) return right.impactScore - left.impactScore
      if (left.status === 'NOT_RUN' && right.status !== 'NOT_RUN') return 1
      if (right.status === 'NOT_RUN' && left.status !== 'NOT_RUN') return -1
      if (left.passRate !== right.passRate) return left.passRate - right.passRate
      return left.fileName.localeCompare(right.fileName)
    })
  const validatedSpecs = categorySpecs.filter((spec) => spec.status !== 'NOT_RUN').length
  const perfectSpecs = categorySpecs.filter((spec) => spec.passRate === 100 && spec.status === 'PASS').length
  const notRunSpecs = categorySpecs.filter((spec) => spec.status === 'NOT_RUN').length
  const attentionSpecs = categorySpecs.length - perfectSpecs - notRunSpecs
  const totalValidatedCases = categorySpecs.reduce((sum, spec) => sum + spec.total, 0)
  const totalPassedCases = categorySpecs.reduce((sum, spec) => sum + spec.passed, 0)

  return {
    id: category.id,
    label: category.label,
    order: TEST_SUITE_CATEGORIES.findIndex((definition) => definition.id === category.id) + 1,
    description: category.description,
    totalTestSpecs: categorySpecs.length,
    validatedSpecs,
    perfectSpecs,
    attentionSpecs,
    notRunSpecs,
    overallPassRate: totalValidatedCases > 0 ? (totalPassedCases / totalValidatedCases) * 100 : 0,
    testSpecs: categorySpecs,
  }
}

function readTestSuite(): TestSuiteResponse {
  const overview = readTestOverview()
  const recommendedNext = overview.testSpecs.find((spec) => spec.recommendedNext) || null

  return {
    schema: 'janus-dashboard.testsuite.v1',
    source: TEST_SPEC_DIRECTORY_PATH,
    summary: overview.summary,
    recommendedNext,
    categories: TEST_SUITE_CATEGORIES.map((category) => buildTestSuiteCategory(category, overview.testSpecs)),
  }
}

// Health check endpoint
fastify.get('/health', async () => {
  return { status: 'ok', timestamp: new Date().toISOString() }
})

fastify.get('/api/backlog/items', async (request, reply) => {
  try {
    return readBacklogData()
  } catch (error) {
    fastify.log.error(error)
    reply.code(500)
    return { 
      error: 'Failed to read local data',
      message: error instanceof Error ? error.message : 'Unknown error'
    }
  }
})

fastify.get('/api/backlog/recommendations', async (request, reply) => {
  try {
    return readBacklogRecommendations()
  } catch (error) {
    fastify.log.error(error)
    reply.code(500)
    return {
      error: 'Failed to calculate backlog recommendations',
      message: error instanceof Error ? error.message : 'Unknown error',
    }
  }
})

fastify.get('/api/task-execution-history', async (request, reply) => {
  try {
    return readTaskExecutionHistory()
  } catch (error) {
    fastify.log.error(error)
    reply.code(500)
    return {
      error: 'Failed to read local task execution history',
      message: error instanceof Error ? error.message : 'Unknown error'
    }
  }
})

fastify.get('/api/test-results', async (request, reply) => {
  try {
    return readTestResults()
  } catch (error) {
    fastify.log.error(error)
    reply.code(500)
    return {
      error: 'Failed to read local test results',
      message: error instanceof Error ? error.message : 'Unknown error',
    }
  }
})

fastify.get('/api/test-overview', async (request, reply) => {
  try {
    return readTestOverview()
  } catch (error) {
    fastify.log.error(error)
    reply.code(500)
    return {
      error: 'Failed to read test overview',
      message: error instanceof Error ? error.message : 'Unknown error',
    }
  }
})

fastify.get('/api/test-suite', async (request, reply) => {
  try {
    return readTestSuite()
  } catch (error) {
    fastify.log.error(error)
    reply.code(500)
    return {
      error: 'Failed to read test suite',
      message: error instanceof Error ? error.message : 'Unknown error',
    }
  }
})

const start = async () => {
  try {
    await fastify.listen({ port: LOCAL_API_PORT, host: '127.0.0.1' })
    console.log(`🚀 Local API running on http://127.0.0.1:${LOCAL_API_PORT}`)
  } catch (err) {
    fastify.log.error(err)
    process.exit(1)
  }
}

start()
