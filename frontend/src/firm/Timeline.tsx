// Subtle timeline: a thin strip with phase shading and one dot per event. Only a handful of key
// milestones get labels (chosen by rules, packed to fit the width); everything else is on hover,
// and "All events" opens the full chronological list. Click any dot or row to open its source.
import { useLayoutEffect, useMemo, useRef, useState } from 'react'
import type { Citation, TimelineEvent } from '../api/types'
import { DAY, daysFromToday, fmtDate, parseDate } from '../components'

type Kind = TimelineEvent['kind']

const DOT: Record<Kind, string> = {
  incident: 'bg-danger-600', treatment: 'bg-ok-600', legal: 'bg-brand-500', communication: 'bg-slate-400', deadline: 'bg-warn-600',
}
const KIND_LABEL: Record<Kind, string> = {
  incident: 'Incident', treatment: 'Treatment', legal: 'Legal', communication: 'Contact', deadline: 'Deadline',
}

// Generic PI vocabulary used to pick milestones (no case content).
const SUIT_RE = /\b(summons|complaint|lawsuit|suit|petition)\b.*\b(filed|commenced|served|dated)\b|\b(filed|commenced)\b.*\b(suit|lawsuit|complaint)\b/i
const SOL_RE = /statute of limitations|limitations date|\bSOL\b/i

const MAX_LABELS = 7
const LABEL_ROWS = 2
const CHAR_PX = 6.2
/** Share of the strip given to the future (today → last upcoming event), so upcoming items are readable. */
const FUTURE_FRAC = 0.16
/** Upcoming events further out than this are pinned at the right edge instead of stretching the scale. */
const HORIZON_DAYS = 120

interface Pt { e: TimelineEvent; t: number; x: number }
interface Label { pt: Pt; caption: string; tone: string; align: 'left' | 'right' | 'center'; row: number }

const time = (e: TimelineEvent) => parseDate(e.date)?.getTime() ?? 0

function buildScale(events: TimelineEvent[]) {
  const now = Date.now()
  const sorted = [...events].filter(e => parseDate(e.date)).sort((a, b) => time(a) - time(b))
  const horizon = now + HORIZON_DAYS * DAY
  const inScale = sorted.filter(e => time(e) <= horizon)
  const pinned = sorted.filter(e => time(e) > horizon)
  const past = inScale.filter(e => time(e) <= now)
  const future = inScale.filter(e => time(e) > now)
  const t0 = past.length ? time(past[0]) : now - 30 * DAY
  const tEnd = future.length ? time(future[future.length - 1]) : now
  const split = future.length ? 1 - FUTURE_FRAC : 0.985
  const x = (t: number) => t <= now
    ? ((t - t0) / Math.max(now - t0, DAY)) * split * 100
    : (split + ((t - now) / Math.max(tEnd - now, DAY)) * (1 - split)) * 100
  const pts: Pt[] = inScale.map(e => ({ e, t: time(e), x: x(time(e)) }))
  return { pts, pinned, x, now, todayX: x(now), t0, sorted }
}

const KIND_TONE: Record<Kind, string> = {
  incident: 'text-danger-700', treatment: 'text-ok-700', legal: 'text-brand-700', communication: 'text-slate-600', deadline: 'text-warn-700',
}

/** Short caption from an event label: the part before ":" or ",", capped. */
function caption(label: string) {
  const head = label.split(/[:,(—–]/)[0].trim() || label
  return head.length > 24 ? `${head.slice(0, 23).trimEnd()}…` : head
}

function pickMilestones(pts: Pt[], now: number) {
  // Prefer the digest's own `major` flags; keyword rules below are the fallback.
  const major = pts.filter(p => p.e.major)
  if (major.length) {
    const next = major.find(p => p.t > now)
    const first = major.find(p => p.e.kind === 'incident') ?? major[0]
    const rest = major.filter(p => p !== next && p !== first).sort((a, b) => b.t - a.t)
    return [first, next, ...rest].filter((p): p is Pt => !!p).map(p => ({
      pt: p,
      caption: p === next ? `Next: ${caption(p.e.label)}` : caption(p.e.label),
      tone: p.t > now ? 'text-warn-700' : KIND_TONE[p.e.kind],
    }))
  }
  const past = pts.filter(p => p.t <= now)
  const future = pts.filter(p => p.t > now)
  const firstWhere = (arr: Pt[], f: (p: Pt) => boolean) => arr.find(f)
  const lastWhere = (arr: Pt[], f: (p: Pt) => boolean) => [...arr].reverse().find(f)
  const treat = (p: Pt) => p.e.kind === 'treatment'
  // Priority order: the first ones win space when the strip is narrow.
  const cands: [Pt | undefined, string, string][] = [
    [firstWhere(past, p => p.e.kind === 'incident') ?? past[0], 'Incident', 'text-danger-700'],
    [future[0], 'Next', 'text-warn-700'],
    [firstWhere(pts, p => SUIT_RE.test(p.e.label)), 'Suit filed', 'text-brand-700'],
    [firstWhere(future, p => SOL_RE.test(p.e.label)), 'SOL', 'text-danger-700'],
    [firstWhere(past, treat), 'First treatment', 'text-ok-700'],
    [lastWhere(past, treat), 'Last treatment', 'text-ok-700'],
    [past[past.length - 1], 'Latest', 'text-slate-600'],
  ]
  const seen = new Set<TimelineEvent>()
  return cands.filter(([p]) => p && !seen.has(p.e) && seen.add(p.e)).map(([p, caption, tone]) => ({ pt: p!, caption, tone }))
}

function packLabels(cands: { pt: Pt; caption: string; tone: string }[], widthPx: number): Label[] {
  const rows: [number, number][][] = Array.from({ length: LABEL_ROWS }, () => [])
  const out: Label[] = []
  for (const c of cands) {
    if (out.length >= MAX_LABELS) break
    const chars = Math.max(c.caption.length, fmtDate(c.pt.e.date, true).length)
    const w = ((chars * CHAR_PX + 10) / Math.max(widthPx, 1)) * 100
    const align: Label['align'] = c.pt.x + w > 100 ? 'right' : c.pt.x - w / 2 < 0 ? 'left' : 'center'
    const start = align === 'left' ? c.pt.x : align === 'right' ? c.pt.x - w : c.pt.x - w / 2
    const end = start + w
    const row = rows.findIndex(r => r.every(([a, b]) => end < a || start > b))
    if (row === -1) continue
    rows[row].push([start, end])
    out.push({ ...c, align, row })
  }
  return out
}

export function TimelineStrip({ events, onOpenSource }: { events: TimelineEvent[]; onOpenSource?: (c: Citation) => void }) {
  const ref = useRef<HTMLDivElement>(null)
  const [w, setW] = useState(900)
  const [hover, setHover] = useState<Pt | null>(null)
  const [showAll, setShowAll] = useState(false)
  useLayoutEffect(() => {
    if (!ref.current) return
    const ro = new ResizeObserver(([e]) => setW(e.contentRect.width))
    ro.observe(ref.current)
    return () => ro.disconnect()
  }, [])

  const s = useMemo(() => buildScale(events), [events])
  const labels = useMemo(() => packLabels(pickMilestones(s.pts, s.now), w), [s, w])
  if (!events.length) return <div className="mt-5 text-[12.5px] text-slate-400">No dated events found in the record yet.</div>

  const open = (e: TimelineEvent) => e.citations[0] && onOpenSource?.(e.citations[0])
  // Phases: shaded spans behind the dots.
  const treatPts = s.pts.filter(p => p.e.kind === 'treatment' && p.t <= s.now)
  const suit = s.pts.find(p => SUIT_RE.test(p.e.label))
  const phases = [
    treatPts.length > 1 && { from: treatPts[0].x, to: treatPts[treatPts.length - 1].x, cls: 'bg-ok-600/25', name: 'Treatment' },
    suit && { from: suit.x, to: s.todayX, cls: 'bg-brand-500/25', name: 'Litigation' },
  ].filter(Boolean) as { from: number; to: number; cls: string; name: string }[]
  const labelled = new Set(labels.map(l => l.pt.e))

  return (
    <div className="mt-5">
      <div className="flex items-start gap-4">
        <div ref={ref} className="relative min-w-0 flex-1" style={{ height: 30 + LABEL_ROWS * 28 }}>
          {/* track + phases + future zone */}
          <div className="absolute inset-x-0 top-[14px] h-1.5 rounded-full bg-line-soft" />
          {phases.map(p => (
            <div key={p.name} title={p.name} className={`absolute top-[14px] h-1.5 rounded-full ${p.cls}`}
              style={{ left: `${p.from}%`, width: `${Math.max(p.to - p.from, 0.6)}%` }} />
          ))}
          <div className="absolute top-[14px] right-0 h-1.5 rounded-r-full bg-[repeating-linear-gradient(90deg,var(--color-warn-200)_0_3px,transparent_3px_6px)]"
            style={{ left: `${s.todayX}%` }} />
          {/* year ticks */}
          {s.pts.length > 0 && yearTicks(s).map(y => (
            <span key={y.year} className="pointer-events-none absolute top-0 -translate-x-1/2 text-[9.5px] tabular-nums text-slate-300" style={{ left: `${y.x}%` }}>
              {y.year}
            </span>
          ))}
          {/* dots */}
          {s.pts.map((p, i) => (
            <button key={i} type="button" onClick={() => open(p.e)} onMouseEnter={() => setHover(p)} onMouseLeave={() => setHover(null)}
              onFocus={() => setHover(p)} onBlur={() => setHover(null)} aria-label={`${p.e.label}, ${fmtDate(p.e.date, true)}`}
              className="absolute top-[10px] -ml-[7px] grid h-[14px] w-[14px] cursor-pointer place-items-center rounded-full" style={{ left: `${p.x}%` }}>
              <span className={`block rounded-full transition-transform ${labelled.has(p.e) ? 'h-2.5 w-2.5 ring-2 ring-white' : p.e.major ? 'h-2 w-2' : 'h-[6px] w-[6px] opacity-70'} ${p.t > s.now ? 'bg-white ring-[1.5px] !ring-warn-600' : DOT[p.e.kind]} ${hover === p ? 'scale-150' : ''}`} />
            </button>
          ))}
          {/* today */}
          <div className="pointer-events-none absolute top-[6px] h-[22px] w-0.5 -ml-px rounded bg-brand-700" style={{ left: `${s.todayX}%` }} />
          {/* milestone labels */}
          {labels.map((l, i) => (
            <button key={i} type="button" onClick={() => open(l.pt.e)} title={l.pt.e.label}
              className={`absolute cursor-pointer whitespace-nowrap leading-tight hover:underline ${l.align === 'left' ? '' : l.align === 'right' ? '-translate-x-full' : '-translate-x-1/2'} ${l.align === 'center' ? 'text-center' : l.align === 'right' ? 'text-right' : 'text-left'}`}
              style={{ left: `${l.pt.x}%`, top: 30 + l.row * 28 }}>
              <span className={`block text-[11px] font-semibold ${l.tone}`}>{l.caption}</span>
              <span className="block text-[10.5px] tabular-nums text-slate-400">{fmtDate(l.pt.e.date, true)}</span>
            </button>
          ))}
          {/* hover card */}
          {hover && !labelled.has(hover.e) && (
            <div className={`pointer-events-none absolute z-10 max-w-[280px] rounded-lg bg-slate-900 px-2.5 py-1.5 text-[11.5px] text-white shadow-pop ${hover.x > 70 ? '-translate-x-full' : hover.x < 15 ? '' : '-translate-x-1/2'}`}
              style={{ left: `${hover.x}%`, top: 30 }}>
              <div className="font-medium">{hover.e.label}</div>
              <div className="text-slate-400">{KIND_LABEL[hover.e.kind]} · {fmtDate(hover.e.date, true)}</div>
            </div>
          )}
        </div>
        {s.pinned.length > 0 && (
          <div className="mt-2 flex shrink-0 flex-col items-end gap-1">
            {s.pinned.slice(0, 2).map((e, i) => (
              <button key={i} type="button" onClick={() => open(e)} title={e.label}
                className="max-w-[160px] cursor-pointer truncate rounded-md bg-warn-50 px-2 py-1 text-[11px] text-warn-700 hover:bg-warn-200/50">
                {SOL_RE.test(e.label) ? 'SOL' : e.label} · {fmtDate(e.date, true)} →
              </button>
            ))}
          </div>
        )}
      </div>

      {/* legend + all events toggle */}
      <div className="mt-1 flex flex-wrap items-center gap-x-4 gap-y-1 text-[11px] text-slate-500">
        {phases.map(p => <span key={p.name} className="inline-flex items-center gap-1.5"><span className={`h-1.5 w-4 rounded-full ${p.cls}`} />{p.name}</span>)}
        <span className="inline-flex items-center gap-1.5"><span className="h-3 w-0.5 rounded bg-brand-700" />Today</span>
        <span className="inline-flex items-center gap-1.5"><span className="h-1.5 w-4 rounded-full bg-[repeating-linear-gradient(90deg,var(--color-warn-200)_0_3px,transparent_3px_6px)]" />Upcoming</span>
        <button type="button" onClick={() => setShowAll(v => !v)}
          className="ml-auto cursor-pointer font-semibold text-brand-700 hover:underline">
          {showAll ? 'Hide events' : `All ${s.sorted.length} events`}
        </button>
      </div>
      {showAll && <EventList events={s.sorted} onOpen={open} />}
    </div>
  )
}

function yearTicks(s: ReturnType<typeof buildScale>) {
  const out: { year: number; x: number }[] = []
  for (let y = new Date(s.t0).getFullYear() + 1; y <= new Date(s.now).getFullYear(); y++) {
    const t = new Date(y, 0, 1).getTime()
    if (t > s.t0 && t < s.now) out.push({ year: y, x: s.x(t) })
  }
  return out
}

function EventList({ events, onOpen }: { events: TimelineEvent[]; onOpen: (e: TimelineEvent) => void }) {
  const upcoming = events.filter(e => (daysFromToday(e.date) ?? -1) >= 0)
  const past = events.filter(e => (daysFromToday(e.date) ?? -1) < 0).reverse()
  const Row = ({ e }: { e: TimelineEvent }) => (
    <li>
      <button type="button" onClick={() => onOpen(e)}
        className="flex w-full cursor-pointer items-start gap-2.5 rounded-md px-2 py-1.5 text-left text-[12.5px] hover:bg-page">
        <span className={`mt-[5px] h-2 w-2 shrink-0 rounded-full ${DOT[e.kind]}`} />
        <span className="w-[86px] shrink-0 tabular-nums text-slate-400">{fmtDate(e.date, true)}</span>
        <span className="min-w-0 flex-1 text-slate-800">{e.label}</span>
        <span className="hidden shrink-0 text-[11px] text-slate-400 sm:inline">{KIND_LABEL[e.kind]}</span>
      </button>
    </li>
  )
  return (
    <div className="mt-3 max-h-80 overflow-y-auto rounded-lg border border-line-soft p-1.5">
      {upcoming.length > 0 && <>
        <div className="px-2 pt-1 text-[10.5px] font-semibold uppercase tracking-wider text-warn-700">Upcoming</div>
        <ul>{upcoming.map((e, i) => <Row key={`u${i}`} e={e} />)}</ul>
      </>}
      {past.length > 0 && <>
        <div className="px-2 pt-2 text-[10.5px] font-semibold uppercase tracking-wider text-slate-400">Past</div>
        <ul>{past.map((e, i) => <Row key={`p${i}`} e={e} />)}</ul>
      </>}
    </div>
  )
}
