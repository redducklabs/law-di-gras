// Small shared primitives: Card, Badge, Tile, Avatar, Skeleton. S4 imports these; never edits.
import type { ReactNode } from 'react'
import type { Citation, Fact } from '../api/types'
import { SourceChips } from './SourceChip'
import { initials } from './format'

export function Card({ title, extra, children, className = '', pad = true }: {
  title?: ReactNode
  extra?: ReactNode
  children: ReactNode
  className?: string
  pad?: boolean
}) {
  return (
    <section className={`rounded-xl border border-line bg-surface shadow-card ${pad ? 'p-5' : ''} ${className}`}>
      {(title || extra) && (
        <div className={`mb-3 flex flex-wrap items-baseline justify-between gap-x-3 gap-y-1 ${pad ? '' : 'px-5 pt-5'}`}>
          {title && <h2 className="text-[14px] font-semibold text-slate-900">{title}</h2>}
          {extra}
        </div>
      )}
      {children}
    </section>
  )
}

export type Tone = 'brand' | 'danger' | 'warn' | 'ok' | 'neutral'

const badgeTone: Record<Tone, string> = {
  brand: 'bg-brand-50 text-brand-700',
  danger: 'bg-danger-50 text-danger-700',
  warn: 'bg-warn-50 text-warn-700',
  ok: 'bg-ok-50 text-ok-700',
  neutral: 'bg-slate-100 text-slate-600',
}

export function Badge({ tone = 'neutral', children, className = '' }: { tone?: Tone; children: ReactNode; className?: string }) {
  return (
    <span className={`inline-flex items-center gap-1 rounded-md px-2 py-0.5 text-[11px] font-semibold ${badgeTone[tone]} ${className}`}>
      {children}
    </span>
  )
}

const dotTone: Record<Tone, string> = {
  brand: 'bg-brand-500', danger: 'bg-danger-600', warn: 'bg-warn-600', ok: 'bg-ok-600', neutral: 'bg-slate-400',
}

/** Big type only for short values; long values step down and clamp to two lines (full text on hover). */
function valueSize(v: string, compact: boolean) {
  if (v.length <= 14) return compact ? 'text-[22px] sm:text-[24px]' : 'text-[24px] sm:text-[26px]'
  if (v.length <= 28) return 'text-[17px] sm:text-[18px]'
  return 'text-[14px] leading-snug'
}

/** KPI tile for a Fact. Unverified values render amber with a dashed edge. */
export function Tile({ fact, label, tone = 'neutral', sub, onOpen, compact = false }: {
  fact?: Fact | null
  label?: string
  tone?: Tone
  sub?: ReactNode
  onOpen?: (c: Citation) => void
  compact?: boolean
}) {
  return (
    <div className={`flex min-w-0 flex-col rounded-xl border bg-surface shadow-card ${compact ? 'p-3.5 sm:p-4' : 'p-4 sm:p-5'} ${fact && !fact.verified ? 'border-dashed border-warn-600/60' : 'border-line'}`}>
      <div className="flex items-center gap-2 text-[12px] font-medium text-slate-500">
        <span className={`h-2 w-2 shrink-0 rounded-full ${dotTone[tone]}`} />
        <span className="truncate">{fact?.label ?? label}</span>
      </div>
      {fact ? (
        <>
          <div title={fact.value}
            className={`mt-1 line-clamp-2 font-semibold tracking-tight tabular-nums ${valueSize(fact.value, compact)} ${fact.verified ? 'text-slate-900' : 'text-warn-700'}`}>
            {fact.value}
          </div>
          {sub && <div className="mt-0.5 truncate text-[12px] text-slate-500">{sub}</div>}
          <div className={`mt-auto ${compact ? 'pt-2' : 'pt-3'}`}><SourceChips citations={fact.citations} onOpen={onOpen} max={compact ? 1 : 2} showMore={!compact} /></div>
        </>
      ) : (
        <div className="mt-1 text-[14px] text-slate-400">Not found in the record</div>
      )}
    </div>
  )
}

export function Avatar({ name, src, size = 48 }: { name: string; src?: string | null; size?: number }) {
  return src ? (
    <img src={src} alt="" width={size} height={size} className="shrink-0 rounded-full object-cover ring-2 ring-white" />
  ) : (
    <div style={{ width: size, height: size, fontSize: size * 0.32 }}
      className="grid shrink-0 place-items-center rounded-full bg-gradient-to-br from-brand-500 to-brand-700 font-semibold text-white">
      {initials(name)}
    </div>
  )
}

export function Skeleton({ className = '' }: { className?: string }) {
  return <div className={`animate-pulse rounded-md bg-slate-200/70 ${className}`} />
}
