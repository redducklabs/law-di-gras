import type { Citation } from '../api/types'
import { fmtDate } from './format'

export const chipLabel = (c: Citation) =>
  c.page ? `${c.source_title} · p.${c.page}` : c.date ? `${c.source_title} · ${fmtDate(c.date)}` : c.source_title

/** A clickable link to the record. Unverified citations are dashed amber and say so. */
export function SourceChip({ citation: c, onOpen, compact = false }: {
  citation: Citation
  onOpen?: (c: Citation) => void
  compact?: boolean
}) {
  const label = chipLabel(c)
  const base = 'inline-flex max-w-full items-center gap-1 rounded-full px-2 py-0.5 text-[11px] font-medium align-middle transition-colors focus-visible:outline-2 focus-visible:outline-offset-1 focus-visible:outline-brand-500'
  const title = `“${c.quote}”${c.verified ? '' : ' — not found verbatim in the source; verify before relying on it'}`
  return c.verified ? (
    <button type="button" title={title} onClick={() => onOpen?.(c)}
      className={`${base} cursor-pointer bg-brand-50 text-brand-700 hover:bg-brand-100`}>
      <DocIcon />
      <span className="truncate">{compact ? (c.page ? `p.${c.page}` : c.source_title) : label}</span>
    </button>
  ) : (
    <button type="button" title={title} onClick={() => onOpen?.(c)}
      className={`${base} cursor-pointer border border-dashed border-warn-600 bg-warn-50 text-warn-700 hover:bg-warn-200/40`}>
      <span className="truncate">{compact ? (c.page ? `p.${c.page}` : c.source_title) : label}</span>
      <span className="shrink-0 text-[9.5px] font-semibold uppercase tracking-wide">unverified</span>
    </button>
  )
}

export function SourceChips({ citations, onOpen, max = 3 }: {
  citations: Citation[]
  onOpen?: (c: Citation) => void
  max?: number
}) {
  if (!citations.length) return null
  const shown = citations.slice(0, max)
  const more = citations.length - shown.length
  return (
    <span className="inline-flex flex-wrap items-center gap-1">
      {shown.map((c, i) => <SourceChip key={`${c.source_id}-${i}`} citation={c} onOpen={onOpen} />)}
      {more > 0 && <span className="text-[11px] text-slate-400">+{more}</span>}
    </span>
  )
}

function DocIcon() {
  return (
    <svg width="10" height="10" viewBox="0 0 16 16" fill="currentColor" aria-hidden className="shrink-0">
      <path d="M4 1h6l4 4v10H4z" opacity=".35" /><path d="M10 1v4h4" />
    </svg>
  )
}
