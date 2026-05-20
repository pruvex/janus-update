import { useEffect, useMemo, useState } from 'react'
import { CheckCircle2, Loader2, XCircle, AlertTriangle, CircleDashed } from 'lucide-react'
import type { TestResultRecord } from '@shared/types'
import { fetchTestResults } from '../lib/api'
import { cn } from '../lib/utils'

const statusStyle: Record<string, string> = {
  PASS: 'bg-emerald-50 text-emerald-700 border-emerald-200',
  FAIL: 'bg-red-50 text-red-700 border-red-200',
  BLOCKED: 'bg-amber-50 text-amber-700 border-amber-200',
  PARTIAL: 'bg-sky-50 text-sky-700 border-sky-200',
  RUNNING: 'bg-muted text-muted-foreground border-border',
}

function StatusIcon({ status }: { status: string }) {
  if (status === 'PASS') return <CheckCircle2 className="h-4 w-4" />
  if (status === 'FAIL') return <XCircle className="h-4 w-4" />
  if (status === 'BLOCKED' || status === 'PARTIAL') return <AlertTriangle className="h-4 w-4" />
  return <CircleDashed className="h-4 w-4" />
}

function ResultBadge({ status }: { status: string }) {
  return (
    <span className={cn('inline-flex items-center gap-1 rounded-md border px-2 py-1 text-xs font-semibold', statusStyle[status] || statusStyle.RUNNING)}>
      <StatusIcon status={status} />
      {status}
    </span>
  )
}

function failureCodes(record: TestResultRecord): string[] {
  return Array.from(
    new Set(
      record.results
        .filter((result) => result.result === 'FAIL' || result.result === 'BLOCKED')
        .map((result) => result.classification)
        .filter(Boolean),
    ),
  )
}

export function TestResultsView() {
  const [records, setRecords] = useState<TestResultRecord[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    loadTestResults()
  }, [])

  const loadTestResults = async () => {
    try {
      setLoading(true)
      const response = await fetchTestResults()
      setRecords(response.records)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load test results')
    } finally {
      setLoading(false)
    }
  }

  const totals = useMemo(() => {
    return records.reduce(
      (acc, record) => {
        acc.total += record.summary.total
        acc.passed += record.summary.passed
        acc.failed += record.summary.failed
        acc.blocked += record.summary.blocked
        acc.manual += record.summary.manualGateRequired
        return acc
      },
      { total: 0, passed: 0, failed: 0, blocked: 0, manual: 0 },
    )
  }, [records])

  if (loading) {
    return (
      <div className="flex h-full items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex h-full items-center justify-center">
        <p className="text-destructive">{error}</p>
      </div>
    )
  }

  return (
    <div className="h-full overflow-auto">
      <div className="border-b border-border p-4">
        <h2 className="text-xl font-bold text-foreground">Test Results</h2>
        <p className="mt-1 text-sm text-muted-foreground">
          Read-only view over machine-readable Janus test result JSON files.
        </p>
      </div>

      <div className="border-b border-border bg-muted/30 p-4">
        <div className="grid max-w-4xl grid-cols-5 gap-2">
          <div className="rounded-lg border border-border bg-card p-2">
            <span className="text-[10px] text-muted-foreground">Runs</span>
            <p className="mt-0.5 text-lg font-bold text-foreground">{records.length}</p>
          </div>
          <div className="rounded-lg border border-border bg-card p-2">
            <span className="text-[10px] text-muted-foreground">Cases</span>
            <p className="mt-0.5 text-lg font-bold text-foreground">{totals.total}</p>
          </div>
          <div className="rounded-lg border border-border bg-card p-2">
            <span className="text-[10px] text-muted-foreground">Passed</span>
            <p className="mt-0.5 text-lg font-bold text-emerald-700">{totals.passed}</p>
          </div>
          <div className="rounded-lg border border-border bg-card p-2">
            <span className="text-[10px] text-muted-foreground">Failed</span>
            <p className="mt-0.5 text-lg font-bold text-red-700">{totals.failed}</p>
          </div>
          <div className="rounded-lg border border-border bg-card p-2">
            <span className="text-[10px] text-muted-foreground">Blocked/Manual</span>
            <p className="mt-0.5 text-lg font-bold text-amber-700">{totals.blocked + totals.manual}</p>
          </div>
        </div>
      </div>

      <div className="p-4">
        {records.length === 0 ? (
          <div className="rounded-lg border border-border bg-card p-6 text-sm text-muted-foreground">
            No machine-readable test results found.
          </div>
        ) : (
          <div className="overflow-hidden rounded-lg border border-border bg-card">
            <table className="w-full text-left text-sm">
              <thead className="border-b border-border bg-muted/50 text-xs uppercase text-muted-foreground">
                <tr>
                  <th className="px-3 py-2">TestRun</th>
                  <th className="px-3 py-2">Status</th>
                  <th className="px-3 py-2">Cases</th>
                  <th className="px-3 py-2">Failure Codes</th>
                  <th className="px-3 py-2">Evidence</th>
                  <th className="px-3 py-2">Updated</th>
                </tr>
              </thead>
              <tbody>
                {records.map((record) => {
                  const codes = failureCodes(record)
                  return (
                    <tr key={record.testRunId} className="border-b border-border last:border-b-0">
                      <td className="px-3 py-3 align-top">
                        <p className="font-semibold text-foreground">{record.testRunId}</p>
                        <p className="mt-1 max-w-xs truncate text-xs text-muted-foreground">{record.title || 'Untitled'}</p>
                      </td>
                      <td className="px-3 py-3 align-top">
                        <ResultBadge status={record.status} />
                      </td>
                      <td className="px-3 py-3 align-top text-xs text-muted-foreground">
                        <p>{record.summary.passed}/{record.summary.total} pass</p>
                        <p>{record.summary.failed} fail</p>
                        <p>{record.summary.blocked + record.summary.manualGateRequired} blocked/manual</p>
                      </td>
                      <td className="px-3 py-3 align-top">
                        {codes.length === 0 ? (
                          <span className="text-xs text-muted-foreground">N/A</span>
                        ) : (
                          <div className="flex max-w-sm flex-wrap gap-1">
                            {codes.map((code) => (
                              <span key={code} className="rounded border border-border bg-muted px-1.5 py-0.5 text-[11px] font-mono text-foreground">
                                {code}
                              </span>
                            ))}
                          </div>
                        )}
                      </td>
                      <td className="px-3 py-3 align-top">
                        <p className="max-w-xs truncate font-mono text-xs text-muted-foreground">{record.artifacts.resultJson}</p>
                        <p className="mt-1 text-xs text-muted-foreground">{record.artifacts.evidenceFiles.length} evidence files</p>
                      </td>
                      <td className="px-3 py-3 align-top text-xs text-muted-foreground">
                        {record.updatedAt}
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}
