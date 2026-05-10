import { readFileSync, writeFileSync, mkdirSync } from 'node:fs'
import { dirname, resolve } from 'node:path'

const HISTORY_PATH = resolve('data/task-execution-history.json')
const SCHEMA = 'janus-dashboard.task_execution_history.v1'
const VALID_SOURCES = new Set(['skill_lifecycle', 'backlog_sync', 'manual_skill_update_with_evidence'])

function readJson(path) {
  return JSON.parse(readFileSync(path, 'utf-8'))
}

function parseArgs(argv) {
  const inputIndex = argv.indexOf('--input')
  if (inputIndex === -1 || !argv[inputIndex + 1]) {
    throw new Error('Missing required --input <record.json> argument')
  }

  return {
    input: resolve(argv[inputIndex + 1]),
  }
}

function requireString(record, key) {
  if (typeof record[key] !== 'string' || record[key].trim() === '') {
    throw new Error(`Invalid task execution record: ${key} must be a non-empty string`)
  }
}

function requireBoolean(record, key) {
  if (typeof record[key] !== 'boolean') {
    throw new Error(`Invalid task execution record: ${key} must be a boolean`)
  }
}

function validateIsoDate(record, key) {
  requireString(record, key)
  const date = new Date(record[key])
  if (Number.isNaN(date.getTime())) {
    throw new Error(`Invalid task execution record: ${key} must be a valid ISO timestamp`)
  }
}

function validateRecord(record) {
  const requiredStrings = ['execution_id', 'task_id', 'task_type', 'skill_used', 'importance', 'effort', 'risk', 'source']
  requiredStrings.forEach((key) => requireString(record, key))
  validateIsoDate(record, 'started_at')
  validateIsoDate(record, 'finished_at')
  requireBoolean(record, 'successful')
  requireBoolean(record, 'reopened')

  if (!VALID_SOURCES.has(record.source)) {
    throw new Error(`Invalid task execution record: source must be one of ${Array.from(VALID_SOURCES).join(', ')}`)
  }

  if (record.successful !== true) {
    throw new Error('Only completed successful executions may be persisted in task-execution-history.json')
  }

  if (!Number.isFinite(record.duration_minutes) || record.duration_minutes <= 0) {
    throw new Error('Invalid task execution record: duration_minutes must be a positive number')
  }

  const startedAt = new Date(record.started_at).getTime()
  const finishedAt = new Date(record.finished_at).getTime()
  if (finishedAt < startedAt) {
    throw new Error('Invalid task execution record: finished_at must be after started_at')
  }

  return {
    ...record,
    execution_id: record.execution_id.trim(),
    task_id: record.task_id.trim(),
    task_type: record.task_type.trim().toUpperCase(),
    skill_used: record.skill_used.trim().toUpperCase(),
    importance: record.importance.trim().toUpperCase(),
    effort: record.effort.trim().toUpperCase(),
    risk: record.risk.trim().toUpperCase(),
  }
}

function readHistory() {
  try {
    const history = readJson(HISTORY_PATH)
    return {
      schema: history.schema || SCHEMA,
      updated_at: history.updated_at || null,
      records: Array.isArray(history.records) ? history.records : [],
    }
  } catch {
    return {
      schema: SCHEMA,
      updated_at: null,
      records: [],
    }
  }
}

function main() {
  const args = parseArgs(process.argv.slice(2))
  const record = validateRecord(readJson(args.input))
  const history = readHistory()
  const existingIndex = history.records.findIndex((entry) => entry.execution_id === record.execution_id)

  if (existingIndex >= 0) {
    history.records[existingIndex] = record
  } else {
    history.records.push(record)
  }

  history.schema = SCHEMA
  history.updated_at = new Date().toISOString()
  mkdirSync(dirname(HISTORY_PATH), { recursive: true })
  writeFileSync(HISTORY_PATH, `${JSON.stringify(history, null, 2)}\n`, 'utf-8')
  console.log(`Task execution history updated: ${record.execution_id}`)
}

try {
  main()
} catch (error) {
  console.error(error instanceof Error ? error.message : error)
  process.exit(1)
}
