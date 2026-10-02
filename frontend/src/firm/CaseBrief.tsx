// Firm Case Brief: one screen answering "where does this case stand, and what do I do next".
// Calm by default: status, numbers, timeline, the few actions; detail opens on demand.
import { useState, type FormEvent } from 'react'
import { Link } from 'react-router-dom'
import { Account } from '../cases/Account'
import type { Citation, Dashboard, Fact } from '../api/types'
import {
  Avatar, Card, Disclosure, Fonts, SourceChips, daysFromToday, fmtDate, fmtDateTime, money, relDays, useReveal,
} from '../components'
import { StageStepper } from './CaseProgress'
import { TimelineStrip } from './Timeline'
import { NextSteps } from './NextSteps'
import { KpiStrip } from './KpiStrip'
import { AuditBadge, FlagCount, FlagDot, indexAudit, useAudit, type AuditIndex } from './audit'
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
  const audit = useAudit(d.matter.id)
  const ax = indexAudit(audit)
  const billedTotal = d.treatment.reduce((s, t) => s + (t.billed?.amount ?? 0), 0)
  const nextVisit = d.treatment.map(t => t.next_visit).filter((v): v is string => !!v).sort()[0]

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

        {/* Header: who, matter, last contact. Stage lives on the stepper below. */}
        <header className="mb-4 flex flex-wrap items-start justify-between gap-4">
          <div className="flex min-w-0 flex-1 items-center gap-3.5">
            <Avatar name={d.matter.client_name} src={d.matter.client_photo_url} />
            <div className="min-w-0">
              <h1 className="truncate text-[22px] font-semibold tracking-tight">{d.matter.client_name}</h1>
              <div className="flex flex-wrap items-center gap-x-1.5 text-[13px] text-slate-500">
                <span className="truncate">{d.matter.title} · {d.matter.display_number}</span>
                {d.last_client_contact && (
                  <span className={`inline-flex items-center gap-1.5 ${contactAge != null && contactAge <= -30 ? 'font-medium text-warn-700' : ''}`}>
                    · Last client contact {contactAge != null ? relDays(contactAge) : d.last_client_contact.value}
                    <SourceChips citations={d.last_client_contact.citations} onOpen={onOpenSource} max={1} compact />
                    <FlagDot flags={ax.item(d.last_client_contact.id)} />
                  </span>
                )}
              </div>
            </div>
          </div>
          <div className="flex w-full items-center gap-2 sm:w-auto">
            <AuditBadge report={audit} />
            {onSearch && <SearchBox onSearch={onSearch} />}
            <button type="button" onClick={onShare}
              className="shrink-0 cursor-pointer rounded-lg bg-brand-700 px-4 py-2 text-[13px] font-semibold text-white shadow-sm hover:bg-brand-800">
              Share with provider
            </button>
          </div>
        </header>

        {/* The one headline sentence. */}
        <p className="mb-4 max-w-[64rem] text-[18px] font-medium leading-snug text-slate-900">
          {d.headline.status_line}{' '}
          {!!d.headline.status_citations?.length && <SourceChips citations={d.headline.status_citations} onOpen={onOpenSource} max={2} compact />}{' '}
          <FlagDot flags={ax.item('status_line')} />
        </p>

        {/* Section ids match PageSection (chat deeplinks). */}
        <section id="timeline" className="scroll-mt-4">
          <Card className="p-5 sm:p-6" pad={false}>
            <StageStepper stage={d.headline.stage} />
            <TimelineStrip events={d.timeline} onOpenSource={onOpenSource} zoomUi="direct" lanes focusDate={focusDate} />
          </Card>
        </section>

        {/* Blind spots: S7's whole-case review, a thin expandable bar under the timeline. */}
        <section id="blind-spots" className="mt-4 scroll-mt-4">
          <BlindSpots review={review.review} loading={review.loading} onRun={review.run} onOpenSource={onOpenSource} collapsible />
        </section>

        <div className="mt-4 grid grid-cols-1 gap-4 lg:grid-cols-12">
          <section id="next-steps" className="scroll-mt-4 lg:col-span-7">
            <NextSteps data={d} onOpenSource={onOpenSource} flagsFor={title => ax.item(`action:${title}`)} />
          </section>
          <section id="status" className="scroll-mt-4 lg:col-span-5">
            <KeyFacts bullets={d.headline.bullets} onOpenSource={onOpenSource} ax={ax} />
          </section>
        </div>

        {/* Detail on demand: one card, three collapsed rows. Deeplinks open them. */}
        <div className="mt-4 overflow-hidden rounded-xl border border-line bg-surface shadow-card">
          <Disclosure id="kpis" title="Money" summary={moneySummary(d)}
            extra={<Markers facts={[d.kpis.case_value, d.kpis.specials, d.kpis.firm_spent, ...d.kpis.coverage, ...(d.kpis.liens ?? [])].filter((f): f is Fact => !!f)} section="kpis" ax={ax} />}>
            <KpiStrip data={d} onOpenSource={onOpenSource} ax={ax} />
          </Disclosure>
          <Disclosure id="injuries" title="Injuries" extra={<Markers facts={d.injuries} section="injuries" ax={ax} />}
            summary={d.injuries.length ? `${d.injuries.length} documented · ${d.injuries.map(f => f.label).join(', ')}` : 'None found in the record yet'}>
            {d.injuries.length ? (
              <ul className="grid grid-cols-1 gap-2 sm:grid-cols-2 lg:grid-cols-3">
                {d.injuries.map(f => (
                  <li key={f.id} className={`rounded-lg border px-3 py-2.5 ${f.verified ? 'border-line' : 'border-dashed border-warn-600/70'}`}>
                    <div className="flex items-center justify-between gap-2 text-[11px] font-medium uppercase tracking-wide text-slate-400">{f.label}<FlagDot flags={ax.item(f.id)} /></div>
                    <div className={`text-[13.5px] font-medium ${f.verified ? '' : 'text-warn-700'}`}>{f.value}</div>
                    <div className="mt-1.5"><SourceChips citations={f.citations} onOpen={onOpenSource} max={2} compact /></div>
                  </li>
                ))}
              </ul>
            ) : <Empty>No injuries found in the record yet.</Empty>}
          </Disclosure>

          <Disclosure id="treatment" title="Treatment" extra={<Markers facts={d.treatment.flatMap(t => (t.billed ? [t.billed] : []))} section="treatment" ax={ax} ids={d.treatment.map(t => `treatment:${t.provider}`)} />}
            summary={d.treatment.length
              ? <>{d.treatment.length} provider{d.treatment.length === 1 ? '' : 's'}{billedTotal > 0 && <> · {money(billedTotal)} billed</>}{nextVisit && <> · next visit {fmtDate(nextVisit, true)}</>}</>
              : 'None found in the record yet'}>
            {d.treatment.length ? (
              <ul>
                {d.treatment.map((t, i) => {
                  const share = billedTotal && t.billed?.amount ? (t.billed.amount / billedTotal) * 100 : 0
                  return (
                    <li key={i} className="border-t border-line-soft py-2.5 first:border-0 first:pt-0">
                      <div className="flex items-start justify-between gap-3">
                        <div className="min-w-0">
                          <div className="flex items-center gap-2 text-[13.5px] font-medium">{t.provider}<FlagDot flags={[...ax.item(`treatment:${t.provider}`), ...(t.billed ? ax.item(t.billed.id) : [])]} /></div>
                          <div className="text-[12px] text-slate-500">
                            {t.visit_count != null && <>{t.visit_count} visit{t.visit_count === 1 ? '' : 's'} billed · </>}
                            {t.first_visit && <>first {fmtDate(t.first_visit, true)}</>}
                            {/* last_visit is usually a billing service-through date, not the last appointment. */}
                            {t.last_visit && <> · {t.last_visit_basis === 'records' ? 'last visit' : 'billed through'} {fmtDate(t.last_visit, true)}</>}
                            {t.next_visit && <span className="text-ok-700"> · next visit {fmtDate(t.next_visit, true)}</span>}
                          </div>
                        </div>
                        <div className="flex min-w-0 max-w-[55%] shrink-0 items-center gap-2">
                          <SourceChips citations={t.billed?.citations ?? t.citations} onOpen={onOpenSource} max={1} compact />
                          {t.billed
                            ? <div className={`text-[14px] font-semibold tabular-nums ${t.billed.verified ? '' : 'text-warn-700'}`}>{t.billed.value}</div>
                            : <div className="text-[12px] text-slate-400">Bill not in file</div>}
                        </div>
                      </div>
                      {share > 0 && <div className="mt-1.5 h-1 rounded-full bg-line-soft"><div className="h-1 rounded-full bg-slate-300" style={{ width: `${share}%` }} /></div>}
                    </li>
                  )
                })}
              </ul>
            ) : <Empty>No treatment found in the record yet.</Empty>}
          </Disclosure>

          <Disclosure id="recent" title="Recent activity" extra={<Markers facts={d.recent} section="recent" ax={ax} />}
            summary={d.recent[0] ? `${d.recent.length} items · latest ${fmtDate(d.recent[0].date)}: ${d.recent[0].label}` : 'Nothing recent in the record'}>
            <ul>
              {d.recent.map(f => (
                <li key={f.id} className="flex gap-3 py-1.5 text-[13px]">
                  <span className="w-12 shrink-0 pt-px text-[12px] tabular-nums text-slate-400">{fmtDate(f.date)}</span>
                  <span className="min-w-0 flex-1">
                    <span className={f.verified ? 'text-slate-800' : 'text-warn-700'} title={f.value}>{f.label}</span>{' '}
                    <SourceChips citations={f.citations} onOpen={onOpenSource} max={1} compact /> <FlagDot flags={ax.item(f.id)} />
                  </span>
                </li>
              ))}
            </ul>
          </Disclosure>
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

/** One line for the collapsed Money row: short amounts, not the full fact text. */
function moneySummary(d: Dashboard) {
  const k = d.kpis
  const amt = (f?: Fact | null) => f ? (f.amount != null ? money(f.amount) : f.value.split(/\s(?:billed|across)\s/)[0]) : null
  const parts = [
    k.case_value && `Draft value ${k.case_value.value}`,
    amt(k.specials) && `specials ${amt(k.specials)}`,
    k.liens?.length && `${k.liens.length} lien${k.liens.length === 1 ? '' : 's'}`,
    amt(k.firm_spent) && `costs ${amt(k.firm_spent)}`,
    k.coverage.length && `${k.coverage.length} coverage source${k.coverage.length === 1 ? '' : 's'}`,
  ].filter(Boolean)
  return parts.length ? parts.join(' · ') : 'No amounts found in the record yet'
}

const FACTS_VISIBLE = 3

/** Headline bullets: the first three, the rest on demand. A "status" deeplink opens all. */
function KeyFacts({ bullets, onOpenSource, ax }: { bullets: Fact[]; onOpenSource?: (c: Citation) => void; ax: AuditIndex }) {
  const [all, setAll] = useState(false)
  useReveal('status', () => setAll(true))
  const shown = all ? bullets : bullets.slice(0, FACTS_VISIBLE)
  return (
    <Card className="h-full" title="Key facts">
      {bullets.length ? (
        <ul className="space-y-3">
          {shown.map(b => (
            <li key={b.id} className="flex gap-3 text-[13.5px] leading-relaxed text-slate-700">
              <span className={`mt-[7px] h-1.5 w-1.5 shrink-0 rounded-full ${b.verified ? 'bg-slate-300' : 'bg-warn-600'}`} />
              <span className={b.verified ? '' : 'text-warn-700'}>
                {b.label.length <= 40 && <span className="font-semibold text-slate-900">{b.label}. </span>}{b.value}{' '}
                <SourceChips citations={b.citations} onOpen={onOpenSource} max={2} compact /> <FlagDot flags={ax.item(b.id)} />
              </span>
            </li>
          ))}
        </ul>
      ) : <Empty>No key facts digested yet.</Empty>}
      {bullets.length > FACTS_VISIBLE && (
        <button type="button" onClick={() => setAll(v => !v)} className="mt-3 cursor-pointer px-1 text-[12px] font-semibold text-brand-700 hover:underline">
          {all ? 'Show fewer' : `${bullets.length - FACTS_VISIBLE} more`}
          {!all && <> <FlagCount flags={bullets.slice(FACTS_VISIBLE).flatMap(b => ax.item(b.id))} /></>}
        </button>
      )}
    </Card>
  )
}

/** Collapsed rows still say what inside is unverified or flagged by the audit. */
function Markers({ facts, section, ax, ids = [] }: { facts: Fact[]; section: string; ax: AuditIndex; ids?: string[] }) {
  return (
    <span className="inline-flex items-center gap-1.5">
      <Unverified facts={facts} />
      <FlagCount flags={ax.section(section, [...facts.map(f => f.id), ...ids])} />
    </span>
  )
}

/** Collapsed rows still say when something inside is not verified. */
function Unverified({ facts }: { facts: Fact[] }) {
  const n = facts.filter(f => !f.verified || f.citations.some(c => !c.verified)).length
  return n ? <span className="rounded-full border border-dashed border-warn-600 bg-warn-50 px-2 py-0.5 text-[11px] font-semibold text-warn-700">{n} unverified</span> : null
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
