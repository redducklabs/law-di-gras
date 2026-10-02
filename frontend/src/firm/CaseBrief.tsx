// Firm Case Brief: one screen answering "where does this case stand, and what do I do next".
import { useState, type FormEvent } from 'react'
import { Link } from 'react-router-dom'
import { Account } from '../cases/Account'
import type { Citation, Dashboard, Fact } from '../api/types'
import {
  Avatar, Badge, Card, Fonts, SourceChips, Tile, daysFromToday, fmtDate, fmtDateTime, money, relDays,
} from '../components'
import { StageStepper } from './CaseProgress'
import { TimelineStrip } from './Timeline'
import { NextSteps } from './NextSteps'
import { BlindSpots, useReview } from '../review'

export interface CaseBriefProps {
  data: Dashboard
  onOpenSource?: (c: Citation) => void
  onShare?: () => void
  onSearch?: (q: string) => void
  onRefresh?: () => void
  /** Zoom the timeline to this date and pulse the nearest event (chat deeplinks). */
  focusDate?: string | null
}

export function CaseBrief({ data: d, onOpenSource, onShare, onSearch, onRefresh, focusDate }: CaseBriefProps) {
  const contactAge = daysFromToday(d.last_client_contact?.date)
  const review = useReview(d.matter.id)
  const billedTotal = d.treatment.reduce((s, t) => s + (t.billed?.amount ?? 0), 0)

  return (
    <div className="min-h-screen bg-page text-slate-900">
      <Fonts />
      <div className="mx-auto max-w-[1280px] px-4 py-5 sm:px-8 sm:py-6">
        <nav className="mb-3 flex items-center justify-between">
          <Link to="/cases" className="inline-flex items-center gap-1.5 rounded-md px-1.5 py-1 -ml-1.5 text-[12.5px] font-medium text-brand-700 hover:bg-brand-50">
            <img src="/logo.png" alt="" width={18} height={18} className="h-[18px] w-[18px]" />← Cases
          </Link>
          <Account />
        </nav>
        {/* Header */}
        <header className="mb-5 flex flex-wrap items-center justify-between gap-4">
          <div className="flex min-w-0 items-center gap-3.5">
            <Avatar name={d.matter.client_name} src={d.matter.client_photo_url} />
            <div className="min-w-0">
              <div className="flex flex-wrap items-center gap-2">
                <h1 className="truncate text-[22px] font-semibold tracking-tight">{d.matter.client_name}</h1>
                <Badge tone="brand">{d.headline.stage}</Badge>
              </div>
              <div className="truncate text-[13px] text-slate-500">
                {d.matter.title} · {d.matter.display_number}
                {d.matter.opened_date && <> · opened {fmtDate(d.matter.opened_date, true)}</>}
              </div>
            </div>
          </div>
          <div className="flex w-full items-center gap-2 sm:w-auto">
            {onSearch && <SearchBox onSearch={onSearch} />}
            <button type="button" onClick={onShare}
              className="shrink-0 cursor-pointer rounded-lg bg-brand-700 px-4 py-2 text-[13px] font-semibold text-white shadow-sm hover:bg-brand-800">
              Share with provider
            </button>
          </div>
        </header>

        {/* Timeline first: lawyers read the case through it. Section ids match PageSection (chat deeplinks). */}
        <section id="timeline" className="scroll-mt-4">
          <Card className="p-5 sm:p-6" pad={false}>
            <StageStepper stage={d.headline.stage} />
            <TimelineStrip events={d.timeline} onOpenSource={onOpenSource} zoomUi="direct" lanes focusDate={focusDate} />
          </Card>
        </section>

        <div className="mt-5 grid grid-cols-1 gap-5 lg:grid-cols-12">
          <section id="next-steps" className="scroll-mt-4 lg:col-span-7">
            <NextSteps data={d} onOpenSource={onOpenSource} />
          </section>
          <section id="status" className="scroll-mt-4 lg:col-span-5">
            <Card className="h-full" title="Where the case stands">
              <p className="text-[17px] font-medium leading-snug text-slate-900">{d.headline.status_line}</p>
              {!!d.headline.status_citations?.length && (
                <div className="mt-1.5"><SourceChips citations={d.headline.status_citations} onOpen={onOpenSource} max={2} /></div>
              )}
              <ul className="mt-4 space-y-3">
                {d.headline.bullets.map(b => (
                  <li key={b.id} className="flex gap-3 text-[13.5px] leading-relaxed text-slate-700">
                    <span className={`mt-[7px] h-1.5 w-1.5 shrink-0 rounded-full ${b.verified ? 'bg-brand-500' : 'bg-warn-600'}`} />
                    <span>
                      {b.label.length <= 40 && <span className="font-semibold text-slate-900">{b.label}. </span>}{b.value}{' '}
                      <SourceChips citations={b.citations} onOpen={onOpenSource} max={2} />
                    </span>
                  </li>
                ))}
              </ul>
              {d.last_client_contact && (
                <div className={`mt-5 flex flex-wrap items-center gap-2 rounded-lg px-3 py-2 text-[12.5px] ${contactAge != null && contactAge <= -30 ? 'bg-warn-50 text-warn-700' : 'bg-page text-slate-600'}`}>
                  <span className="font-semibold">Last client contact</span>
                  <span>{d.last_client_contact.value}{contactAge != null && ` · ${relDays(contactAge)}`}</span>
                  <SourceChips citations={d.last_client_contact.citations} onOpen={onOpenSource} max={1} />
                </div>
              )}
              {d.recent.length > 0 && <RecentActivity items={d.recent} onOpenSource={onOpenSource} />}
            </Card>
          </section>
        </div>

        {/* Blind spots: S7's whole-case review, under Next steps. */}
        <section id="blind-spots" className="mt-5 scroll-mt-4">
          <BlindSpots review={review.review} loading={review.loading} onRun={review.run} onOpenSource={onOpenSource} />
        </section>

        {/* Money: compact here; the Cases page carries these across matters. */}
        <section id="kpis" className="mt-5 grid scroll-mt-4 grid-cols-2 gap-3 lg:grid-cols-4">
          {d.kpis.case_value
            ? <Tile compact fact={d.kpis.case_value} tone="warn" onOpen={onOpenSource} sub="Draft range · attorney review" />
            : <Tile compact label="Case value (draft)" tone="warn" />}
          {d.kpis.coverage.length
            ? <Tile compact fact={d.kpis.coverage[0]} tone="brand" onOpen={onOpenSource}
                sub={d.kpis.coverage.length > 1 ? `+${d.kpis.coverage.length - 1} more polic${d.kpis.coverage.length > 2 ? 'ies' : 'y'}` : undefined} />
            : <Tile compact label="Coverage / policy limits" tone="brand" />}
          <Tile compact fact={d.kpis.specials} label="Medical specials" tone="ok" onOpen={onOpenSource} sub={liensSub(d.kpis.liens)} />
          <Tile compact fact={d.kpis.firm_spent} label="Firm costs advanced" tone="neutral" onOpen={onOpenSource} />
        </section>

        {/* Detail */}
        <div className="mt-5 grid grid-cols-1 gap-5 lg:grid-cols-12">
          <section id="injuries" className="scroll-mt-4 lg:col-span-5"><Card className="h-full" title="Injuries" extra={<span className="text-[12px] text-slate-400">{d.injuries.length} documented</span>}>
            {d.injuries.length ? (
              <ul className="grid grid-cols-1 gap-2 sm:grid-cols-2">
                {d.injuries.map(f => (
                  <li key={f.id} className={`rounded-lg border px-3 py-2.5 ${f.verified ? 'border-line' : 'border-dashed border-warn-600/70'}`}>
                    <div className="text-[11px] font-medium uppercase tracking-wide text-slate-400">{f.label}</div>
                    <div className="text-[13.5px] font-medium">{f.value}</div>
                    <div className="mt-1.5"><SourceChips citations={f.citations} onOpen={onOpenSource} max={2} /></div>
                  </li>
                ))}
              </ul>
            ) : <Empty>No injuries found in the record yet.</Empty>}
          </Card></section>
          <section id="treatment" className="scroll-mt-4 lg:col-span-7"><Card className="h-full" title="Treatment by provider"
            extra={billedTotal > 0 && <span className="text-[12px] text-slate-500">Billed to date <b className="text-slate-900">{money(billedTotal)}</b></span>}>
            {d.treatment.length ? (
              <ul>
                {d.treatment.map((t, i) => {
                  const share = billedTotal && t.billed?.amount ? (t.billed.amount / billedTotal) * 100 : 0
                  return (
                    <li key={i} className="border-t border-line-soft py-2.5 first:border-0 first:pt-0">
                      <div className="flex items-start justify-between gap-3">
                        <div className="min-w-0">
                          <div className="text-[13.5px] font-medium">{t.provider}</div>
                          <div className="text-[12px] text-slate-500">
                            {t.visit_count != null && <>{t.visit_count} visit{t.visit_count === 1 ? '' : 's'} billed · </>}
                            {t.first_visit && <>first {fmtDate(t.first_visit, true)}</>}
                            {/* last_visit is usually a billing service-through date, not the last appointment. */}
                            {t.last_visit && <> · {t.last_visit_basis === 'records' ? 'last visit' : 'billed through'} {fmtDate(t.last_visit, true)}</>}
                            {t.next_visit && <span className="text-ok-700"> · next visit {fmtDate(t.next_visit, true)}</span>}
                          </div>
                        </div>
                        <div className="min-w-0 max-w-[55%] shrink-0 text-right">
                          {t.billed
                            ? <div className={`text-[14px] font-semibold tabular-nums ${t.billed.verified ? '' : 'text-warn-700'}`}>{t.billed.value}</div>
                            : <div className="text-[12px] text-slate-400">Bill not in file</div>}
                          <div className="mt-0.5"><SourceChips citations={t.billed?.citations ?? t.citations} onOpen={onOpenSource} max={1} /></div>
                        </div>
                      </div>
                      {share > 0 && <div className="mt-1.5 h-1 rounded-full bg-line-soft"><div className="h-1 rounded-full bg-ok-600/60" style={{ width: `${share}%` }} /></div>}
                    </li>
                  )
                })}
              </ul>
            ) : <Empty>No treatment found in the record yet.</Empty>}
          </Card></section>
        </div>

        <footer className="mt-6 flex flex-wrap items-center justify-center gap-x-2 gap-y-1 text-center text-[11.5px] text-slate-400">
          <span className="font-semibold text-slate-500">Draft for attorney review</span>
          <span>· generated {fmtDateTime(d.generated_at)}</span>
          <span>· ${d.cost_usd.toFixed(2)}</span>
          <span>· every fact links to its source; <span className="text-warn-700">amber</span> = not verified verbatim</span>
          {onRefresh && <button type="button" onClick={onRefresh} className="cursor-pointer text-brand-700 hover:underline">· re-digest</button>}
        </footer>
      </div>
    </div>
  )
}

const RECENT_VISIBLE = 4

function RecentActivity({ items, onOpenSource }: { items: Fact[]; onOpenSource?: (c: Citation) => void }) {
  const [all, setAll] = useState(false)
  const shown = all ? items : items.slice(0, RECENT_VISIBLE)
  return (
    <div id="recent" className="mt-5 scroll-mt-4 border-t border-line-soft pt-4">
      <div className="mb-2 flex items-baseline justify-between">
        <h3 className="text-[11px] font-semibold uppercase tracking-wider text-slate-400">Recent activity</h3>
        {items.length > RECENT_VISIBLE && (
          <button type="button" onClick={() => setAll(v => !v)} className="cursor-pointer text-[12px] font-semibold text-brand-700 hover:underline">
            {all ? 'Show fewer' : `All ${items.length}`}
          </button>
        )}
      </div>
      <ul>
        {shown.map(f => (
          <li key={f.id} className="flex gap-3 py-1.5 text-[13px]">
            <span className="w-12 shrink-0 pt-px text-[12px] tabular-nums text-slate-400">{fmtDate(f.date)}</span>
            <span className="min-w-0 flex-1">
              <span className={f.verified ? 'text-slate-800' : 'text-warn-700'} title={f.value}>{f.label}</span>{' '}
              <SourceChips citations={f.citations} onOpen={onOpenSource} max={1} />
            </span>
          </li>
        ))}
      </ul>
    </div>
  )
}

function liensSub(liens?: Fact[]) {
  if (!liens?.length) return undefined
  const total = liens.reduce((s, f) => s + (f.amount ?? 0), 0)
  return `${liens.length} lien${liens.length === 1 ? '' : 's'}${total ? ` · ${money(total)}` : ''}`
}

function SearchBox({ onSearch }: { onSearch: (q: string) => void }) {
  const [q, setQ] = useState('')
  const submit = (e: FormEvent) => { e.preventDefault(); if (q.trim()) onSearch(q.trim()) }
  return (
    <form onSubmit={submit} className="relative min-w-0 flex-1 sm:w-64 sm:flex-none">
      <svg className="pointer-events-none absolute left-2.5 top-1/2 -translate-y-1/2 text-slate-400" width="14" height="14" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.8"><circle cx="7" cy="7" r="4.5" /><path d="M10.5 10.5L14 14" /></svg>
      <input value={q} onChange={e => setQ(e.target.value)} placeholder="Find in case…"
        className="w-full rounded-lg border border-line bg-surface py-2 pl-8 pr-3 text-[13px] outline-none placeholder:text-slate-400 focus:border-brand-500 focus:ring-2 focus:ring-brand-500/15" />
    </form>
  )
}

function Empty({ children }: { children: React.ReactNode }) {
  return <div className="rounded-lg bg-page px-4 py-6 text-center text-[13px] text-slate-400">{children}</div>
}
