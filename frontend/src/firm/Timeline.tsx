// Subtle timeline: a thin strip with phase shading and one dot per event. Only a handful of key
// milestones get labels at full view; zooming in (animated) reveals more labels for the period in
// view. Everything else is on hover, and "All events" opens the full list. Click any dot to open
// its source. zoomUi="direct": +/− buttons, double-click (Shift = out), pinch or ⌘/Ctrl-scroll at
// the pointer, drag to pan.
import { useCallback, useEffect, useLayoutEffect, useMemo, useRef, useState } from 'react'
import type { Citation, TimelineEvent } from '../api/types'
import { DAY, daysFromToday, fmtDate, parseDate } from '../components'

type Kind = TimelineEvent['kind']
export type ZoomUi = 'none' | 'direct'

const DOT: Record<Kind, string> = {
  incident: 'bg-danger-600', treatment: 'bg-ok-600', legal: 'bg-brand-500', communication: 'bg-slate-400', deadline: 'bg-warn-600',
}
const KIND_LABEL: Record<Kind, string> = {
  incident: 'Incident', treatment: 'Treatment', legal: 'Legal', communication: 'Contact', deadline: 'Deadline',
}
const KIND_TONE: Record<Kind, string> = {
  incident: 'text-danger-700', treatment: 'text-ok-700', legal: 'text-brand-700', communication: 'text-slate-600', deadline: 'text-warn-700',
}

// Generic PI vocabulary used to pick milestones (no case content).
const SUIT_RE = /\b(summons|complaint|lawsuit|suit|petition)\b.*\b(filed|commenced|served|dated)\b|\b(filed|commenced)\b.*\b(suit|lawsuit|complaint)\b/i
const SOL_RE = /statute of limitations|limitations date|\bSOL\b/i

const FULL = { rows: 1, max: 5 }
const ZOOMED = { rows: 2, max: 14 }
const CHAR_PX = 6.2
/** Share of the strip given to the future (today → last upcoming event), so upcoming items are readable. */
const FUTURE_FRAC = 0.16
/** Upcoming events further out than this are pinned at the right edge instead of stretching the scale. */
const HORIZON_DAYS = 120
/** Narrowest view, in overview percent (≈ 30× zoom). */
const MIN_SPAN = 3
const ANIM_MS = 450

interface Pt { e: TimelineEvent; t: number; u: number; x: number }
interface Cand { pt: Pt; caption: string; tone: string }
interface Label extends Cand { align: 'left' | 'right' | 'center'; row: number }
type View = [number, number]

const time = (e: TimelineEvent) => parseDate(e.date)?.getTime() ?? 0
const clampView = ([a, b]: View): View => {
  let span = Math.min(100, Math.max(MIN_SPAN, b - a))
  let s = Math.min(Math.max(0, a), 100 - span)
  if (!Number.isFinite(s)) { s = 0; span = 100 }
  return [s, s + span]
}
const ease = (k: number) => (k < 0.5 ? 4 * k * k * k : 1 - Math.pow(-2 * k + 2, 3) / 2)

/** Overview scale: time → u (0..100), past and future warped so upcoming items stay readable. */
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
  const pastSpan = Math.max(now - t0, DAY), futSpan = Math.max(tEnd - now, DAY)
  const u = (t: number) => t <= now ? ((t - t0) / pastSpan) * split * 100 : (split + ((t - now) / futSpan) * (1 - split)) * 100
  const tOf = (x: number) => x / 100 <= split ? t0 + (x / 100 / split) * pastSpan : now + ((x / 100 - split) / (1 - split)) * futSpan
  const pts = inScale.map(e => ({ e, t: time(e), u: u(time(e)), x: u(time(e)) }))
  return { pts, pinned, u, tOf, now, nowU: u(now), t0, tEnd, sorted }
}
type Scale = ReturnType<typeof buildScale>

/** Short caption from an event label: the part before ":" or ",", capped. */
function caption(label: string, max = 24) {
  const head = label.split(/[:,(—–]/)[0].trim() || label
  return head.length > max ? `${head.slice(0, max - 1).trimEnd()}…` : head
}

function pickMilestones(pts: Pt[], now: number, zoomed: boolean, max = 24): Cand[] {
  const cap = (l: string) => caption(l, max)
  const out: Cand[] = []
  const major = pts.filter(p => p.e.major)
  if (major.length) {
    const next = major.find(p => p.t > now)
    const first = major.find(p => p.e.kind === 'incident') ?? major[0]
    const rest = major.filter(p => p !== next && p !== first).sort((a, b) => b.t - a.t)
    for (const p of [first, next, ...rest]) if (p) out.push({
      pt: p, caption: p === next ? `Next: ${cap(p.e.label)}` : cap(p.e.label),
      tone: p.t > now ? 'text-warn-700' : KIND_TONE[p.e.kind],
    })
  } else {
    const past = pts.filter(p => p.t <= now)
    const future = pts.filter(p => p.t > now)
    const treat = (p: Pt) => p.e.kind === 'treatment'
    const cands: [Pt | undefined, string, string][] = [
      [past.find(p => p.e.kind === 'incident') ?? past[0], 'Incident', 'text-danger-700'],
      [future[0], 'Next', 'text-warn-700'],
      [pts.find(p => SUIT_RE.test(p.e.label)), 'Suit filed', 'text-brand-700'],
      [future.find(p => SOL_RE.test(p.e.label)), 'SOL', 'text-danger-700'],
      [past.find(treat), 'First treatment', 'text-ok-700'],
      [[...past].reverse().find(treat), 'Last treatment', 'text-ok-700'],
      [past[past.length - 1], 'Latest', 'text-slate-600'],
    ]
    for (const [p, c, tone] of cands) if (p) out.push({ pt: p, caption: c, tone })
  }
  // Zoomed in: every other event in view becomes a label candidate too.
  if (zoomed) for (const p of pts) out.push({ pt: p, caption: cap(p.e.label), tone: p.t > now ? 'text-warn-700' : KIND_TONE[p.e.kind] })
  const seen = new Set<TimelineEvent>()
  return out.filter(c => !seen.has(c.pt.e) && seen.add(c.pt.e))
}

function packLabels(cands: Cand[], widthPx: number, rowsN: number, max: number): Label[] {
  const rows: [number, number][][] = Array.from({ length: rowsN }, () => [])
  const out: Label[] = []
  for (const c of cands) {
    if (out.length >= max) break
    const chars = Math.max(c.caption.length, fmtDate(c.pt.e.date, true).length)
    const w = ((chars * CHAR_PX + 12) / Math.max(widthPx, 1)) * 100
    const align: Label['align'] = c.pt.x + w / 2 > 100 ? 'right' : c.pt.x - w / 2 < 0 ? 'left' : 'center'
    const start = align === 'left' ? c.pt.x : align === 'right' ? c.pt.x - w : c.pt.x - w / 2
    const end = start + w
    const row = rows.findIndex(r => r.every(([a, b]) => end < a || start > b))
    if (row === -1) continue
    rows[row].push([start, end])
    out.push({ ...c, align, row })
  }
  return out
}

const fmtMonth = (t: number) => new Date(t).toLocaleDateString('en-US', { month: 'short', year: 'numeric' })

export function TimelineStrip({ events, onOpenSource, zoomUi = 'none' }: {
  events: TimelineEvent[]
  onOpenSource?: (c: Citation) => void
  zoomUi?: ZoomUi
}) {
  const ref = useRef<HTMLDivElement>(null)
  const [w, setW] = useState(900)
  const [hover, setHover] = useState<Pt | null>(null)
  const [showAll, setShowAll] = useState(false)
  const [view, setView] = useState<View>([0, 100])
  const viewRef = useRef<View>(view)
  viewRef.current = view
  const raf = useRef(0)

  useLayoutEffect(() => {
    if (!ref.current) return
    const ro = new ResizeObserver(([e]) => setW(e.contentRect.width))
    ro.observe(ref.current)
    return () => ro.disconnect()
  }, [])

  const animateTo = useCallback((target: View) => {
    cancelAnimationFrame(raf.current)
    const from = viewRef.current, to = clampView(target), t0 = performance.now()
    const step = (now: number) => {
      const k = Math.min(1, (now - t0) / ANIM_MS), e = ease(k)
      setView([from[0] + (to[0] - from[0]) * e, from[1] + (to[1] - from[1]) * e])
      if (k < 1) raf.current = requestAnimationFrame(step)
    }
    raf.current = requestAnimationFrame(step)
  }, [])
  const setNow = useCallback((v: View) => { cancelAnimationFrame(raf.current); setView(clampView(v)) }, [])
  const zoomAt = useCallback((centerU: number, factor: number, animate = true) => {
    const [a, b] = viewRef.current, span = (b - a) / factor
    const k = (centerU - a) / (b - a)
    const v: View = [centerU - k * span, centerU - k * span + span]
    animate ? animateTo(v) : setNow(v)
  }, [animateTo, setNow])

  const s = useMemo(() => buildScale(events), [events])
  const [v0, v1] = view
  const span = v1 - v0
  const zoomed = span < 88
  const vx = (u: number) => ((u - v0) / span) * 100
  const uAtPx = (px: number) => v0 + (px / Math.max(w, 1)) * span

  const pts: Pt[] = useMemo(() => s.pts.map(p => ({ ...p, x: ((p.u - v0) / span) * 100 })), [s, v0, span])
  const inView = pts.filter(p => p.x >= -0.5 && p.x <= 100.5)
  const cfg = zoomed ? ZOOMED : FULL
  const labels = useMemo(() => packLabels(pickMilestones(inView, s.now, zoomed, w < 520 ? 13 : 24), w, cfg.rows, cfg.max),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [pts, w, zoomed])
  const labelled = new Set(labels.map(l => l.pt.e))

  // Direct manipulation: ⌘/Ctrl-wheel (and trackpad pinch) zooms at the pointer.
  useEffect(() => {
    const el = ref.current
    if (!el || zoomUi !== 'direct') return
    const onWheel = (e: WheelEvent) => {
      if (!e.ctrlKey && !e.metaKey) return
      e.preventDefault()
      const r = el.getBoundingClientRect()
      zoomAt(uAtPxRef.current(e.clientX - r.left), Math.exp(-e.deltaY * 0.004), false)
    }
    el.addEventListener('wheel', onWheel, { passive: false })
    return () => el.removeEventListener('wheel', onWheel)
  }, [zoomUi, zoomAt])
  const uAtPxRef = useRef(uAtPx)
  uAtPxRef.current = uAtPx

  // Drag to pan (direct mode).
  const drag = useRef<{ x: number; view: View; moved: boolean } | null>(null)
  const onPointerDown = (e: React.PointerEvent) => {
    if (zoomUi !== 'direct' || (e.target as HTMLElement).closest('button')) return
    drag.current = { x: e.clientX, view: viewRef.current, moved: false }
    ;(e.currentTarget as HTMLElement).setPointerCapture(e.pointerId)
  }
  const onPointerMove = (e: React.PointerEvent) => {
    const d = drag.current
    if (!d) return
    const dx = e.clientX - d.x
    if (Math.abs(dx) > 3) d.moved = true
    const du = (dx / Math.max(w, 1)) * (d.view[1] - d.view[0])
    setNow([d.view[0] - du, d.view[1] - du])
  }
  const onPointerUp = () => { drag.current = null }
  const onDoubleClick = (e: React.MouseEvent) => {
    if (zoomUi !== 'direct') return
    const r = ref.current!.getBoundingClientRect()
    zoomAt(uAtPx(e.clientX - r.left), e.shiftKey ? 1 / 2.5 : 2.5)
  }

  if (!events.length) return <div className="mt-5 text-[12.5px] text-slate-400">No dated events found in the record yet.</div>

  const open = (e: TimelineEvent) => e.citations[0] && onOpenSource?.(e.citations[0])
  const treatPts = s.pts.filter(p => p.e.kind === 'treatment' && p.t <= s.now)
  const suit = s.pts.find(p => SUIT_RE.test(p.e.label))
  const phases = [
    treatPts.length > 1 && { from: treatPts[0].u, to: treatPts[treatPts.length - 1].u, cls: 'bg-ok-600/25', name: 'Treatment' },
    suit && { from: suit.u, to: s.nowU, cls: 'bg-brand-500/25', name: 'Litigation' },
  ].filter(Boolean) as { from: number; to: number; cls: string; name: string }[]
  const ticks = timeTicks(s, v0, v1, w)
  const rowsH = 30 + cfg.rows * 28
  const rangeText = `${fmtMonth(s.tOf(v0))} – ${fmtMonth(s.tOf(v1))}`

  return (
    <div className="mt-5">
      <div className="flex items-start gap-4">
        <div className="relative min-w-0 flex-1">
          <div ref={ref}
            onPointerDown={onPointerDown} onPointerMove={onPointerMove} onPointerUp={onPointerUp} onDoubleClick={onDoubleClick}
            className={`relative overflow-x-clip transition-[height] duration-300 ${zoomUi === 'direct' ? `touch-pan-y ${drag.current ? 'cursor-grabbing' : 'cursor-grab'}` : ''} select-none`}
            style={{ height: rowsH }}>
            <div className="absolute inset-x-0 top-[14px] h-1.5 rounded-full bg-line-soft" />
            {phases.map(p => (
              <div key={p.name} title={p.name} className={`absolute top-[14px] h-1.5 rounded-full ${p.cls}`}
                style={{ left: `${vx(p.from)}%`, width: `${Math.max(vx(p.to) - vx(p.from), 0.6)}%` }} />
            ))}
            <div className="absolute top-[14px] h-1.5 rounded-r-full bg-[repeating-linear-gradient(90deg,var(--color-warn-200)_0_3px,transparent_3px_6px)]"
              style={{ left: `${vx(s.nowU)}%`, right: `${100 - vx(100)}%` }} />
            {ticks.map(t => (
              <span key={t.key} className={`pointer-events-none absolute top-0 -translate-x-1/2 whitespace-nowrap text-[9.5px] tabular-nums ${t.major ? 'text-slate-400' : 'text-slate-300'}`}
                style={{ left: `${t.x}%` }}>{t.text}</span>
            ))}
            {inView.map((p, i) => (
              <button key={i} type="button" onClick={() => open(p.e)} onMouseEnter={() => setHover(p)} onMouseLeave={() => setHover(null)}
                onFocus={() => setHover(p)} onBlur={() => setHover(null)} aria-label={`${p.e.label}, ${fmtDate(p.e.date, true)}`}
                className="absolute top-[10px] -ml-[7px] grid h-[14px] w-[14px] cursor-pointer place-items-center rounded-full" style={{ left: `${p.x}%` }}>
                <span className={`block rounded-full transition-all duration-200 ${labelled.has(p.e) ? 'h-2.5 w-2.5 ring-2 ring-white' : p.e.major || zoomed ? 'h-2 w-2' : 'h-[6px] w-[6px] opacity-70'} ${p.t > s.now ? 'bg-white ring-[1.5px] !ring-warn-600' : DOT[p.e.kind]} ${hover?.e === p.e ? 'scale-150' : ''}`} />
              </button>
            ))}
            {vx(s.nowU) >= 0 && vx(s.nowU) <= 100 && (
              <div className="pointer-events-none absolute top-[6px] h-[22px] w-0.5 -ml-px rounded bg-brand-700" style={{ left: `${vx(s.nowU)}%` }} />
            )}
            {labels.map(l => (
              <button key={`${l.pt.e.date}-${l.pt.e.label}`} type="button" onClick={() => open(l.pt.e)} title={l.pt.e.label}
                className={`tl-fade absolute cursor-pointer whitespace-nowrap leading-tight hover:underline ${l.align === 'left' ? '' : l.align === 'right' ? '-translate-x-full' : '-translate-x-1/2'} ${l.align === 'center' ? 'text-center' : l.align === 'right' ? 'text-right' : 'text-left'}`}
                style={{ left: `${Math.max(0, Math.min(100, l.pt.x))}%`, top: 30 + l.row * 28 }}>
                <span className={`block text-[11px] font-semibold ${l.tone}`}>{l.caption}</span>
                <span className="block text-[10.5px] tabular-nums text-slate-400">{fmtDate(l.pt.e.date, true)}</span>
              </button>
            ))}
          </div>
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

      {/* legend + range + all events toggle */}
      <div className="mt-1.5 flex flex-wrap items-center gap-x-4 gap-y-1 text-[11px] text-slate-500">
        {phases.map(p => <span key={p.name} className="inline-flex items-center gap-1.5"><span className={`h-1.5 w-4 rounded-full ${p.cls}`} />{p.name}</span>)}
        <span className="inline-flex items-center gap-1.5"><span className="h-3 w-0.5 rounded bg-brand-700" />Today</span>
        <span className="inline-flex items-center gap-1.5"><span className="h-1.5 w-4 rounded-full bg-[repeating-linear-gradient(90deg,var(--color-warn-200)_0_3px,transparent_3px_6px)]" />Upcoming</span>
        {zoomed && (
          <span className="tl-fade inline-flex items-center gap-1.5 rounded-md bg-brand-50 px-2 py-0.5 font-medium text-brand-700">
            {rangeText} · {inView.length} events
            <button type="button" onClick={() => animateTo([0, 100])} className="cursor-pointer font-semibold underline">Reset</button>
          </span>
        )}
        {zoomUi === 'direct' && !zoomed && <span className="hidden text-slate-400 md:inline">Double-click or pinch to zoom · drag to pan</span>}
        {zoomUi === 'direct' && (
          <span className="ml-auto flex items-center gap-0.5 rounded-lg border border-line bg-surface p-0.5">
            <IconBtn label="Zoom out" onClick={() => zoomAt((v0 + v1) / 2, 1 / 2)}>−</IconBtn>
            <IconBtn label="Zoom in" onClick={() => zoomAt((v0 + v1) / 2, 2)}>+</IconBtn>
          </span>
        )}
        <button type="button" onClick={() => setShowAll(v => !v)} className={`${zoomUi === 'direct' ? '' : 'ml-auto '}cursor-pointer font-semibold text-brand-700 hover:underline`}>
          {showAll ? 'Hide events' : `All ${s.sorted.length} events`}
        </button>
      </div>
      {showAll && <EventList events={s.sorted} onOpen={open} />}
    </div>
  )
}

function IconBtn({ label, onClick, children }: { label: string; onClick: () => void; children: React.ReactNode }) {
  return (
    <button type="button" aria-label={label} title={label} onClick={onClick}
      className="grid h-6 w-6 cursor-pointer place-items-center rounded-md text-[14px] font-semibold leading-none text-slate-600 hover:bg-brand-50 hover:text-brand-700">
      {children}
    </button>
  )
}

/** Year ticks at full view; month ticks once zoomed far enough to have room. */
function timeTicks(s: Scale, v0: number, v1: number, w: number) {
  const span = v1 - v0
  const tA = s.tOf(Math.max(0, v0)), tB = s.tOf(Math.min(100, v1))
  const pxPerMonth = (w * (30 * DAY)) / Math.max(tB - tA, DAY)
  const out: { key: string; x: number; text: string; major: boolean }[] = []
  const start = new Date(tA); start.setDate(1); start.setHours(0, 0, 0, 0)
  const step = pxPerMonth > 70 ? 1 : pxPerMonth > 40 ? 3 : 12
  for (let d = new Date(start); d.getTime() <= tB; d.setMonth(d.getMonth() + 1)) {
    const isYear = d.getMonth() === 0
    if (step === 12 ? !isYear : d.getMonth() % step !== 0) continue
    const t = d.getTime()
    if (t < s.t0 || t > s.tEnd) continue
    const x = ((s.u(t) - v0) / span) * 100
    if (x < 2 || x > 98) continue
    out.push({ key: `${t}`, x, major: isYear, text: isYear ? `${d.getFullYear()}` : d.toLocaleDateString('en-US', { month: 'short' }) })
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
