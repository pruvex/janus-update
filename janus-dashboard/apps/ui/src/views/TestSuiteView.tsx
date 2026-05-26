import { useEffect, useState } from 'react'
import { AlertTriangle, CheckCircle2, CircleDashed, Columns3, Loader2, Target, XCircle } from 'lucide-react'
import type { TestSpecOverview, TestSuiteCategory, TestSuiteResponse } from '@shared/types'
import { fetchTestSuite } from '../lib/api'
import { cn } from '../lib/utils'

const statusStyle: Record<string, string> = {
  PASS: 'border-emerald-200 bg-emerald-50 text-emerald-700',
  FAIL: 'border-red-200 bg-red-50 text-red-700',
  BLOCKED: 'border-amber-200 bg-amber-50 text-amber-700',
  PARTIAL: 'border-sky-200 bg-sky-50 text-sky-700',
  RUNNING: 'border-border bg-muted text-muted-foreground',
  NOT_RUN: 'border-border bg-muted text-muted-foreground',
}

const impactStyle: Record<string, string> = {
  critical: 'border-red-200 bg-red-50 text-red-700',
  high: 'border-amber-200 bg-amber-50 text-amber-700',
  medium: 'border-sky-200 bg-sky-50 text-sky-700',
  low: 'border-border bg-muted text-muted-foreground',
}

function StatusIcon({ status }: { status: string }) {
  if (status === 'PASS') return <CheckCircle2 className="h-3.5 w-3.5" />
  if (status === 'FAIL') return <XCircle className="h-3.5 w-3.5" />
  if (status === 'BLOCKED' || status === 'PARTIAL') return <AlertTriangle className="h-3.5 w-3.5" />
  return <CircleDashed className="h-3.5 w-3.5" />
}

function StatusBadge({ spec }: { spec: TestSpecOverview }) {
  const label = spec.status === 'NOT_RUN' ? 'NOT RUN' : spec.status

  return (
    <span className={cn('inline-flex items-center gap-1 rounded-md border px-1.5 py-0.5 text-[11px] font-semibold', statusStyle[spec.status] || statusStyle.RUNNING)}>
      <StatusIcon status={spec.status} />
      {label}
    </span>
  )
}

function passRateClass(passRate: number, status: string) {
  if (status === 'NOT_RUN') return 'text-muted-foreground'
  if (status === 'FAIL') return 'text-red-700'
  if (status === 'BLOCKED' || status === 'PARTIAL') return 'text-amber-700'
  if (status === 'RUNNING') return 'text-muted-foreground'
  if (passRate === 100) return 'text-emerald-700'
  if (passRate >= 80) return 'text-sky-700'
  if (passRate >= 50) return 'text-amber-700'
  return 'text-red-700'
}

function ImpactBadge({ spec }: { spec: TestSpecOverview }) {
  return (
    <span
      className={cn('inline-flex items-center gap-1 rounded-md border px-1.5 py-0.5 text-[11px] font-semibold uppercase', impactStyle[spec.impactLevel] || impactStyle.low)}
      title={spec.impactReason}
    >
      {spec.impactLevel}
      <span className="tabular-nums">{spec.impactScore}</span>
    </span>
  )
}

function SpecCard({ spec }: { spec: TestSpecOverview }) {
  return (
    <article
      className={cn(
        'rounded-lg border bg-card p-3 shadow-sm',
        spec.recommendedNext ? 'border-2 border-amber-400 shadow-amber-100' : 'border-border',
      )}
    >
      <div className="flex items-start justify-between gap-2">
        <StatusBadge spec={spec} />
        <span className={cn('text-sm font-bold tabular-nums', passRateClass(spec.passRate, spec.status))}>
          {spec.status === 'NOT_RUN' ? '--' : `${spec.passRate.toFixed(0)}%`}
        </span>
      </div>
      <div className="mt-2 flex flex-wrap items-center gap-1">
        <ImpactBadge spec={spec} />
        {spec.recommendedNext ? (
          <span className="inline-flex items-center gap-1 rounded-md border border-amber-300 bg-amber-100 px-1.5 py-0.5 text-[11px] font-semibold text-amber-800">
            <Target className="h-3.5 w-3.5" />
            Next
          </span>
        ) : null}
      </div>
      <h3 className="mt-2 text-sm font-semibold leading-5 text-foreground">{spec.title}</h3>
      <p className="mt-1 line-clamp-3 text-xs leading-5 text-muted-foreground">{spec.description}</p>
      <p className="mt-2 line-clamp-2 text-[11px] leading-4 text-muted-foreground">Impact: {spec.impactReason}</p>
      <div className="mt-3 flex items-center justify-between gap-2 text-[11px] text-muted-foreground">
        <span>{spec.status === 'NOT_RUN' ? 'No run yet' : `${spec.passed}/${spec.total} pass`}</span>
        {spec.latestRunId ? <span className="font-mono">{spec.latestRunId.replace('TEST-RUN-', '')}</span> : null}
      </div>
      <p className="mt-2 truncate font-mono text-[10px] text-muted-foreground" title={spec.path}>
        {spec.path}
      </p>
    </article>
  )
}

function CategoryColumn({ category }: { category: TestSuiteCategory }) {
  return (
    <section className="flex min-w-[260px] max-w-[280px] flex-1 flex-col rounded-lg border border-border bg-muted/20">
      <div className="border-b border-border p-3">
        <div className="flex items-start justify-between gap-2">
          <div>
            <p className="text-[10px] font-semibold uppercase text-muted-foreground">Category {category.order}</p>
            <h2 className="mt-0.5 text-sm font-bold text-foreground">{category.label}</h2>
          </div>
          <span className={cn('rounded-md px-2 py-1 text-xs font-bold tabular-nums', passRateClass(category.overallPassRate, category.validatedSpecs > 0 ? 'PASS' : 'NOT_RUN'))}>
            {category.validatedSpecs > 0 ? `${category.overallPassRate.toFixed(0)}%` : '--'}
          </span>
        </div>
        <p className="mt-2 min-h-10 text-xs leading-5 text-muted-foreground">{category.description}</p>
        <div className="mt-3 grid grid-cols-4 gap-1 text-center text-[10px]">
          <div className="rounded border border-border bg-card px-1 py-1">
            <p className="font-bold text-foreground">{category.totalTestSpecs}</p>
            <p className="text-muted-foreground">Specs</p>
          </div>
          <div className="rounded border border-border bg-card px-1 py-1">
            <p className="font-bold text-emerald-700">{category.perfectSpecs}</p>
            <p className="text-muted-foreground">Green</p>
          </div>
          <div className="rounded border border-border bg-card px-1 py-1">
            <p className="font-bold text-amber-700">{category.attentionSpecs}</p>
            <p className="text-muted-foreground">Work</p>
          </div>
          <div className="rounded border border-border bg-card px-1 py-1">
            <p className="font-bold text-muted-foreground">{category.notRunSpecs}</p>
            <p className="text-muted-foreground">Open</p>
          </div>
        </div>
      </div>

      <div className="flex flex-1 flex-col gap-2 p-2">
        {category.testSpecs.length === 0 ? (
          <div className="rounded-lg border border-dashed border-border p-4 text-xs leading-5 text-muted-foreground">
            No TestSpecs assigned yet.
          </div>
        ) : (
          category.testSpecs.map((spec) => <SpecCard key={spec.path} spec={spec} />)
        )}
      </div>
    </section>
  )
}

export function TestSuiteView() {
  const [suite, setSuite] = useState<TestSuiteResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    loadTestSuite()
  }, [])

  const loadTestSuite = async () => {
    try {
      setLoading(true)
      const response = await fetchTestSuite()
      setSuite(response)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load test suite')
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

  if (!suite) {
    return (
      <div className="flex h-full items-center justify-center">
        <p className="text-muted-foreground">No test suite data available</p>
      </div>
    )
  }

  return (
    <div className="flex h-full flex-col overflow-hidden">
      <div className="border-b border-border p-4">
        <div className="flex items-center gap-2">
          <Columns3 className="h-5 w-5 text-muted-foreground" />
          <h1 className="text-xl font-bold text-foreground">Testsuite</h1>
        </div>
        <p className="mt-1 text-sm text-muted-foreground">
          Seven quality columns for Janus system tests. Feature-specific tests stay with their feature specs in documentation/SPEC.
        </p>
        {suite.recommendedNext ? (
          <div className="mt-3 inline-flex items-center gap-2 rounded-lg border border-amber-300 bg-amber-50 px-3 py-2 text-sm text-amber-900">
            <Target className="h-4 w-4" />
            <span className="font-semibold">Next recommended:</span>
            <span>{suite.recommendedNext.title}</span>
            <span className="text-xs text-amber-700">Impact {suite.recommendedNext.impactScore}</span>
          </div>
        ) : null}
      </div>

      <div className="border-b border-border bg-muted/30 p-4">
        <div className="grid max-w-4xl grid-cols-5 gap-2">
          <div className="rounded-lg border border-border bg-card p-2">
            <p className="text-[10px] text-muted-foreground">Specs</p>
            <p className="mt-0.5 text-lg font-bold text-foreground">{suite.summary.totalTestSpecs}</p>
          </div>
          <div className="rounded-lg border border-border bg-card p-2">
            <p className="text-[10px] text-muted-foreground">Validated</p>
            <p className="mt-0.5 text-lg font-bold text-foreground">{suite.summary.validatedSpecs}</p>
          </div>
          <div className="rounded-lg border border-border bg-card p-2">
            <p className="text-[10px] text-muted-foreground">Green</p>
            <p className="mt-0.5 text-lg font-bold text-emerald-700">{suite.summary.perfectSpecs}</p>
          </div>
          <div className="rounded-lg border border-border bg-card p-2">
            <p className="text-[10px] text-muted-foreground">Needs Work</p>
            <p className="mt-0.5 text-lg font-bold text-amber-700">{suite.summary.attentionSpecs}</p>
          </div>
          <div className="rounded-lg border border-border bg-card p-2">
            <p className="text-[10px] text-muted-foreground">Overall</p>
            <p className={cn('mt-0.5 text-lg font-bold', suite.summary.overallPassRate === 100 ? 'text-emerald-700' : 'text-amber-700')}>
              {suite.summary.overallPassRate.toFixed(0)}%
            </p>
          </div>
        </div>
      </div>

      <div className="flex-1 overflow-auto p-4">
        <div className="flex min-w-max gap-3">
          {suite.categories.map((category) => (
            <CategoryColumn key={category.id} category={category} />
          ))}
        </div>
      </div>
    </div>
  )
}
