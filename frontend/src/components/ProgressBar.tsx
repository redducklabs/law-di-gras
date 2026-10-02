// Slim progress for long background runs (Blind spots review, built-in audit): stage, percent, elapsed.
import { useEffect, useState } from 'react'
import type { RunProgress } from '../api/types'

/** pct may arrive as 0..1 or 0..100; normalize to 0..100. */
export function pctOf(p: RunProgress) {
  const v = p.pct <= 1 && p.pct > 0 ? p.pct * 100 : p.pct
  return Math.max(0, Math.min(100, Math.round(v || 0)))
}

function elapsed(from?: string | null, to?: string | null, now = Date.now()) {
  if (!from) return null
  const s = Math.max(0, Math.round(((to ? Date.parse(to) : now) - Date.parse(from)) / 1000))
  if (!Number.isFinite(s)) return null
  return s < 60 ? `${s}s` : `${Math.floor(s / 60)}m ${String(s % 60).padStart(2, '0')}s`
}

export function ProgressBar({ progress: p, className = '' }: { progress: RunProgress; className?: string }) {
  const live = p.status === 'queued' || p.status === 'running'
  const [now, setNow] = useState(Date.now())
  useEffect(() => {
    if (!live) return
    const t = setInterval(() => setNow(Date.now()), 1000)
    return () => clearInterval(t)
  }, [live])
  const pct = p.status === 'done' ? 100 : pctOf(p)
  const failed = p.status === 'failed'
  const took = elapsed(p.started_at, p.finished_at, now)
  return (
    <div className={`min-w-0 ${className}`} role="progressbar" aria-valuemin={0} aria-valuemax={100} aria-valuenow={pct} aria-label={p.stage}>
      <div className="flex items-baseline justify-between gap-3 text-[11.5px]">
        <span className={`min-w-0 truncate ${failed ? 'text-danger-700' : 'text-slate-600'}`} title={p.error ?? p.stage}>
          {failed ? `Failed${p.error ? `: ${p.error}` : ''}` : p.status === 'queued' ? 'Queued…' : p.stage || 'Working…'}
        </span>
        <span className="shrink-0 tabular-nums text-slate-400">{pct}%{took && ` · ${took}`}</span>
      </div>
      <div className="mt-1 h-1 overflow-hidden rounded-full bg-line-soft">
        <div className={`h-1 rounded-full transition-[width] duration-500 ease-out ${failed ? 'bg-danger-600' : 'bg-brand-500'} ${live && pct === 0 ? 'w-1/4 animate-pulse' : ''}`}
          style={live && pct === 0 ? undefined : { width: `${pct}%` }} />
      </div>
    </div>
  )
}
