import Fastify from 'fastify'
import cors from '@fastify/cors'
import { existsSync, readFileSync, readdirSync, statSync } from 'fs'
import { fileURLToPath } from 'url'
import { dirname, join } from 'path'
import type { BacklogCounts, BacklogItem, BacklogResponse, TaskExecutionHistoryResponse, TaskExecutionRecord } from '../../../shared/types/index.js'

const __filename = fileURLToPath(import.meta.url)
const __dirname = dirname(__filename)

const LOCAL_API_PORT = 3001
const DATA_FILE_PATH = join(__dirname, '../../../data/backlog.snapshot.json')
const TASK_EXECUTION_HISTORY_PATH = join(__dirname, '../../../data/task-execution-history.json')
const BACKLOG_FILE_PATH = join(__dirname, '../../../../documentation/backlog/BACKLOG.md')
const SPEC_DIRECTORY_PATH = join(__dirname, '../../../../documentation/SPEC')

const ITEM_HEADING_PATTERN = /^###\s+(BACKLOG-\d+)\s+[–-]\s+(.+?)\s*$/
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
    raw_fields: {},
  }
}

function createSpecItem(filePath: string, relativePath: string, text: string): BacklogItem {
  const metadata = parseSpecReviewMetadata(text)
  const implementationMetadata = parseSpecImplementationMetadata(text)
  const executionRouting = parseSpecExecutionRouting(text)
  const reviewStatus = (metadata['Review Status'] || '').toUpperCase()
  const skillReady = (metadata['Skill-1 Ready'] || '').toUpperCase()
  const implementationStatus = (implementationMetadata['Implementation Status'] || '').toUpperCase()
  const finalAudit = (implementationMetadata['Final Audit'] || '').toUpperCase()
  const executionMode = normalizeSpecExecutionMode(executionRouting.execution_mode)
  const routingComplexityScore = normalizeSpecComplexityScore(executionRouting.complexity_score)
  const dashboardHint = normalizeSpecDashboardHint(executionRouting.dashboard_hint)
  const routingConfidence = normalizeSpecConfidence(executionRouting.confidence)
  const isSkillReady = skillReady === 'YES' && (reviewStatus === 'APPROVED' || reviewStatus === 'APPROVED_WITH_NOTES')
  const isImplementationDone = implementationStatus === 'DONE' && (finalAudit === 'PASS' || finalAudit === 'PASS WITH FIXES')
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
  item.completed_at = isImplementationDone ? implementationMetadata['Completed At'] || formatDate(fileStat.mtime) : null
  item.completed_by_task = isImplementationDone ? implementationMetadata['Completed By'] || 'SKILL 6 – DIAMANTSTANDARD FINAL AUDIT' : null
  item.final_audit = isImplementationDone ? finalAudit : null
  item.validation_evidence = isImplementationDone ? implementationMetadata['Validation Evidence'] || null : null
  item.raw_fields = {
    Spec: normalizePathForPrompt(relativePath),
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
    'Implementation Status': implementationStatus || '',
    'Final Audit': finalAudit || '',
    'Completed At': implementationMetadata['Completed At'] || '',
    'Completed By': implementationMetadata['Completed By'] || '',
    'Validation Evidence': implementationMetadata['Validation Evidence'] || '',
  }

  return item
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
    if (!/^JANUS FEATURE SPEC\s+[–-]\s+DIAMANTSTANDARD/i.test(title)) {
      return title
    }
  }

  const featureName = text
    .split(/\r?\n/)
    .map((line) => /^-\s+\*?\*?Feature Name\*?\*?:\s*(.+?)\s*$/.exec(line.trim()))
    .find((match): match is RegExpExecArray => Boolean(match))?.[1]

  if (featureName) {
    return featureName.trim()
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

function parseBacklogText(text: string, source: string): BacklogResponse {
  const items: BacklogItem[] = []
  let currentItem: BacklogItem | null = null
  let currentField: keyof BacklogItem | null = null

  for (const rawLine of text.split(/\r?\n/)) {
    const line = rawLine.replace(/\s+$/, '')
    const sectionMatch = SECTION_PATTERN.exec(line)
    if (sectionMatch && !line.startsWith('###')) {
      currentField = null
      continue
    }

    const itemMatch = ITEM_HEADING_PATTERN.exec(line)
    if (itemMatch) {
      if (currentItem) {
        items.push(currentItem)
      }
      currentItem = createBacklogItem(itemMatch[1].trim(), itemMatch[2].trim())
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
