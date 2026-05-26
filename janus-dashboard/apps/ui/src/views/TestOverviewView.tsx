import { useEffect, useState } from 'react'
import { Activity, AlertTriangle, CheckCircle2, CircleDashed, Loader2, XCircle } from 'lucide-react'
import type { TestOverviewResponse, TestSpecOverview } from '@shared/types'
import { fetchTestOverview } from '../lib/api'
import { cn } from '../lib/utils'

const statusStyle: Record<string, string> = {
  PASS: 'bg-emerald-50 text-emerald-700 border-emerald-200',
  FAIL: 'bg-red-50 text-red-700 border-red-200',
  BLOCKED: 'bg-amber-50 text-amber-700 border-amber-200',
  PARTIAL: 'bg-sky-50 text-sky-700 border-sky-200',
  RUNNING: 'bg-muted text-muted-foreground border-border',
  NOT_RUN: 'bg-muted text-muted-foreground border-border',
}

function StatusIcon({ status }: { status: string }) {
  if (status === 'PASS') return <CheckCircle2 className="h-4 w-4" />
  if (status === 'FAIL') return <XCircle className="h-4 w-4" />
  if (status === 'BLOCKED' || status === 'PARTIAL') return <AlertTriangle className="h-4 w-4" />
  if (status === 'RUNNING') return <Activity className="h-4 w-4" />
  return <CircleDashed className="h-4 w-4" />
}

function StatusBadge({ spec }: { spec: TestSpecOverview }) {
  const label = spec.status === 'NOT_RUN' ? 'NOT RUN' : spec.status

  return (
    <span className={cn('inline-flex items-center gap-1 rounded-md border px-2 py-1 text-xs font-semibold', statusStyle[spec.status] || statusStyle.RUNNING)}>
      <StatusIcon status={spec.status} />
      {label}
    </span>
  )
}

function PassRateBadge({ spec }: { spec: TestSpecOverview }) {
  if (spec.status === 'NOT_RUN') {
    return <span className="text-sm font-semibold text-muted-foreground">--</span>
  }

  const colorClass = spec.status === 'FAIL'
    ? 'text-red-700'
    : spec.status === 'BLOCKED' || spec.status === 'PARTIAL'
    ? 'text-amber-700'
    : spec.status === 'RUNNING'
    ? 'text-muted-foreground'
    : spec.passRate === 100
    ? 'text-emerald-700'
    : spec.passRate >= 80
    ? 'text-sky-700'
    : spec.passRate >= 50
    ? 'text-amber-700'
    : 'text-red-700'

  return <span className={cn('text-base font-bold tabular-nums', colorClass)}>{spec.passRate.toFixed(2)}%</span>
}

function RateList({ rates }: { rates: Record<string, number> }) {
  const entries = Object.entries(rates)

  if (entries.length === 0) {
    return <span className="text-xs text-muted-foreground">N/A</span>
  }

  return (
    <div className="flex flex-wrap gap-1">
      {entries.map(([label, rate]) => (
        <span key={label} className="rounded border border-border bg-muted px-1.5 py-0.5 text-[11px] text-foreground">
          {label}: {rate.toFixed(0)}%
        </span>
      ))}
    </div>
  )
}

function FailedTests({ spec }: { spec: TestSpecOverview }) {
  if (spec.status === 'NOT_RUN') {
    return <span className="text-xs text-muted-foreground">Noch kein TestRun</span>
  }

  if (spec.failedTestCases.length === 0) {
    return <span className="text-xs font-medium text-emerald-700">Keine</span>
  }

  return (
    <div className="flex max-w-md flex-wrap gap-1">
      {spec.failedTestCases.map((testCaseId) => (
        <span key={testCaseId} className="rounded border border-red-200 bg-red-50 px-1.5 py-0.5 font-mono text-[11px] text-red-700">
          {testCaseId}
        </span>
      ))}
    </div>
  )
}

export function TestOverviewView() {
  const [overview, setOverview] = useState<TestOverviewResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    loadTestOverview()
  }, [])

  const loadTestOverview = async () => {
    try {
      setLoading(true)
      const response = await fetchTestOverview()
      setOverview(response)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load test overview')
    } finally {
      setLoading(false)
    }
  }

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

  if (!overview) {
    return (
      <div className="flex h-full items-center justify-center">
        <p className="text-muted-foreground">No TestSpec data available</p>
      </div>
    )
  }

  const { summary, testSpecs } = overview

  return (
    <div className="h-full overflow-auto">
      <div className="border-b border-border p-4">
        <h2 className="text-xl font-bold text-foreground">TestSpec Validation</h2>
        <p className="mt-1 text-sm text-muted-foreground">
          TestSpecs are the dashboard source of truth. Each row shows what Janus must reliably do and the latest pipeline result.
        </p>
      </div>

      <div className="border-b border-border bg-muted/30 p-4">
        <div className="grid max-w-5xl grid-cols-6 gap-2">
          <div className="rounded-lg border border-border bg-card p-2">
            <span className="text-[10px] text-muted-foreground">TestSpecs</span>
            <p className="mt-0.5 text-lg font-bold text-foreground">{summary.totalTestSpecs}</p>
          </div>
          <div className="rounded-lg border border-border bg-card p-2">
            <span className="text-[10px] text-muted-foreground">Validated</span>
            <p className="mt-0.5 text-lg font-bold text-foreground">{summary.validatedSpecs}</p>
          </div>
          <div className="rounded-lg border border-border bg-card p-2">
            <span className="text-[10px] text-muted-foreground">Green</span>
            <p className="mt-0.5 text-lg font-bold text-emerald-700">{summary.perfectSpecs}</p>
          </div>
          <div className="rounded-lg border border-border bg-card p-2">
            <span className="text-[10px] text-muted-foreground">Needs Work</span>
            <p className="mt-0.5 text-lg font-bold text-amber-700">{summary.attentionSpecs}</p>
          </div>
          <div className="rounded-lg border border-border bg-card p-2">
            <span className="text-[10px] text-muted-foreground">Not Run</span>
            <p className="mt-0.5 text-lg font-bold text-muted-foreground">{summary.notRunSpecs}</p>
          </div>
          <div className="rounded-lg border border-border bg-card p-2">
            <span className="text-[10px] text-muted-foreground">Overall Green</span>
            <p className={cn('mt-0.5 text-lg font-bold', summary.overallPassRate === 100 ? 'text-emerald-700' : 'text-amber-700')}>
              {summary.overallPassRate.toFixed(2)}%
            </p>
          </div>
        </div>
      </div>

      <div className="p-4">
        {testSpecs.length === 0 ? (
          <div className="rounded-lg border border-border bg-card p-6 text-sm text-muted-foreground">
            No TestSpecs found in documentation/TEST_SPEC.
          </div>
        ) : (
          <div className="overflow-hidden rounded-lg border border-border bg-card">
            <table className="w-full text-left text-sm">
              <thead className="border-b border-border bg-muted/50 text-xs uppercase text-muted-foreground">
                <tr>
                  <th className="px-3 py-2">TestSpec</th>
                  <th className="px-3 py-2">Status</th>
                  <th className="px-3 py-2">Latest Result</th>
                  <th className="px-3 py-2">Provider</th>
                  <th className="px-3 py-2">Types</th>
                  <th className="px-3 py-2">Open Tests</th>
                </tr>
              </thead>
              <tbody>
                {testSpecs.map((spec) => (
                  <tr key={spec.path} className="border-b border-border last:border-b-0 hover:bg-muted/30">
                    <td className="max-w-xl px-3 py-3 align-top">
                      <p className="font-semibold text-foreground">{spec.title}</p>
                      <p className="mt-0.5 text-xs text-muted-foreground">{spec.capability}</p>
                      <p className="mt-2 text-xs leading-5 text-foreground">{spec.description}</p>
                      <p className="mt-1 text-xs leading-5 text-muted-foreground">
                        Muss zuverlässig: {spec.reliableBehavior}
                      </p>
                      <p className="mt-2 font-mono text-[11px] text-muted-foreground">{spec.path}</p>
                    </td>
                    <td className="px-3 py-3 align-top">
                      <StatusBadge spec={spec} />
                    </td>
                    <td className="px-3 py-3 align-top">
                      <PassRateBadge spec={spec} />
                      <p className="mt-1 text-xs text-muted-foreground">
                        {spec.status === 'NOT_RUN' ? 'Kein Resultat' : `${spec.passed}/${spec.total} passed`}
                      </p>
                      {spec.latestRunId ? (
                        <p className="mt-1 font-mono text-[11px] text-muted-foreground">{spec.latestRunId}</p>
                      ) : null}
                    </td>
                    <td className="px-3 py-3 align-top">
                      <RateList rates={spec.providerPassRate} />
                    </td>
                    <td className="px-3 py-3 align-top">
                      <RateList rates={spec.typePassRate} />
                    </td>
                    <td className="px-3 py-3 align-top">
                      <FailedTests spec={spec} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}
