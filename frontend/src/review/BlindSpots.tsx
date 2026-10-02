import { useState } from 'react'
import type { AuditFlag, AuditReport, CaseReview, Citation, ReviewCategory, ReviewFinding } from '../api/types'
import { Badge, Card, ProgressBar, SourceChips, fmtDate, pctOf, type Tone } from '../components'
import { useReviewAudit } from './hooks'

const CATEGORY: Record<ReviewCategory, { label: string; tone: Tone }> = {
  conflict: { label: 'Conflict', tone: 'danger' },
  inconsistency: { label: 'Inconsistent account', tone: 'danger' },
  gap: { label: 'Gap', tone: 'warn' },
  stale: { label: 'Stale thread', tone: 'warn' },
  risk: { label: 'Risk', tone: 'danger' },
  opportunity: { label: 'Opportunity', tone: 'ok' },
}

const SEV: Record<ReviewFinding['severity'], { bar: string; label: string; text: string }> = {
  high: { bar: 'bg-danger-600', label: 'High', text: 'text-danger-700' },
  medium: { bar: 'bg-warn-600', label: 'Medium', text: 'text-warn-700' },
  low: { bar: 'bg-slate-300', label: 'Low', text: 'text-slate-500' },
}

/** Findings shown before "Show all". */
const VISIBLE = 5

/**
 * "Blind spots": what an item-by-item read of the file misses, from the agentic whole-case review.
 * Every finding is verified against verbatim quotes; chips open the source at the quote.
 */
export function BlindSpots({ review, onOpenSource, loading = false, onRun, collapsible = false }: {
  review: CaseReview | null | undefined
  onOpenSource?: (c: Citation) => void
  loading?: boolean
  onRun?: () => void
  /** Render as a thin full-width bar that expands (animated) on click. */
  collapsible?: boolean
}) {
  const [expanded, setExpanded] = useState(false)
  const [open, setOpen] = useState(false)
  const findings = review?.findings ?? []
  const high = findings.filter(f => f.severity === 'high').length
  const run = review?.run ?? null
  const running = run?.status === 'running' || run?.status === 'queued'
  const audit = useReviewAudit(review?.matter_id, findings.length ? review?.generated_at : undefined)
  const flagsFor = (id: string) => (audit?.run.status === 'done' ? audit.flags.filter(f => f.item_id === id) : [])
  const shown = expanded ? findings : findings.slice(0, VISIBLE)

  const badges = (
    <div className="flex flex-wrap items-center gap-1.5">
      {high > 0 && <Badge tone="danger">{high} high</Badge>}
      {findings.length > 0 && <Badge tone="brand">{findings.length} found</Badge>}
      {running && run && <Badge tone="brand">Reviewing · {pctOf(run)}%</Badge>}
      {findings.length > 0 && !running && <AuditBadge audit={audit} />}
      <Badge>AI file review · draft</Badge>
    </div>
  )

  const body = (
    <>
      <p className="-mt-1 mb-3 text-[12.5px] text-slate-500">
        What a page-by-page read misses: conflicts, gaps, stale threads and unused leverage across the whole file.
        Each point is checked against the quoted record.
      </p>

      {run && (running || run.status === 'failed') && (
        <div className="mb-3 rounded-lg border border-line-soft bg-page/60 px-3 py-2.5">
          <ProgressBar progress={run} />
          <div className="mt-1 text-[11px] text-slate-400">
            {running
              ? `A new whole-file review is running (usually 6–8 minutes).${findings.length ? ' The previous findings stay below until it finishes.' : ''}`
              : 'The previous review is kept.'}
          </div>
        </div>
      )}

      {(loading || running) && !findings.length && (
        <div className="space-y-2">
          {[0, 1, 2].map(i => <div key={i} className="h-20 animate-pulse rounded-lg bg-slate-100" />)}
          {!running && <div className="text-center text-[12px] text-slate-400">Loading the file review…</div>}
        </div>
      )}

      {!loading && !running && !findings.length && (
        <div className="rounded-lg bg-slate-50 px-4 py-6 text-center text-[13px] text-slate-500">
          {review ? 'The review found nothing the dashboard does not already show.' : 'No file review yet.'}
          {onRun && (
            <div className="mt-3">
              <button type="button" onClick={() => onRun()}
                className="cursor-pointer rounded-lg bg-brand-700 px-3 py-1.5 text-[12.5px] font-semibold text-white hover:bg-brand-800">
                Run file review
              </button>
            </div>
          )}
        </div>
      )}

      {findings.length > 0 && (
        <ol className="space-y-2.5">
          {shown.map(f => <Finding key={f.id} f={f} flags={flagsFor(f.id)} onOpenSource={onOpenSource} />)}
        </ol>
      )}

      {findings.length > VISIBLE && (
        <button type="button" onClick={() => setExpanded(v => !v)}
          className="mt-2 cursor-pointer px-1 text-[12px] font-semibold text-brand-700 hover:underline">
          {expanded ? 'Show fewer' : `Show all ${findings.length}`}
        </button>
      )}

      {review && findings.length > 0 && (
        <div className="mt-3 border-t border-line-soft pt-2 text-[11px] text-slate-400">
          Reviewed {fmtDate(review.generated_at)} · draft for attorney review
        </div>
      )}
    </>
  )

  if (!collapsible) {
    return <Card title={<span className="inline-flex items-center gap-2"><EyeIcon /> Blind spots</span>} extra={badges}>{body}</Card>
  }
  const top = findings[0]
  return (
    <section className="rounded-xl border border-line bg-surface shadow-card">
      <button type="button" onClick={() => setOpen(v => !v)} aria-expanded={open}
        className="flex w-full cursor-pointer items-center gap-3 rounded-xl px-4 py-3 text-left hover:bg-page/60 sm:px-5">
        <Chevron open={open} />
        <span className="inline-flex shrink-0 items-center gap-2 text-[14px] font-semibold text-slate-900"><EyeIcon /> Blind spots</span>
        <span className={`hidden min-w-0 flex-1 truncate text-[12.5px] text-slate-500 transition-opacity md:block ${open ? 'opacity-0' : 'opacity-100'}`}>
          {top ? <>Top: {top.title}</> : !loading && !review ? 'Run a whole-file review for conflicts, gaps and stale threads' : ''}
        </span>
        <span className="ml-auto shrink-0">{badges}</span>
      </button>
      <div className="grid transition-[grid-template-rows] duration-300 ease-out" style={{ gridTemplateRows: open ? '1fr' : '0fr' }}>
        <div className="overflow-hidden">
          <div className={`px-4 pb-5 transition-opacity duration-300 sm:px-5 ${open ? 'opacity-100' : 'opacity-0'}`}>{body}</div>
        </div>
      </div>
    </section>
  )
}

function Chevron({ open }: { open: boolean }) {
  return (
    <svg width="14" height="14" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden
      className={`shrink-0 text-slate-400 transition-transform duration-300 ${open ? 'rotate-90' : ''}`}>
      <path d="M6 3l5 5-5 5" />
    </svg>
  )
}

function Finding({ f, flags, onOpenSource }: { f: ReviewFinding; flags: AuditFlag[]; onOpenSource?: (c: Citation) => void }) {
  const cat = CATEGORY[f.category]
  const sev = SEV[f.severity]
  return (
    <li className="relative overflow-hidden rounded-lg border border-line bg-surface py-3 pl-4 pr-3.5">
      <span className={`absolute inset-y-0 left-0 w-1 ${sev.bar}`} aria-hidden />
      <div className="flex flex-wrap items-center gap-1.5">
        <Badge tone={cat.tone}>{cat.label}</Badge>
        <span className={`text-[10.5px] font-semibold uppercase tracking-wider ${sev.text}`}>{sev.label}</span>
        {!f.verified && <Badge tone="warn">unverified</Badge>}
      </div>
      <div className="mt-1.5 text-[14px] font-semibold leading-snug text-slate-900">{f.title}</div>
      <div className="mt-1 text-[13px] leading-relaxed text-slate-600">{f.why_it_matters}</div>
      <div className="mt-2 flex items-start gap-1.5 rounded-md bg-brand-50/70 px-2.5 py-1.5 text-[12.5px] text-brand-800">
        <ArrowIcon />
        <span><span className="font-semibold">Next step: </span>{f.suggested_next_step}</span>
      </div>
      <div className="mt-2"><SourceChips citations={f.citations} onOpen={onOpenSource} max={3} /></div>
      {flags.map((fl, i) => (
        <div key={i} className="mt-2 rounded-md border border-dashed border-warn-600/60 bg-warn-50 px-2.5 py-1.5 text-[12.5px] text-warn-700">
          <span className="font-semibold">Audit flag{fl.severity === 'minor' ? '' : ` (${fl.severity})`}: </span>{fl.note}
          {fl.citations.length > 0 && <div className="mt-1"><SourceChips citations={fl.citations} onOpen={onOpenSource} max={2} /></div>}
        </div>
      ))}
    </li>
  )
}

function EyeIcon() {
  return (
    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden className="text-brand-700">
      <path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7S2 12 2 12z" /><circle cx="12" cy="12" r="3" />
    </svg>
  )
}

function ArrowIcon() {
  return (
    <svg width="12" height="12" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden className="mt-[3px] shrink-0">
      <path d="M2 8h11M9 4l4 4-4 4" />
    </svg>
  )
}

/** "Unaudited" until the built-in audit is done; then "Audited · N flags". Missing audit route → Unaudited. */
function AuditBadge({ audit }: { audit: AuditReport | null }) {
  if (!audit || audit.run.status === 'failed') return <Badge>Unaudited</Badge>
  if (audit.run.status !== 'done') return <Badge>Audit running · {pctOf(audit.run)}%</Badge>
  const n = audit.flags.length
  return <Badge tone={n ? 'warn' : 'ok'}>Audited · {n} flag{n === 1 ? '' : 's'}</Badge>
}
