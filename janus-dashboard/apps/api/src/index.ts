import Fastify from 'fastify'
import cors from '@fastify/cors'
import { readFileSync, statSync } from 'fs'
import { fileURLToPath } from 'url'
import { dirname, join } from 'path'
import type { BacklogCounts, BacklogItem, BacklogResponse } from '../../../shared/types/index.js'

const __filename = fileURLToPath(import.meta.url)
const __dirname = dirname(__filename)

const LOCAL_API_PORT = 3001
const DATA_FILE_PATH = join(__dirname, '../../../data/backlog.snapshot.json')
const BACKLOG_FILE_PATH = join(__dirname, '../../../../documentation/backlog/BACKLOG.md')

const ITEM_HEADING_PATTERN = /^###\s+(BACKLOG-\d+)\s+[–-]\s+(.+?)\s*$/
const SECTION_PATTERN = /^##\s+(.+?)\s*$/
const FIELD_PATTERN = /^-\s+\*\*(.+?):\*\*\s*(.*)$/

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
      return {
        ...parseBacklogText(text, BACKLOG_FILE_PATH),
        snapshot_path: DATA_FILE_PATH,
        is_stale: true,
      }
    }
    return {
      ...snapshot,
      snapshot_path: DATA_FILE_PATH,
      is_stale: false,
    }
  } catch (error) {
    fastify.log.warn({ error }, 'Falling back to live parsed backlog data')
    const text = readFileSync(BACKLOG_FILE_PATH, 'utf-8')
    return {
      ...parseBacklogText(text, BACKLOG_FILE_PATH),
      snapshot_path: DATA_FILE_PATH,
      is_stale: true,
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
