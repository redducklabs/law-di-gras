// Throwaway: three visual directions for the Case Brief, on the fictional fixture.
// Open /src/dev/directions.html?d=a|b|c. Deleted with src/dev/.
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import '../index.css'
import type { ActionItem, Citation, Dashboard, Fact, TimelineEvent } from '../api/types'
import { fixture } from './fixture'

const d: Dashboard = fixture
const TODAY = new Date()
const DAY = 86_400_000

const fmt = (iso?: string | null, opts: Intl.DateTimeFormatOptions = { month: 'short', day: 'numeric' }) =>
  iso ? new Date(iso + (iso.length === 10 ? 'T12:00:00' : '')).toLocaleDateString('en-US', opts) : '—'
const fmtY = (iso?: string | null) => fmt(iso, { month: 'short', day: 'numeric', year: 'numeric' })
const initials = (n: string) => n.split(/\s+/).map(p => p[0]).slice(0, 2).join('').toUpperCase()
const chipText = (c: Citation) => (c.page ? `${c.source_title} · p.${c.page}` : c.source_title)

// Timeline scale: events far beyond today get pinned at the right edge as "off-scale".
function scale(events: TimelineEvent[]) {
  const t = (e: TimelineEvent) => new Date(e.date + 'T12:00:00').getTime()
  const horizon = TODAY.getTime() + 120 * DAY
  const inScale = events.filter(e => t(e) <= horizon)
  const off = events.filter(e => t(e) > horizon)
  const min = Math.min(...inScale.map(t))
  const max = Math.max(horizon - 60 * DAY, ...inScale.map(t))
  const pos = (ms: number) => ((ms - min) / (max - min)) * 100
  // Greedy row packing so clustered labels never overlap (labels start at their dot).
  const rowEnd: number[] = []
  const placed = inScale.map(e => {
    const x = pos(t(e))
    const w = ((e.label.length + 8) * 6.4 * 100) / 1100
    let row = rowEnd.findIndex(end => end < x)
    if (row === -1) row = rowEnd.length
    rowEnd[row] = x + w
    return { e, x, row }
  })
  return { inScale: placed, rows: rowEnd.length, off, todayX: pos(TODAY.getTime()) }
}

const STAGES = ['Intake', 'Treating', 'Pre-demand', 'Demand', 'Negotiation', 'Litigation', 'Resolved']

/* ───────────────────────────── A · LEDGER ───────────────────────────── */
// Editorial, paper-and-ink. Serif headline, hairline rules, no boxes, tables.

function ChipA({ c }: { c: Citation }) {
  return c.verified ? (
    <button className="inline-flex items-center gap-1 rounded-sm border border-[#d9d3c7] bg-white px-1.5 py-0.5 text-[11px] text-[#2b4a6f] hover:border-[#2b4a6f]">
      <span className="text-[#8a8478]">§</span>{chipText(c)}
    </button>
  ) : (
    <button className="inline-flex items-center gap-1 rounded-sm border border-dashed border-[#c08a2b] bg-[#fdf6e7] px-1.5 py-0.5 text-[11px] text-[#8a5a12]">
      {chipText(c)} <span className="font-semibold uppercase tracking-wide text-[9px]">unverified</span>
    </button>
  )
}

function TimelineA() {
  const { inScale, rows, off, todayX } = scale(d.timeline)
  return (
    <div className="relative mt-6 mb-2" style={{ height: 34 + rows * 16 }}>
      <div className="absolute left-0 right-28 top-5 h-px bg-[#1c2430]/25" />
      <div className="absolute left-0 right-28 top-0 h-full">
        {inScale.map(({ e, x, row }, i) => (
          <div key={i} className="absolute" style={{ left: `${x}%`, top: 15 }}>
            <div className={`-ml-[5px] h-[11px] w-[11px] rounded-full border ${e.is_future ? 'border-[#1c2430]/50 bg-[#faf8f4]' : e.kind === 'incident' ? 'border-[#8a2b2b] bg-[#8a2b2b]' : 'border-[#1c2430] bg-[#1c2430]'}`} />
            {row > 0 && <div className="absolute left-0 top-[11px] w-px bg-[#1c2430]/15" style={{ height: row * 16 + 4 }} />}
            <div className={`absolute left-0 whitespace-nowrap pl-1 text-[11px] ${e.is_future ? 'text-[#6b675f] italic' : 'text-[#1c2430]'}`} style={{ top: 14 + row * 16 }}>
              {e.label} <span className="text-[#8a8478]">{fmt(e.date)}</span>
            </div>
          </div>
        ))}
        <div className="absolute top-0 bottom-3 w-px bg-[#8a2b2b]" style={{ left: `${todayX}%` }}>
          <span className="absolute -top-1 left-1.5 text-[10px] font-semibold uppercase tracking-widest text-[#8a2b2b]">Today</span>
        </div>
      </div>
      <div className="absolute right-0 top-2.5 w-24 text-right text-[11px] text-[#6b675f]">
        {off.map((e, i) => <div key={i}>{e.label} <span className="font-medium text-[#1c2430]">{fmtY(e.date)}</span> →</div>)}
      </div>
    </div>
  )
}

const statusA: Record<ActionItem['status'], string> = { overdue: 'text-[#8a2b2b]', upcoming: 'text-[#1c2430]', waiting: 'text-[#6b675f]' }

function DirectionA() {
  return (
    <div className="min-h-screen bg-[#faf8f4] text-[#1c2430]" style={{ fontFamily: 'Inter, sans-serif' }}>
      <div className="mx-auto max-w-[1280px] px-10 py-8">
        <header className="flex items-end justify-between border-b-2 border-[#1c2430] pb-4">
          <div className="flex items-center gap-4">
            <div className="grid h-12 w-12 place-items-center rounded-full bg-[#1c2430] text-sm font-semibold text-[#faf8f4]">{initials(d.matter.client_name)}</div>
            <div>
              <div className="text-[11px] uppercase tracking-[0.18em] text-[#6b675f]">Case Brief · {d.matter.display_number}</div>
              <h1 className="text-[30px] leading-tight" style={{ fontFamily: 'Newsreader, serif' }}>{d.matter.title}</h1>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <span className="border border-[#1c2430] px-2.5 py-1 text-[11px] font-semibold uppercase tracking-[0.14em]">{d.headline.stage}</span>
            <button className="bg-[#1c2430] px-4 py-2 text-sm font-medium text-[#faf8f4]">Share with provider</button>
          </div>
        </header>

        <TimelineA />

        <section className="mt-6 grid grid-cols-12 gap-10 border-t border-[#1c2430]/15 pt-6">
          <div className="col-span-8">
            <p className="text-[26px] leading-[1.3]" style={{ fontFamily: 'Newsreader, serif' }}>{d.headline.status_line}</p>
            <ul className="mt-5 space-y-3">
              {d.headline.bullets.map(b => (
                <li key={b.id} className="grid grid-cols-[110px_1fr] gap-3 text-[14px] leading-relaxed">
                  <span className="pt-px text-[11px] font-semibold uppercase tracking-[0.12em] text-[#6b675f]">{b.label}</span>
                  <span>{b.value} {b.citations.map((c, i) => <ChipA key={i} c={c} />)}</span>
                </li>
              ))}
            </ul>
          </div>
          <div className="col-span-4 border-l border-[#1c2430]/15 pl-8">
            {[d.kpis.specials, ...d.kpis.coverage, d.kpis.firm_spent, d.kpis.case_value].filter(Boolean).map(k => (
              <div key={k!.id} className="flex items-baseline justify-between border-b border-dotted border-[#1c2430]/25 py-2.5">
                <span className="text-[13px] text-[#4a4740]">{k!.label}</span>
                <span className={`text-[18px] tabular-nums ${k!.verified ? '' : 'text-[#8a5a12]'}`} style={{ fontFamily: 'Newsreader, serif' }}>
                  {k!.value}{!k!.verified && <sup className="ml-0.5 text-[10px]">†</sup>}
                </span>
              </div>
            ))}
            <p className="mt-2 text-[11px] text-[#8a8478]">† unverified against the record</p>
          </div>
        </section>

        <section className="mt-8 grid grid-cols-12 gap-10 border-t border-[#1c2430]/15 pt-6">
          <div className="col-span-7">
            <h2 className="mb-3 text-[11px] font-semibold uppercase tracking-[0.18em] text-[#6b675f]">Needs action</h2>
            <table className="w-full text-[14px]">
              <tbody>
                {d.actions.map((a, i) => (
                  <tr key={i} className="border-b border-[#1c2430]/10 align-top">
                    <td className={`w-24 py-2.5 text-[11px] font-semibold uppercase tracking-wider ${statusA[a.status]}`}>{a.status}</td>
                    <td className="py-2.5">{a.title}{a.waiting_on && <span className="text-[#6b675f]"> — on {a.waiting_on}</span>}<div className="mt-1">{a.citations.map((c, j) => <ChipA key={j} c={c} />)}</div></td>
                    <td className="w-20 py-2.5 text-right tabular-nums text-[#4a4740]">{fmt(a.due_date)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            <p className="mt-4 text-[13px] text-[#4a4740]">Last client contact: <span className="text-[#1c2430]">{d.last_client_contact?.value}</span> {d.last_client_contact?.citations.map((c, i) => <ChipA key={i} c={c} />)}</p>
          </div>
          <div className="col-span-5">
            <h2 className="mb-3 text-[11px] font-semibold uppercase tracking-[0.18em] text-[#6b675f]">Injuries</h2>
            {d.injuries.map(f => (
              <div key={f.id} className="flex items-baseline justify-between gap-3 border-b border-[#1c2430]/10 py-2 text-[14px]">
                <span>{f.value}</span><span className="shrink-0">{f.citations.map((c, i) => <ChipA key={i} c={c} />)}</span>
              </div>
            ))}
            <h2 className="mt-7 mb-3 text-[11px] font-semibold uppercase tracking-[0.18em] text-[#6b675f]">Treatment</h2>
            <table className="w-full text-[13px]">
              <thead><tr className="text-left text-[11px] text-[#8a8478]"><th className="font-normal">Provider</th><th className="font-normal">Visits</th><th className="font-normal">Dates</th><th className="text-right font-normal">Billed</th></tr></thead>
              <tbody>
                {d.treatment.map((t, i) => (
                  <tr key={i} className="border-b border-[#1c2430]/10">
                    <td className="py-2">{t.provider}</td><td className="tabular-nums">{t.visit_count}</td>
                    <td className="tabular-nums text-[#4a4740]">{fmt(t.first_visit)}–{fmt(t.last_visit)}</td>
                    <td className="text-right tabular-nums" style={{ fontFamily: 'Newsreader, serif' }}>{t.billed?.value ?? <span className="text-[#8a8478] italic">pending</span>}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
        <footer className="mt-10 border-t border-[#1c2430]/15 pt-3 text-[11px] text-[#8a8478]">Draft for attorney review · generated {fmtY(d.generated_at.slice(0, 10))} · ${d.cost_usd.toFixed(2)}</footer>
      </div>
    </div>
  )
}

/* ───────────────────────────── B · CONSOLE ───────────────────────────── */
// Dark, dense, data-terminal. Mono numerals, teal accent, timeline lanes by kind.

function ChipB({ c }: { c: Citation }) {
  return c.verified ? (
    <button className="inline-flex items-center gap-1 rounded border border-[#2a3441] bg-[#111820] px-1.5 py-0.5 font-mono text-[10.5px] text-[#5eead4] hover:border-[#5eead4]/60">
      ↗ {chipText(c)}
    </button>
  ) : (
    <button className="inline-flex items-center gap-1 rounded border border-dashed border-[#f59e0b]/70 bg-[#f59e0b]/10 px-1.5 py-0.5 font-mono text-[10.5px] text-[#fbbf24]">
      ⚠ {chipText(c)} · unverified
    </button>
  )
}

const laneColor: Record<TimelineEvent['kind'], string> = {
  incident: '#f87171', treatment: '#5eead4', legal: '#a78bfa', communication: '#94a3b8', deadline: '#fbbf24',
}

function TimelineB() {
  const { inScale, off, todayX } = scale(d.timeline)
  const lanes: TimelineEvent['kind'][] = ['incident', 'treatment', 'legal', 'communication', 'deadline']
  return (
    <div className="rounded-lg border border-[#1f2833] bg-[#0f151c] p-4">
      <div className="flex">
        <div className="w-24 shrink-0 space-y-[7px] pt-0.5 font-mono text-[10px] uppercase tracking-wider text-[#5b6776]">
          {lanes.map(l => <div key={l} className="h-3 leading-3">{l.slice(0, 5)}</div>)}
        </div>
        <div className="relative flex-1">
          {lanes.map((l, li) => <div key={l} className="absolute left-0 right-0 h-px bg-[#1f2833]" style={{ top: li * 19 + 6 }} />)}
          {inScale.map(({ e, x }, i) => (
            <div key={i} className="group absolute -translate-x-1/2" style={{ left: `${x}%`, top: lanes.indexOf(e.kind) * 19 }}>
              <div className={`h-3 w-3 rotate-45 ${e.is_future ? 'border' : ''}`} style={e.is_future ? { borderColor: laneColor[e.kind] } : { background: laneColor[e.kind] }} />
              {(i === 0 || inScale[i - 1].e.kind !== e.kind || x - inScale[i - 1].x > 6) && (
                <div className="absolute left-4 -top-0.5 whitespace-nowrap font-mono text-[10.5px] text-[#c9d1d9]">{e.label} <span className="text-[#5b6776]">{fmt(e.date)}</span></div>
              )}
            </div>
          ))}
          <div className="absolute -top-2 w-px bg-[#5eead4]" style={{ left: `${todayX}%`, height: 104 }}>
            <span className="absolute -top-0 left-1 font-mono text-[9px] font-semibold text-[#5eead4]">NOW</span>
          </div>
          <div className="h-[96px]" />
        </div>
        <div className="w-36 shrink-0 border-l border-[#1f2833] pl-3 font-mono text-[10.5px] text-[#8b949e]">
          <div className="mb-1 text-[9px] uppercase tracking-wider text-[#5b6776]">Off-scale</div>
          {off.map((e, i) => <div key={i}><span style={{ color: laneColor[e.kind] }}>◆</span> {e.label} {fmtY(e.date)}</div>)}
        </div>
      </div>
    </div>
  )
}

function TileB({ f, accent }: { f?: Fact | null; accent?: boolean }) {
  if (!f) return null
  return (
    <div className={`rounded-lg border p-4 ${accent ? 'border-[#5eead4]/40 bg-[#5eead4]/[0.06]' : 'border-[#1f2833] bg-[#0f151c]'}`}>
      <div className="font-mono text-[10px] uppercase tracking-wider text-[#5b6776]">{f.label}</div>
      <div className={`mt-1.5 font-mono text-[24px] font-semibold tabular-nums ${f.verified ? 'text-[#e6edf3]' : 'text-[#fbbf24]'}`}>{f.value}</div>
      <div className="mt-2 flex flex-wrap gap-1">{f.citations.slice(0, 2).map((c, i) => <ChipB key={i} c={c} />)}</div>
    </div>
  )
}

const statusB: Record<ActionItem['status'], string> = {
  overdue: 'bg-[#f87171]/15 text-[#f87171]', upcoming: 'bg-[#5eead4]/10 text-[#5eead4]', waiting: 'bg-[#94a3b8]/15 text-[#94a3b8]',
}

function DirectionB() {
  return (
    <div className="min-h-screen bg-[#0a0e13] text-[#c9d1d9]" style={{ fontFamily: '"IBM Plex Sans", sans-serif' }}>
      <div className="mx-auto max-w-[1360px] px-8 py-6">
        <header className="mb-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="grid h-10 w-10 place-items-center rounded-md bg-[#1f2833] font-mono text-sm font-semibold text-[#5eead4]">{initials(d.matter.client_name)}</div>
            <div>
              <h1 className="text-[18px] font-semibold text-[#e6edf3]">{d.matter.title}</h1>
              <div className="font-mono text-[11px] text-[#5b6776]">{d.matter.display_number} · opened {fmtY(d.matter.opened_date)} · {d.matter.status}</div>
            </div>
            <span className="ml-3 rounded bg-[#a78bfa]/15 px-2 py-0.5 font-mono text-[11px] font-semibold uppercase tracking-wider text-[#c4b5fd]">{d.headline.stage}</span>
          </div>
          <div className="flex items-center gap-2">
            <input placeholder="Find in case…  ⌘K" className="w-64 rounded-md border border-[#1f2833] bg-[#0f151c] px-3 py-1.5 font-mono text-[12px] placeholder:text-[#5b6776]" />
            <button className="rounded-md bg-[#5eead4] px-3.5 py-1.5 text-[13px] font-semibold text-[#0a0e13]">Share</button>
          </div>
        </header>

        <TimelineB />

        <div className="mt-4 grid grid-cols-12 gap-4">
          <section className="col-span-7 rounded-lg border border-[#1f2833] bg-[#0f151c] p-5">
            <div className="font-mono text-[10px] uppercase tracking-wider text-[#5b6776]">Status</div>
            <p className="mt-1.5 text-[19px] leading-snug text-[#e6edf3]">{d.headline.status_line}</p>
            <ul className="mt-4 space-y-2.5">
              {d.headline.bullets.map(b => (
                <li key={b.id} className="text-[13.5px] leading-relaxed">
                  <span className="mr-2 font-mono text-[10.5px] uppercase text-[#5b6776]">{b.label}</span>{b.value} <span className="inline-flex flex-wrap gap-1 align-middle">{b.citations.map((c, i) => <ChipB key={i} c={c} />)}</span>
                </li>
              ))}
            </ul>
          </section>
          <div className="col-span-5 grid grid-cols-2 gap-4">
            <TileB f={d.kpis.specials} accent />
            <TileB f={d.kpis.coverage[0]} />
            <TileB f={d.kpis.firm_spent} />
            <TileB f={d.kpis.case_value} />
          </div>

          <section className="col-span-5 rounded-lg border border-[#1f2833] bg-[#0f151c] p-5">
            <div className="mb-3 flex items-baseline justify-between">
              <span className="font-mono text-[10px] uppercase tracking-wider text-[#5b6776]">Needs action</span>
              <span className="font-mono text-[10.5px] text-[#8b949e]">last client contact {fmt(d.last_client_contact?.date)}</span>
            </div>
            {d.actions.map((a, i) => (
              <div key={i} className="flex items-start gap-3 border-t border-[#1f2833] py-2.5">
                <span className={`w-[68px] shrink-0 rounded px-1.5 py-0.5 text-center font-mono text-[10px] font-semibold uppercase ${statusB[a.status]}`}>{a.status}</span>
                <div className="flex-1 text-[13px]">{a.title}{a.waiting_on && <span className="text-[#8b949e]"> · {a.waiting_on}</span>}</div>
                <span className="font-mono text-[11px] tabular-nums text-[#8b949e]">{fmt(a.due_date)}</span>
              </div>
            ))}
          </section>
          <section className="col-span-3 rounded-lg border border-[#1f2833] bg-[#0f151c] p-5">
            <div className="mb-3 font-mono text-[10px] uppercase tracking-wider text-[#5b6776]">Injuries</div>
            {d.injuries.map(f => (
              <div key={f.id} className="border-t border-[#1f2833] py-2">
                <div className="text-[13px] text-[#e6edf3]">{f.value}</div>
                <div className="mt-1">{f.citations.map((c, i) => <ChipB key={i} c={c} />)}</div>
              </div>
            ))}
          </section>
          <section className="col-span-4 rounded-lg border border-[#1f2833] bg-[#0f151c] p-5">
            <div className="mb-3 font-mono text-[10px] uppercase tracking-wider text-[#5b6776]">Treatment</div>
            {d.treatment.map((t, i) => {
              const max = Math.max(...d.treatment.map(x => x.billed?.amount ?? 0))
              return (
                <div key={i} className="border-t border-[#1f2833] py-2">
                  <div className="flex justify-between text-[13px]"><span className="text-[#e6edf3]">{t.provider}</span><span className="font-mono tabular-nums">{t.billed?.value ?? <span className="text-[#5b6776]">—</span>}</span></div>
                  <div className="mt-1 h-1 rounded bg-[#1f2833]"><div className="h-1 rounded bg-[#5eead4]/70" style={{ width: `${((t.billed?.amount ?? 0) / max) * 100}%` }} /></div>
                  <div className="mt-1 font-mono text-[10.5px] text-[#5b6776]">{t.visit_count} visits · {fmt(t.first_visit)} → {fmt(t.last_visit)}</div>
                </div>
              )
            })}
          </section>
        </div>
        <footer className="mt-5 font-mono text-[10.5px] text-[#5b6776]">DRAFT FOR ATTORNEY REVIEW · generated {fmtY(d.generated_at.slice(0, 10))} · ${d.cost_usd.toFixed(2)} · {d.models.join(', ')}</footer>
      </div>
    </div>
  )
}

/* ───────────────────────────── C · CLINICAL ───────────────────────────── */
// Bright, calm, card-based. Stage stepper + timeline in one header card, big KPI tiles.

function ChipC({ c }: { c: Citation }) {
  return c.verified ? (
    <button className="inline-flex items-center gap-1 rounded-full bg-[#eef2ff] px-2 py-0.5 text-[11px] font-medium text-[#4338ca] hover:bg-[#e0e7ff]">
      <svg width="10" height="10" viewBox="0 0 16 16" fill="currentColor"><path d="M4 1h6l4 4v10H4z" opacity=".35" /><path d="M10 1v4h4" /></svg>{chipText(c)}
    </button>
  ) : (
    <button className="inline-flex items-center gap-1 rounded-full border border-dashed border-[#d97706] bg-[#fffbeb] px-2 py-0.5 text-[11px] font-medium text-[#b45309]">
      {chipText(c)} · unverified
    </button>
  )
}

function StepperC() {
  const cur = STAGES.indexOf(d.headline.stage)
  return (
    <ol className="flex items-center gap-1">
      {STAGES.map((s, i) => (
        <li key={s} className="flex flex-1 flex-col gap-1.5">
          <div className={`h-1.5 rounded-full ${i < cur ? 'bg-[#6366f1]' : i === cur ? 'bg-[#6366f1] ring-4 ring-[#6366f1]/15' : 'bg-[#e2e8f0]'}`} />
          <span className={`text-[11px] ${i === cur ? 'font-semibold text-[#4338ca]' : i < cur ? 'text-[#475569]' : 'text-[#94a3b8]'}`}>{s}</span>
        </li>
      ))}
    </ol>
  )
}

const dotC: Record<TimelineEvent['kind'], string> = {
  incident: 'bg-[#e11d48]', treatment: 'bg-[#0d9488]', legal: 'bg-[#6366f1]', communication: 'bg-[#64748b]', deadline: 'bg-[#d97706]',
}

function TimelineC() {
  const { inScale, rows, off, todayX } = scale(d.timeline)
  return (
    <div className="relative mt-7 flex">
      <div className="relative flex-1" style={{ height: 24 + rows * 15 }}>
        <div className="absolute left-0 top-2 h-1 rounded-full bg-[#e2e8f0]" style={{ width: '100%' }} />
        <div className="absolute left-0 top-2 h-1 rounded-full bg-[#c7d2fe]" style={{ width: `${todayX}%` }} />
        {inScale.map(({ e, x, row }, i) => (
          <div key={i} className="absolute" style={{ left: `${x}%`, top: 4 }}>
            <div className={`-ml-1.5 h-3 w-3 rounded-full ring-2 ring-white ${e.is_future ? 'bg-white !ring-[#cbd5e1]' : dotC[e.kind]}`} />
            <div className={`absolute left-0 whitespace-nowrap text-[10.5px] ${e.is_future ? 'text-[#94a3b8]' : 'text-[#475569]'}`} style={{ top: 16 + row * 15 }}>{e.label} <span className="text-[#94a3b8]">{fmt(e.date)}</span></div>
          </div>
        ))}
        <div className="absolute -top-1 h-6 w-0.5 rounded bg-[#4338ca]" style={{ left: `${todayX}%` }}>
          <span className="absolute -top-4 -translate-x-1/2 rounded bg-[#4338ca] px-1 text-[9px] font-semibold text-white">Today</span>
        </div>
      </div>
      <div className="ml-6 shrink-0 text-right">
        {off.map((e, i) => <div key={i} className="rounded-md bg-[#fffbeb] px-2 py-1 text-[11px] text-[#b45309]"><b>{e.label}</b> {fmtY(e.date)}</div>)}
      </div>
    </div>
  )
}

function TileC({ f, tone }: { f?: Fact | null; tone: string }) {
  if (!f) return null
  return (
    <div className="rounded-xl border border-[#e2e8f0] bg-white p-5 shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
      <div className="flex items-center gap-2 text-[12px] font-medium text-[#64748b]"><span className={`h-2 w-2 rounded-full ${tone}`} />{f.label}</div>
      <div className={`mt-2 text-[28px] font-semibold tracking-tight tabular-nums ${f.verified ? 'text-[#0f172a]' : 'text-[#b45309]'}`}>{f.value}</div>
      <div className="mt-3 flex flex-wrap gap-1">{f.citations.slice(0, 2).map((c, i) => <ChipC key={i} c={c} />)}</div>
    </div>
  )
}

const statusC: Record<ActionItem['status'], string> = {
  overdue: 'bg-[#fff1f2] text-[#be123c]', upcoming: 'bg-[#eef2ff] text-[#4338ca]', waiting: 'bg-[#f1f5f9] text-[#475569]',
}

function CardC({ title, children, extra }: { title: string; children: React.ReactNode; extra?: React.ReactNode }) {
  return (
    <section className="rounded-xl border border-[#e2e8f0] bg-white p-5 shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
      <div className="mb-3 flex items-baseline justify-between"><h2 className="text-[14px] font-semibold text-[#0f172a]">{title}</h2>{extra}</div>
      {children}
    </section>
  )
}

function DirectionC() {
  const groups: ActionItem['status'][] = ['overdue', 'upcoming', 'waiting']
  return (
    <div className="min-h-screen bg-[#f8fafc] text-[#0f172a]" style={{ fontFamily: 'Inter, sans-serif' }}>
      <div className="mx-auto max-w-[1280px] px-8 py-6">
        <header className="mb-5 flex items-center justify-between">
          <div className="flex items-center gap-3.5">
            <div className="grid h-12 w-12 place-items-center rounded-full bg-gradient-to-br from-[#6366f1] to-[#4338ca] text-[15px] font-semibold text-white">{initials(d.matter.client_name)}</div>
            <div>
              <h1 className="text-[22px] font-semibold tracking-tight">{d.matter.client_name}</h1>
              <div className="text-[13px] text-[#64748b]">{d.matter.title} · {d.matter.display_number}</div>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <input placeholder="Find in case…" className="w-60 rounded-lg border border-[#e2e8f0] bg-white px-3 py-2 text-[13px] placeholder:text-[#94a3b8]" />
            <button className="rounded-lg bg-[#4338ca] px-4 py-2 text-[13px] font-semibold text-white shadow-sm">Share with provider</button>
          </div>
        </header>

        <section className="rounded-xl border border-[#e2e8f0] bg-white p-6 shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
          <StepperC />
          <TimelineC />
          <div className="mt-8 border-t border-[#f1f5f9] pt-5">
            <p className="text-[19px] font-medium leading-snug">{d.headline.status_line}</p>
            <ul className="mt-3 grid grid-cols-2 gap-x-8 gap-y-2.5">
              {d.headline.bullets.map(b => (
                <li key={b.id} className="text-[13.5px] leading-relaxed text-[#334155]">
                  <span className="font-semibold text-[#0f172a]">{b.label}.</span> {b.value} {b.citations.map((c, i) => <ChipC key={i} c={c} />)}
                </li>
              ))}
            </ul>
          </div>
        </section>

        <div className="mt-5 grid grid-cols-4 gap-5">
          <TileC f={d.kpis.specials} tone="bg-[#0d9488]" />
          <TileC f={d.kpis.coverage[0]} tone="bg-[#6366f1]" />
          <TileC f={d.kpis.firm_spent} tone="bg-[#64748b]" />
          <TileC f={d.kpis.case_value} tone="bg-[#d97706]" />
        </div>

        <div className="mt-5 grid grid-cols-12 gap-5">
          <div className="col-span-7">
            <CardC title="Needs action" extra={<span className="text-[12px] text-[#64748b]">Last client contact <b className="text-[#0f172a]">{fmt(d.last_client_contact?.date)}</b></span>}>
              {groups.map(g => {
                const items = d.actions.filter(a => a.status === g)
                if (!items.length) return null
                return (
                  <div key={g} className="mb-3 last:mb-0">
                    <div className={`mb-1.5 inline-block rounded-md px-2 py-0.5 text-[11px] font-semibold capitalize ${statusC[g]}`}>{g === 'waiting' ? 'Waiting on others' : g} · {items.length}</div>
                    {items.map((a, i) => (
                      <div key={i} className="flex items-center justify-between gap-3 rounded-lg px-2 py-2 hover:bg-[#f8fafc]">
                        <div className="text-[13.5px]">{a.title}{a.waiting_on && <span className="text-[#64748b]"> · {a.waiting_on}</span>}</div>
                        <div className="flex shrink-0 items-center gap-2">{a.citations.slice(0, 1).map((c, j) => <ChipC key={j} c={c} />)}<span className="w-14 text-right text-[12px] tabular-nums text-[#64748b]">{fmt(a.due_date)}</span></div>
                      </div>
                    ))}
                  </div>
                )
              })}
            </CardC>
          </div>
          <div className="col-span-5 space-y-5">
            <CardC title="Injuries">
              <div className="flex flex-wrap gap-2">
                {d.injuries.map(f => (
                  <div key={f.id} className={`rounded-lg border px-3 py-2 ${f.verified ? 'border-[#e2e8f0]' : 'border-dashed border-[#d97706]'}`}>
                    <div className="text-[13px] font-medium">{f.value}</div>
                    <div className="mt-1">{f.citations.map((c, i) => <ChipC key={i} c={c} />)}</div>
                  </div>
                ))}
              </div>
            </CardC>
            <CardC title="Treatment by provider">
              {d.treatment.map((t, i) => (
                <div key={i} className="flex items-center justify-between border-t border-[#f1f5f9] py-2.5 first:border-0">
                  <div><div className="text-[13.5px] font-medium">{t.provider}</div><div className="text-[12px] text-[#64748b]">{t.visit_count} visit{t.visit_count === 1 ? '' : 's'} · {fmt(t.first_visit)} – {fmt(t.last_visit)}</div></div>
                  <div className="text-[14px] font-semibold tabular-nums">{t.billed?.value ?? <span className="text-[12px] font-normal text-[#94a3b8]">Bill pending</span>}</div>
                </div>
              ))}
            </CardC>
          </div>
        </div>
        <footer className="mt-6 text-center text-[11.5px] text-[#94a3b8]">Draft for attorney review · generated {fmtY(d.generated_at.slice(0, 10))} · ${d.cost_usd.toFixed(2)}</footer>
      </div>
    </div>
  )
}

function Directions() {
  const which = new URLSearchParams(location.search).get('d') ?? 'a'
  const Comp = { a: DirectionA, b: DirectionB, c: DirectionC }[which] ?? DirectionA
  return <Comp />
}

createRoot(document.getElementById('root')!).render(<StrictMode><Directions /></StrictMode>)
