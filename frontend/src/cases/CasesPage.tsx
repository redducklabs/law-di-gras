// Cases landing page: every matter, most-needs-attention first (the API sorts). Sample rows are
// fictional demo rows, visibly labeled and never clickable. Integration wires the route.
import type { ReactNode } from 'react'
import type { CaseRow, Citation, Fact } from '../api/types'
import { Badge, Fonts, SourceChip, daysFromToday, fmtDate, money, relDays, type Tone } from '../components'

function reasonTone(r: string): Tone {
  if (/overdue|statute|\bSOL\b/i.test(r)) return 'danger'
  if (/deadline|no client contact/i.test(r)) return 'warn'
  return 'neutral'
}

/** Money cell: the amount when we have it (full sentence on hover), else the clamped value. */
function MoneyCell({ fact, extra, onChip }: { fact?: Fact | null; extra?: ReactNode; onChip?: (c: Citation) => void }) {
  if (!fact) return <span className="text-[12.5px] text-slate-300">—</span>
  // Prefer the bare amount when the value is a sentence ("$118,400 billed across 9 providers"); keep ranges.
  const wordy = /[a-z]{3,}/i.test(fact.value.replace(/^[^a-z]*/i, '')) && !/[–-]\s*\$/.test(fact.value)
  const short = fact.amount != null && wordy ? money(fact.amount) : fact.value
  return (
    <div className="min-w-0">
      <div title={fact.value}
        className={`line-clamp-2 text-[13.5px] font-semibold leading-snug tabular-nums ${fact.verified ? 'text-slate-900' : 'text-warn-700'}`}>
        {short}
      </div>
      {extra && <div className="truncate text-[11.5px] text-slate-500">{extra}</div>}
      {fact.citations[0] && <div className="mt-1 flex min-w-0 [&>button]:max-w-full"><SourceChip citation={fact.citations[0]} compact onOpen={onChip} /></div>}
    </div>
  )
}

function Row({ r, onOpen }: { r: CaseRow; onOpen: (id: string) => void }) {
  const open = () => !r.sample && onOpen(r.id)
  const deadlineIn = daysFromToday(r.next_deadline?.date)
  const contactAge = daysFromToday(r.last_client_contact)
  const cov = r.coverage[0]
  const cells = (
    <>
      {/* Client / matter */}
      <div className="min-w-0 lg:col-span-4">
        <div className="flex flex-wrap items-center gap-2">
          <span className="truncate text-[15px] font-semibold text-slate-900">{r.client_name}</span>
          {r.stage && <Badge tone="brand">{r.stage}</Badge>}
          {r.sample && <Badge tone="neutral" className="border border-dashed border-slate-300">Sample · not from Clio</Badge>}
        </div>
        <div className="truncate text-[12.5px] text-slate-500">{r.display_number} · {r.title}</div>
        {r.attention_reasons.length > 0 ? (
          <div className="mt-2 flex flex-wrap gap-1.5">
            {r.attention_reasons.map(x => <Badge key={x} tone={reasonTone(x)}>{x}</Badge>)}
          </div>
        ) : <div className="mt-2 text-[12px] text-ok-700">Nothing needs attention</div>}
      </div>

      {/* Next deadline + last contact */}
      <div className="min-w-0 lg:col-span-3">
        <Label>Next deadline</Label>
        {r.next_deadline ? (
          <>
            <div className={`text-[13px] font-semibold ${deadlineIn != null && deadlineIn <= 14 ? 'text-warn-700' : 'text-slate-900'}`}>
              {fmtDate(r.next_deadline.date, true)}{deadlineIn != null && <span className="font-normal text-slate-500"> · {relDays(deadlineIn)}</span>}
            </div>
            <div className="line-clamp-1 text-[12px] text-slate-500" title={r.next_deadline.label}>{r.next_deadline.label}</div>
          </>
        ) : <div className="text-[12.5px] text-slate-300">—</div>}
        <div className="mt-1.5 text-[12px] text-slate-500">
          Client contact {r.last_client_contact
            ? <span className={contactAge != null && contactAge <= -30 ? 'font-semibold text-warn-700' : 'text-slate-700'}>{relDays(contactAge ?? 0)}</span>
            : <span className="text-slate-300">—</span>}
        </div>
      </div>

      {/* Money */}
      <div className="grid min-w-0 grid-cols-3 gap-3 lg:col-span-5">
        <div className="min-w-0"><Label>Specials</Label><MoneyCell fact={r.specials} onChip={open} /></div>
        <div className="min-w-0"><Label>Coverage</Label>
          <MoneyCell fact={cov} onChip={open} extra={r.coverage.length > 1 ? `+${r.coverage.length - 1} more` : undefined} />
        </div>
        <div className="min-w-0"><Label>Value (draft)</Label>
          {r.case_value ? <MoneyCell fact={r.case_value} onChip={open} />
            : <div className="text-[12px] text-slate-400">{r.digested ? 'Not enough in the record' : 'Not digested yet'}</div>}
        </div>
      </div>
    </>
  )
  const base = 'grid grid-cols-1 gap-4 rounded-xl border bg-surface p-4 text-left shadow-card sm:p-5 lg:grid-cols-12 lg:items-start'
  return r.sample ? (
    <div aria-disabled className={`${base} cursor-default border-dashed border-line opacity-60`}>{cells}</div>
  ) : (
    <div role="link" tabIndex={0} onClick={open} onKeyDown={e => (e.key === 'Enter' || e.key === ' ') && open()}
      className={`${base} group cursor-pointer border-line transition-shadow hover:border-brand-200 hover:shadow-pop focus-visible:outline-2 focus-visible:outline-brand-500`}>
      {cells}
    </div>
  )
}

function Label({ children }: { children: ReactNode }) {
  return <div className="mb-0.5 text-[10.5px] font-semibold uppercase tracking-wider text-slate-400">{children}</div>
}

export function CasesHeader({ right }: { right?: ReactNode }) {
  return (
    <header className="border-b border-line bg-surface">
      <div className="mx-auto flex max-w-[1280px] items-center justify-between gap-4 px-4 py-3 sm:px-8">
        <div className="flex items-center gap-2.5">
          <img src="/logo.png" alt="" width={36} height={36} className="h-9 w-9" />
          <div className="leading-tight">
            <div className="text-[15px] font-semibold tracking-tight text-slate-900">Red Duck Lawyer</div>
            <div className="text-[11.5px] text-slate-500">Case briefs from Clio</div>
          </div>
        </div>
        {right}
      </div>
    </header>
  )
}

export function CasesPage({ rows, onOpen }: { rows: CaseRow[]; onOpen: (id: string) => void }) {
  const real = rows.filter(r => !r.sample)
  const attention = real.filter(r => r.attention_reasons.length > 0).length
  const samples = rows.length - real.length
  return (
    <div className="min-h-screen bg-page text-slate-900">
      <Fonts />
      <CasesHeader />
      <main className="mx-auto max-w-[1280px] px-4 py-6 sm:px-8">
        <div className="mb-4 flex flex-wrap items-end justify-between gap-2">
          <div>
            <h1 className="text-[22px] font-semibold tracking-tight">Cases</h1>
            <p className="text-[13px] text-slate-500">
              {real.length} matter{real.length === 1 ? '' : 's'} from Clio · {attention} need{attention === 1 ? 's' : ''} attention · sorted by what needs you first
            </p>
          </div>
          {samples > 0 && (
            <p className="text-[12px] text-slate-400">{samples} sample row{samples === 1 ? '' : 's'} shown for layout only; not real matters.</p>
          )}
        </div>
        {rows.length ? (
          <div className="space-y-3">{rows.map(r => <Row key={r.id} r={r} onOpen={onOpen} />)}</div>
        ) : (
          <div className="rounded-xl border border-line bg-surface px-4 py-10 text-center text-[13.5px] text-slate-500">
            No matters synced yet. Sync a matter from Clio to see it here.
          </div>
        )}
      </main>
    </div>
  )
}
