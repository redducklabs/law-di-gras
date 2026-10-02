// Renders a ProviderView. Used by the provider page and the share panel preview,
// so the attorney previews exactly what the provider gets.
import type { ReactNode } from 'react'
import type { ActionItem, Citation, Fact, ProviderView, TreatmentLine } from '../api/types'
import { Badge, Card, daysFromToday, fmtDate as fmt, prettyTitle, relDays } from '../components'

export function fmtDate(d?: string | null) {
  return d ? fmt(d, true) : null
}

/** Days since the last visit before attendance is flagged. */
const ATTENDANCE_GAP_DAYS = 30

type OpenDoc = (sourceId: string, title: string, page?: number | null) => void

function DocChip({ c, onOpenDoc }: { c: Citation; onOpenDoc?: OpenDoc }) {
  const label = `${prettyTitle(c.source_title)}${c.page ? ` · p.${c.page}` : ''}`
  return (
    <button type="button" title={`${c.source_title}\n“${c.quote}”`}
      onClick={() => onOpenDoc?.(c.source_id, c.source_title, c.page)}
      className={`inline-flex max-w-[15rem] min-w-0 cursor-pointer items-center gap-1 rounded-full px-2 py-0.5 align-middle text-[11px] font-medium sm:max-w-[20rem] ${c.verified ? 'bg-brand-50 text-brand-700 hover:bg-brand-100' : 'border border-dashed border-warn-600 bg-warn-50 text-warn-700'}`}>
      <span className="truncate">{label}</span>
      {!c.verified && <span className="shrink-0 text-[9.5px] font-semibold uppercase">unverified</span>}
    </button>
  )
}

function Chips({ cits, onOpenDoc, max = 2 }: { cits?: Citation[]; onOpenDoc?: OpenDoc; max?: number }) {
  if (!cits?.length) return null
  return (
    <span className="inline-flex max-w-full flex-wrap gap-1 align-middle">
      {cits.slice(0, max).map((c, i) => <DocChip key={i} c={c} onOpenDoc={onOpenDoc} />)}
      {cits.length > max && <span className="text-[11px] text-slate-400">+{cits.length - max}</span>}
    </span>
  )
}

function Empty({ children }: { children: ReactNode }) {
  return <div className="rounded-lg bg-page px-4 py-5 text-center text-[13px] text-slate-400">{children}</div>
}

function MoneyRow({ f, label, onOpenDoc }: { f: Fact; label?: string; onOpenDoc?: OpenDoc }) {
  return (
    <li className="border-t border-line-soft py-2.5 first:border-0 first:pt-0">
      <div className="flex flex-wrap items-baseline justify-between gap-x-3">
        <span className="text-[13px] text-slate-600">{label ?? f.label}</span>
        <span className={`text-[20px] font-semibold tracking-tight tabular-nums ${f.verified ? 'text-slate-900' : 'text-warn-700'}`}>{f.value}</span>
      </div>
      <div className="mt-1"><Chips cits={f.citations} onOpenDoc={onOpenDoc} /></div>
    </li>
  )
}

function Requests({ items, onOpenDoc }: { items: ActionItem[]; onOpenDoc?: OpenDoc }) {
  if (!items.length) return <Empty>Nothing outstanding from your office right now.</Empty>
  return (
    <ol>
      {items.map((a, i) => {
        const n = daysFromToday(a.due_date)
        const overdue = a.status === 'overdue'
        return (
          <li key={i} className="flex items-start gap-3 border-t border-line-soft py-3 first:border-0 first:pt-0">
            <span className={`mt-px grid h-5 w-5 shrink-0 place-items-center rounded-full text-[11px] font-semibold ${overdue ? 'bg-danger-600 text-white' : 'bg-brand-600 text-white'}`}>{i + 1}</span>
            <div className="min-w-0 flex-1">
              <div className="text-[14px] font-medium text-slate-900">{a.title}</div>
              {a.due_date && (
                <div className={`text-[12.5px] ${overdue ? 'font-medium text-danger-700' : 'text-slate-500'}`}>
                  {overdue ? 'Overdue' : 'Due'} · {fmtDate(a.due_date)}{n != null && ` (${relDays(n)})`}
                </div>
              )}
              <div className="mt-1"><Chips cits={a.citations} onOpenDoc={onOpenDoc} max={1} /></div>
            </div>
          </li>
        )
      })}
    </ol>
  )
}

function Stat({ label, value, sub }: { label: string; value: string; sub?: string | null }) {
  return (
    <div className="rounded-lg bg-page px-3 py-2.5">
      <dt className="text-[11.5px] text-slate-500">{label}</dt>
      <dd className="text-[18px] font-semibold tracking-tight tabular-nums text-slate-900">{value}</dd>
      {sub && <dd className="text-[11.5px] text-slate-400">{sub}</dd>}
    </div>
  )
}

function Attendance({ line }: { line: TreatmentLine }) {
  const n = daysFromToday(line.last_visit)
  if (n == null) return null
  const gap = Math.max(0, -n)
  const ok = gap <= ATTENDANCE_GAP_DAYS
  return (
    <div className={`mb-3 flex flex-wrap items-center gap-x-2 rounded-lg px-3 py-2 text-[13px] ${ok ? 'bg-ok-50 text-ok-700' : 'bg-warn-50 text-warn-700'}`}>
      <span className={`h-2 w-2 shrink-0 rounded-full ${ok ? 'bg-ok-600' : 'bg-warn-600'}`} />
      {ok
        ? <span>Patient seen {relDays(n)} · {fmtDate(line.last_visit)}</span>
        : <><span className="font-semibold">No visit recorded in {gap} days</span><span>· last visit {fmtDate(line.last_visit)}</span></>}
    </div>
  )
}

function Treatment({ lines, onOpenDoc }: { lines: TreatmentLine[]; onOpenDoc?: OpenDoc }) {
  if (!lines.length) return <Empty>No visits or bills from your office are recorded on the file yet.</Empty>
  return (
    <div className="space-y-4">
      {lines.map((t, i) => {
        const ago = daysFromToday(t.last_visit)
        return (
          <div key={i}>
            {lines.length > 1 && <div className="mb-2 text-[13px] font-semibold">{t.provider}</div>}
            <Attendance line={t} />
            <dl className="grid grid-cols-2 gap-2 sm:grid-cols-4">
              <Stat label="Visits on file" value={t.visit_count != null ? String(t.visit_count) : '—'} />
              <Stat label="First visit" value={fmtDate(t.first_visit) ?? '—'} />
              <Stat label="Most recent visit" value={fmtDate(t.last_visit) ?? '—'} sub={ago != null ? relDays(ago) : null} />
              <Stat label="Billed" value={t.billed?.value ?? '—'} />
            </dl>
            {(t.billed?.citations.length || t.citations.length) ? (
              <div className="mt-2 flex flex-wrap items-center gap-1 text-[11.5px] text-slate-400">
                Source <Chips cits={[...(t.billed?.citations ?? []), ...t.citations]} onOpenDoc={onOpenDoc} max={3} />
              </div>
            ) : null}
          </div>
        )
      })}
    </div>
  )
}

export default function ProviderViewBody({ view, onOpenDoc, compact }: { view: ProviderView; onOpenDoc?: OpenDoc; compact?: boolean }) {
  const ago = daysFromToday(view.last_activity_date)
  const gap = compact ? 'space-y-3' : 'space-y-5'
  return (
    <div className={gap}>
      <header>
        <div className="text-[11px] font-semibold uppercase tracking-wider text-brand-700">Case update for {view.provider_name}</div>
        <h1 className={`mt-1 font-semibold tracking-tight text-slate-900 ${compact ? 'text-[19px]' : 'text-[24px]'}`}>
          Patient: {view.client_name}
        </h1>
        <p className="text-[13px] text-slate-500">{view.matter_title}</p>
      </header>

      {/* The two questions a provider has: is it alive, is there money. */}
      <div className={`grid grid-cols-1 items-start gap-3 ${view.coverage ? 'sm:grid-cols-2' : ''}`}>
        <div className={`rounded-xl border p-5 ${view.case_active ? 'border-ok-600/25 bg-ok-50' : 'border-line bg-slate-100'}`}>
          <div className="flex items-center gap-2.5">
            <span className="relative flex h-3 w-3">
              {view.case_active && <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-ok-600 opacity-40" />}
              <span className={`relative inline-flex h-3 w-3 rounded-full ${view.case_active ? 'bg-ok-600' : 'bg-slate-400'}`} />
            </span>
            <span className={`text-[22px] font-semibold tracking-tight ${view.case_active ? 'text-ok-700' : 'text-slate-700'}`}>
              {view.case_active ? 'Case active' : 'Case closed'}
            </span>
          </div>
          {view.status_line && <p className="mt-2 text-[13.5px] leading-snug text-slate-700">{view.status_line}</p>}
          <div className="mt-3 flex flex-wrap items-center gap-2 text-[12.5px] text-slate-600">
            {view.stage && <Badge tone="brand">{view.stage}</Badge>}
            {view.last_activity_date && <span>Last activity {fmtDate(view.last_activity_date)}{ago != null && ` · ${relDays(ago)}`}</span>}
          </div>
        </div>
        {view.coverage && (
          <Card title="Coverage behind the case">
            {view.coverage.length
              ? <ul>{view.coverage.map(f => <MoneyRow key={f.id} f={f} onOpenDoc={onOpenDoc} />)}</ul>
              : <Empty>No coverage information on file yet.</Empty>}
          </Card>
        )}
      </div>

      {!!view.updates?.length && (
        <Card title={view.updates_since ? `Case updates since ${fmtDate(view.updates_since)}` : 'Case updates'}
          extra={<Badge tone="ok">{view.updates.length} new</Badge>}>
          <ul>
            {view.updates.map((e, i) => (
              <li key={i} className="flex items-start gap-3 border-t border-line-soft py-2 text-[13.5px] first:border-0 first:pt-0">
                <span className="mt-[7px] h-2 w-2 shrink-0 rounded-full bg-ok-600" />
                <span className="min-w-0 flex-1 text-slate-800">{e.label}</span>
                <span className="shrink-0 text-[12px] tabular-nums text-slate-400">{fmtDate(e.date)}</span>
              </li>
            ))}
          </ul>
        </Card>
      )}

      {view.requests && (
        <Card className="border-l-4 !border-l-brand-600" title="What the firm needs from your office"
          extra={view.requests.length > 0 && <Badge tone={view.requests.some(r => r.status === 'overdue') ? 'danger' : 'brand'}>{view.requests.length} open</Badge>}>
          <Requests items={view.requests} onOpenDoc={onOpenDoc} />
        </Card>
      )}

      {view.treatment && (
        <Card title="Your patient's visits and bills" extra={<span className="text-[12px] text-slate-400">As recorded on the firm's file</span>}>
          <Treatment lines={view.treatment} onOpenDoc={onOpenDoc} />
          {!!view.liens?.length && (
            <ul className="mt-4 border-t border-line-soft pt-3">
              {view.liens.map(f => <MoneyRow key={f.id} f={f} label={`Your lien on file · ${f.label}`} onOpenDoc={onOpenDoc} />)}
            </ul>
          )}
        </Card>
      )}

      {view.timeline && (
        <Card title="Case milestones">
          {view.timeline.length ? (
            <ol className="relative ml-1 border-l border-line pl-4">
              {view.timeline.map((e, i) => (
                <li key={i} className="relative py-1.5 text-[13px]">
                  <span className={`absolute -left-[21px] top-[11px] h-2.5 w-2.5 rounded-full ring-2 ring-white ${e.is_future ? 'bg-white !ring-warn-600' : 'bg-brand-500'}`} />
                  <span className={`mr-2 tabular-nums ${e.is_future ? 'text-warn-700' : 'text-slate-400'}`}>{fmtDate(e.date)}</span>
                  <span className="text-slate-800">{e.label}</span>
                  {e.is_future && <Badge tone="warn" className="ml-2">upcoming</Badge>}
                </li>
              ))}
            </ol>
          ) : <Empty>No milestones to show yet.</Empty>}
        </Card>
      )}

      {view.documents && (
        <Card title="Records shared with you">
          {view.documents.length ? (
            <ul className="grid grid-cols-1 gap-2 sm:grid-cols-2">
              {view.documents.map(d => (
                <li key={d.source_id}>
                  <button type="button" onClick={() => onOpenDoc?.(d.source_id, d.title)}
                    className="flex w-full cursor-pointer items-center gap-2.5 rounded-lg border border-line px-3 py-2.5 text-left text-[13px] text-slate-800 hover:border-brand-200 hover:bg-brand-50/50">
                    <svg width="16" height="16" viewBox="0 0 16 16" className="shrink-0 text-brand-600" fill="currentColor" aria-hidden><path d="M4 1h6l4 4v10H4z" opacity=".3" /><path d="M10 1v4h4" /></svg>
                    <span className="min-w-0 truncate">{prettyTitle(d.title)}</span>
                  </button>
                </li>
              ))}
            </ul>
          ) : <Empty>No records shared yet.</Empty>}
        </Card>
      )}
    </div>
  )
}
