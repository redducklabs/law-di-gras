// Stage stepper + timeline strip. Wide: horizontal strip with packed labels. Narrow: vertical list.
import { useLayoutEffect, useRef, useState } from 'react'
import type { Citation, TimelineEvent } from '../api/types'
import { DAY, fmtDate, parseDate } from '../components'

/** Canonical PI stages. The digest's `stage` is matched against these (case-insensitive). */
export const STAGES = ['Intake', 'Treating', 'Pre-demand', 'Demand', 'Negotiation', 'Litigation', 'Resolved']

export function stageIndex(stage: string) {
  const s = stage.trim().toLowerCase()
  return STAGES.findIndex(x => x.toLowerCase() === s || s.includes(x.toLowerCase()))
}

export function StageStepper({ stage }: { stage: string }) {
  const cur = stageIndex(stage)
  return (
    <>
      <ol className="hidden items-start gap-1 sm:flex" aria-label="Case stage">
        {STAGES.map((s, i) => (
          <li key={s} className="flex flex-1 flex-col gap-1.5" aria-current={i === cur ? 'step' : undefined}>
            <div className={`h-1.5 rounded-full ${i <= cur ? 'bg-brand-500' : 'bg-line'} ${i === cur ? 'ring-4 ring-brand-500/15' : ''}`} />
            <span className={`text-[11px] ${i === cur ? 'font-semibold text-brand-700' : i < cur ? 'text-slate-600' : 'text-slate-400'}`}>{s}</span>
          </li>
        ))}
      </ol>
      <div className="sm:hidden">
        <div className="flex items-baseline justify-between text-[12px]">
          <span className="font-semibold text-brand-700">{cur >= 0 ? STAGES[cur] : stage}</span>
          {cur >= 0 && <span className="text-slate-400">Stage {cur + 1} of {STAGES.length}</span>}
        </div>
        <div className="mt-1.5 h-1.5 rounded-full bg-line">
          <div className="h-1.5 rounded-full bg-brand-500" style={{ width: `${((cur + 1) / STAGES.length) * 100}%` }} />
        </div>
      </div>
    </>
  )
}

const dot: Record<TimelineEvent['kind'], string> = {
  incident: 'bg-danger-600', treatment: 'bg-ok-600', legal: 'bg-brand-500', communication: 'bg-slate-500', deadline: 'bg-warn-600',
}
export const KIND_LABEL: Record<TimelineEvent['kind'], string> = {
  incident: 'Incident', treatment: 'Treatment', legal: 'Legal', communication: 'Contact', deadline: 'Deadline',
}

const LABEL_PX_PER_CHAR = 6.1
const ROW_H = 15
/** Events beyond this many days ahead are pinned off-scale on the right (e.g. SOL years out). */
const HORIZON_DAYS = 120

function layout(events: TimelineEvent[], widthPx: number) {
  const today = Date.now()
  const t = (e: TimelineEvent) => parseDate(e.date)?.getTime() ?? today
  const sorted = [...events].sort((a, b) => t(a) - t(b))
  const horizon = today + HORIZON_DAYS * DAY
  const inScale = sorted.filter(e => t(e) <= horizon)
  const off = sorted.filter(e => t(e) > horizon)
  const min = Math.min(today, ...inScale.map(t))
  const max = Math.max(today + 30 * DAY, ...inScale.map(t))
  const pos = (ms: number) => ((ms - min) / (max - min || 1)) * 100
  const rowEnd: number[] = []
  const placed = inScale.map(e => {
    const x = pos(t(e))
    const label = `${e.label} ${fmtDate(e.date)}`
    const w = ((label.length * LABEL_PX_PER_CHAR + 14) / Math.max(widthPx, 1)) * 100
    // Labels near the right edge hang left of their dot.
    const flip = x + w > 100
    const start = flip ? x - w : x
    let row = rowEnd.findIndex(end => end < start)
    if (row === -1) row = rowEnd.length
    rowEnd[row] = start + w
    return { e, x, row, flip }
  })
  return { placed, rows: Math.max(rowEnd.length, 1), off, todayX: pos(today) }
}

export function TimelineStrip({ events, onOpenSource }: { events: TimelineEvent[]; onOpenSource?: (c: Citation) => void }) {
  const ref = useRef<HTMLDivElement>(null)
  const [w, setW] = useState(1000)
  useLayoutEffect(() => {
    if (!ref.current) return
    const ro = new ResizeObserver(([e]) => setW(e.contentRect.width))
    ro.observe(ref.current)
    return () => ro.disconnect()
  }, [])

  if (!events.length) return <div className="mt-6 text-[12.5px] text-slate-400">No dated events found in the record yet.</div>
  const { placed, rows, off, todayX } = layout(events, w)
  const open = (e: TimelineEvent) => e.citations[0] && onOpenSource?.(e.citations[0])

  return (
    <>
      {/* Wide */}
      <div className="mt-7 hidden md:flex">
        <div ref={ref} className="relative flex-1" style={{ height: 22 + rows * ROW_H }}>
          <div className="absolute inset-x-0 top-2 h-1 rounded-full bg-line" />
          <div className="absolute left-0 top-2 h-1 rounded-full bg-brand-200" style={{ width: `${todayX}%` }} />
          {placed.map(({ e, x, row, flip }, i) => (
            <button key={i} type="button" onClick={() => open(e)} title={`${KIND_LABEL[e.kind]} · ${fmtDate(e.date, true)}`}
              className="group absolute cursor-pointer" style={{ left: `${x}%`, top: 4 }}>
              <span className={`absolute -ml-1.5 block h-3 w-3 rounded-full ring-2 transition-transform group-hover:scale-125 ${e.is_future ? 'bg-white ring-slate-300' : `${dot[e.kind]} ring-white`}`} />
              {row > 0 && <span className="absolute top-3 block w-px bg-line" style={{ height: row * ROW_H + 2 }} />}
              <span className={`absolute whitespace-nowrap px-1 text-[10.5px] group-hover:text-brand-700 group-hover:underline ${flip ? 'right-0' : 'left-0'} ${e.is_future ? 'text-slate-400' : 'text-slate-600'}`}
                style={{ top: 13 + row * ROW_H }}>
                {e.label} <span className="text-slate-400">{fmtDate(e.date)}</span>
              </span>
            </button>
          ))}
          <div className="pointer-events-none absolute -top-1 h-[15px] w-0.5 rounded bg-brand-700" style={{ left: `${todayX}%` }}>
            <span className="absolute -top-4 -translate-x-1/2 rounded bg-brand-700 px-1 text-[9px] font-semibold text-white">Today</span>
          </div>
        </div>
        {off.length > 0 && (
          <div className="ml-6 flex shrink-0 flex-col items-end gap-1">
            {off.map((e, i) => (
              <button key={i} type="button" onClick={() => open(e)}
                className="cursor-pointer rounded-md bg-warn-50 px-2 py-1 text-[11px] text-warn-700 hover:bg-warn-200/50">
                <b>{e.label}</b> {fmtDate(e.date, true)} →
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Narrow */}
      <ol className="mt-4 space-y-1.5 md:hidden">
        {[...placed.map(p => p.e), ...off].map((e, i) => (
          <li key={i}>
            <button type="button" onClick={() => open(e)} className="flex w-full cursor-pointer items-center gap-2.5 text-left text-[12.5px]">
              <span className={`h-2.5 w-2.5 shrink-0 rounded-full ${e.is_future ? 'bg-white ring-2 ring-slate-300' : dot[e.kind]}`} />
              <span className="w-24 shrink-0 tabular-nums text-slate-400">{fmtDate(e.date, parseDate(e.date)?.getFullYear() !== new Date().getFullYear())}</span>
              <span className={e.is_future ? 'text-slate-500' : 'text-slate-800'}>{e.label}</span>
            </button>
          </li>
        ))}
      </ol>
    </>
  )
}
