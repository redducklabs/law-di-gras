// Renders a ProviderView. Used by the provider page and the share panel preview,
// so the attorney previews exactly what the provider gets.
import type { ActionItem, Citation, Fact, ProviderView, TreatmentLine } from '../api/types'

export function fmtDate(d?: string | null) {
  if (!d) return null
  const dt = new Date(d.length === 10 ? `${d}T12:00:00` : d)
  return Number.isNaN(dt.getTime()) ? d : dt.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
}

function daysAgo(d?: string | null) {
  if (!d) return null
  const t = new Date(d.length === 10 ? `${d}T12:00:00` : d).getTime()
  if (Number.isNaN(t)) return null
  const n = Math.round((Date.now() - t) / 86_400_000)
  return n <= 0 ? 'today' : n === 1 ? 'yesterday' : `${n} days ago`
}

type OpenDoc = (sourceId: string, title: string, page?: number | null) => void

function DocChip({ c, onOpenDoc }: { c: Citation; onOpenDoc?: OpenDoc }) {
  return (
    <button
      type="button"
      onClick={() => onOpenDoc?.(c.source_id, c.source_title, c.page)}
      className="inline-flex items-center gap-1 rounded border border-slate-200 bg-slate-50 px-1.5 py-0.5 text-xs text-slate-600 hover:border-slate-400 hover:text-slate-900"
      title={c.quote}
    >
      {c.source_title}{c.page ? ` · p.${c.page}` : ''}
    </button>
  )
}

function Chips({ cits, onOpenDoc }: { cits?: Citation[]; onOpenDoc?: OpenDoc }) {
  if (!cits?.length) return null
  return <span className="ml-2 inline-flex flex-wrap gap-1 align-middle">{cits.map((c, i) => <DocChip key={i} c={c} onOpenDoc={onOpenDoc} />)}</span>
}

function Section({ title, children, hint }: { title: string; children: React.ReactNode; hint?: string }) {
  return (
    <section className="rounded-lg border border-slate-200 bg-white p-5">
      <div className="mb-3 flex items-baseline justify-between gap-3">
        <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-500">{title}</h2>
        {hint && <span className="text-xs text-slate-400">{hint}</span>}
      </div>
      {children}
    </section>
  )
}

function Empty({ children }: { children: React.ReactNode }) {
  return <p className="text-sm text-slate-400">{children}</p>
}

function CoverageBlock({ coverage, onOpenDoc }: { coverage: Fact[]; onOpenDoc?: OpenDoc }) {
  if (!coverage.length) return <Empty>No coverage information on file yet.</Empty>
  return (
    <ul className="space-y-2">
      {coverage.map((f) => (
        <li key={f.id} className="flex flex-wrap items-baseline justify-between gap-2">
          <span className="text-sm text-slate-600">{f.label}</span>
          <span className="text-base font-semibold text-slate-900">
            {f.value}
            {!f.verified && <span className="ml-2 rounded bg-amber-50 px-1.5 py-0.5 text-xs font-normal text-amber-700">unverified</span>}
            <Chips cits={f.citations} onOpenDoc={onOpenDoc} />
          </span>
        </li>
      ))}
    </ul>
  )
}

function Requests({ items, onOpenDoc }: { items: ActionItem[]; onOpenDoc?: OpenDoc }) {
  if (!items.length) return <Empty>Nothing outstanding from your office right now.</Empty>
  return (
    <ul className="divide-y divide-slate-100">
      {items.map((a, i) => (
        <li key={i} className="flex flex-wrap items-baseline justify-between gap-2 py-2 first:pt-0 last:pb-0">
          <span className="text-sm text-slate-900">
            {a.title}
            <Chips cits={a.citations} onOpenDoc={onOpenDoc} />
          </span>
          {a.due_date && (
            <span className={`text-xs ${a.status === 'overdue' ? 'font-semibold text-red-700' : 'text-slate-500'}`}>
              {a.status === 'overdue' ? 'Overdue · ' : 'Due '}{fmtDate(a.due_date)}
            </span>
          )}
        </li>
      ))}
    </ul>
  )
}

function Treatment({ lines, onOpenDoc }: { lines: TreatmentLine[]; onOpenDoc?: OpenDoc }) {
  if (!lines.length) return <Empty>No visits or bills from your office are recorded on the file yet.</Empty>
  return (
    <div className="space-y-4">
      {lines.map((t, i) => (
        <div key={i}>
          <dl className="grid grid-cols-2 gap-x-6 gap-y-3 sm:grid-cols-4">
            <Stat label="Visits on file" value={t.visit_count != null ? String(t.visit_count) : '—'} />
            <Stat label="First visit" value={fmtDate(t.first_visit) ?? '—'} />
            <Stat label="Most recent visit" value={fmtDate(t.last_visit) ?? '—'} sub={daysAgo(t.last_visit) ?? undefined} />
            <Stat label="Billed" value={t.billed?.value ?? '—'} />
          </dl>
          {(t.billed?.citations.length || t.citations.length) ? (
            <div className="mt-3 flex flex-wrap gap-1 text-xs text-slate-500">
              Source:<Chips cits={[...(t.billed?.citations ?? []), ...t.citations]} onOpenDoc={onOpenDoc} />
            </div>
          ) : null}
        </div>
      ))}
    </div>
  )
}

function Stat({ label, value, sub }: { label: string; value: string; sub?: string }) {
  return (
    <div>
      <dt className="text-xs text-slate-500">{label}</dt>
      <dd className="text-lg font-semibold text-slate-900">{value}</dd>
      {sub && <dd className="text-xs text-slate-400">{sub}</dd>}
    </div>
  )
}

export default function ProviderViewBody({ view, onOpenDoc, compact }: { view: ProviderView; onOpenDoc?: OpenDoc; compact?: boolean }) {
  return (
    <div className={compact ? 'space-y-3' : 'space-y-4'}>
      <header className="space-y-1">
        <p className="text-xs uppercase tracking-wide text-slate-500">Shared with {view.provider_name}</p>
        <h1 className={`${compact ? 'text-xl' : 'text-2xl'} font-semibold text-slate-900`}>
          Patient: {view.client_name}
        </h1>
        <p className="text-sm text-slate-500">{view.matter_title}</p>
      </header>

      <div className={`grid items-start gap-3 ${view.coverage ? 'sm:grid-cols-2' : ''}`}>
        <div className={`rounded-lg border p-5 ${view.case_active ? 'border-emerald-200 bg-emerald-50' : 'border-slate-300 bg-slate-100'}`}>
          <div className="flex items-center gap-2">
            <span className={`h-2.5 w-2.5 rounded-full ${view.case_active ? 'bg-emerald-500' : 'bg-slate-400'}`} />
            <span className={`text-xl font-semibold ${view.case_active ? 'text-emerald-900' : 'text-slate-700'}`}>
              {view.case_active ? 'Case active' : 'Case closed'}
            </span>
          </div>
          {view.stage && <p className="mt-1 text-sm text-slate-700">Stage: <span className="font-medium">{view.stage}</span></p>}
          {view.last_activity_date && (
            <p className="mt-1 text-sm text-slate-600">Last activity on the file {fmtDate(view.last_activity_date)} ({daysAgo(view.last_activity_date)})</p>
          )}
        </div>
        {view.coverage && (
          <div className="rounded-lg border border-slate-200 bg-white p-5">
            <h2 className="mb-2 text-sm font-semibold uppercase tracking-wide text-slate-500">Coverage behind the case</h2>
            <CoverageBlock coverage={view.coverage} onOpenDoc={onOpenDoc} />
          </div>
        )}
      </div>

      {view.requests && (
        <Section title="What the firm needs from your office">
          <Requests items={view.requests} onOpenDoc={onOpenDoc} />
        </Section>
      )}

      {view.treatment && (
        <Section title="Your patient's visits and bills" hint="As recorded on the firm's file">
          <Treatment lines={view.treatment} onOpenDoc={onOpenDoc} />
          {!!view.liens?.length && (
            <ul className="mt-4 space-y-2 border-t border-slate-100 pt-4">
              {view.liens.map((f) => (
                <li key={f.id} className="flex flex-wrap items-baseline justify-between gap-2">
                  <span className="text-sm text-slate-600">Your lien on file · {f.label}</span>
                  <span className="text-base font-semibold text-slate-900">
                    {f.value}
                    {!f.verified && <span className="ml-2 rounded bg-amber-50 px-1.5 py-0.5 text-xs font-normal text-amber-700">unverified</span>}
                    <Chips cits={f.citations} onOpenDoc={onOpenDoc} />
                  </span>
                </li>
              ))}
            </ul>
          )}
        </Section>
      )}

      {view.timeline && (
        <Section title="Case milestones">
          {view.timeline.length ? (
            <ol className="space-y-1.5">
              {view.timeline.map((e, i) => (
                <li key={i} className="flex gap-3 text-sm">
                  <span className={`w-28 shrink-0 tabular-nums ${e.is_future ? 'text-blue-700' : 'text-slate-500'}`}>{fmtDate(e.date)}</span>
                  <span className="text-slate-900">{e.label}{e.is_future && <span className="ml-2 text-xs text-blue-700">upcoming</span>}</span>
                </li>
              ))}
            </ol>
          ) : <Empty>No milestones to show yet.</Empty>}
        </Section>
      )}

      {view.documents && (
        <Section title="Records shared with you">
          {view.documents.length ? (
            <ul className="flex flex-wrap gap-2">
              {view.documents.map((d) => (
                <li key={d.source_id}>
                  <button
                    type="button"
                    onClick={() => onOpenDoc?.(d.source_id, d.title)}
                    className="rounded-md border border-slate-200 bg-white px-3 py-1.5 text-sm text-slate-800 hover:border-slate-400"
                  >
                    {d.title}
                  </button>
                </li>
              ))}
            </ul>
          ) : <Empty>No records shared yet.</Empty>}
        </Section>
      )}
    </div>
  )
}
