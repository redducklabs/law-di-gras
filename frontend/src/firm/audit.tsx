// Built-in audit on the brief: fetch the dashboard audit, poll while it runs, mark flagged items quietly.
// A missing route, 404 or error degrades to nothing.
import { useEffect, useState } from 'react'
import type { AuditFlag, AuditReport } from '../api/types'
import { ProgressBar, pctOf } from '../components'

const POLL_MS = 5000

export function useAudit(matterId: string) {
  const [report, setReport] = useState<AuditReport | null>(null)
  useEffect(() => {
    let alive = true
    let timer: ReturnType<typeof setTimeout> | undefined
    const load = async () => {
      try {
        const res = await fetch(`/api/matters/${encodeURIComponent(matterId)}/audit?target=dashboard`)
        if (!res.ok) { if (alive) setReport(null); return }
        const r = (await res.json()) as AuditReport
        if (!alive) return
        setReport(r)
        if (r.run && (r.run.status === 'queued' || r.run.status === 'running')) timer = setTimeout(load, POLL_MS)
      } catch {
        if (alive) setReport(null)
      }
    }
    load()
    return () => { alive = false; if (timer) clearTimeout(timer) }
  }, [matterId])
  return report
}

export interface AuditIndex {
  item: (id: string) => AuditFlag[]
  /** Flags on a section, or on any of the given item ids. */
  section: (section: string, ids?: string[]) => AuditFlag[]
}

/** Only critical and major flags are marked on screen; minor ones are hover-only notes on the badge. */
const serious = (f: AuditFlag) => f.severity === 'critical' || f.severity === 'major'

export function indexAudit(report: AuditReport | null): AuditIndex {
  const flags = report?.run?.status === 'done' ? report.flags.filter(serious) : []
  return {
    item: id => flags.filter(f => f.item_id === id),
    section: (section, ids = []) => flags.filter(f => f.section === section || ids.includes(f.item_id)),
  }
}

const isCritical = (flags: AuditFlag[]) => flags.some(f => f.severity === 'critical')
const noteOf = (flags: AuditFlag[]) => flags.map(f => `${f.severity.toUpperCase()} · ${f.check}: ${f.note}`).join('\n')

/** Quiet marker on a flagged fact: a small dot, the audit note on hover. */
export function FlagDot({ flags }: { flags: AuditFlag[] }) {
  if (!flags.length) return null
  const crit = isCritical(flags)
  return (
    <span title={`Audit flag\n${noteOf(flags)}`} aria-label="Audit flag"
      className={`inline-block h-2 w-2 shrink-0 cursor-help rounded-full align-middle ring-2 ${crit ? 'bg-danger-600 ring-danger-200' : 'bg-warn-600 ring-warn-200'}`} />
  )
}

/** "N flagged" for a collapsed row. */
export function FlagCount({ flags }: { flags: AuditFlag[] }) {
  if (!flags.length) return null
  const crit = isCritical(flags)
  return (
    <span title={noteOf(flags)}
      className={`cursor-help rounded-full px-2 py-0.5 text-[11px] font-semibold ${crit ? 'bg-danger-50 text-danger-700' : 'bg-warn-50 text-warn-700'}`}>
      {flags.length} flagged
    </span>
  )
}

/** Header badge: progress while the audit runs, then "Audited · N flags". */
export function AuditBadge({ report }: { report: AuditReport | null }) {
  if (!report?.run) return null
  const r = report.run
  if (r.status === 'queued' || r.status === 'running') {
    return (
      <span className="inline-flex w-56 items-center gap-2 rounded-lg border border-line bg-surface px-2.5 py-1.5" title="Built-in audit: every claim re-checked against the record">
        <ProgressBar progress={r} className="flex-1" />
        <span className="sr-only">Audit running · {pctOf(r)}%</span>
      </span>
    )
  }
  if (r.status === 'failed') return null
  const top = report.flags.filter(serious)
  const n = top.length
  const minor = report.flags.length - n
  const crit = isCritical(top)
  const hover = `Built-in audit checked ${report.items_checked} items against the record`
    + (n ? `\n${noteOf(top)}` : '')
    + (minor ? `\n${minor} minor note${minor === 1 ? '' : 's'} (wording, no action needed)` : '')
  return (
    <span title={hover}
      className={`inline-flex shrink-0 cursor-help items-center gap-1.5 rounded-lg border px-2.5 py-1.5 text-[12px] font-semibold ${
        !n ? 'border-line bg-surface text-ok-700' : crit ? 'border-danger-200 bg-danger-50 text-danger-700' : 'border-warn-200 bg-warn-50 text-warn-700'}`}>
      <svg width="12" height="12" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden><path d="M8 1.5l5.5 2v4.2c0 3.2-2.3 5.6-5.5 6.8-3.2-1.2-5.5-3.6-5.5-6.8V3.5z" /><path d="M5.5 8l1.8 1.8L10.5 6.5" /></svg>
      {n ? `Audited · ${n} to review` : 'Audited · no issues'}
    </span>
  )
}
