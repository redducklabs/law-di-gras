import { useState } from 'react'
import type { Citation } from '../api/types'
import { fmtDate } from './format'

/** File names → readable titles: drop extension, numeric/doc prefixes, and separators. */
export function prettyTitle(t: string) {
  if (!/\.(pdf|docx?|txt|jpe?g|png|tiff?)$/i.test(t)) return t
  const s = t.replace(/\.[a-z0-9]+$/i, '')
    .replace(/_+/g, ' ')
    .replace(/\bdoc-?\d+\b/gi, ' ').replace(/^\d+[- ]+/, '').replace(/(?<=[a-z])-(?=[a-z])/gi, ' ').replace(/\s+/g, ' ').trim()
  return s ? s[0].toUpperCase() + s.slice(1) : t
}

export const chipLabel = (c: Citation) => {
  const t = prettyTitle(c.source_title)
  return c.page ? `${t} · p.${c.page}` : c.date ? `${t} · ${fmtDate(c.date)}` : t
}

/** A clickable link to the record. Unverified citations are dashed amber and say so. */
export function SourceChip({ citation: c, onOpen, compact = false }: {
  citation: Citation
  onOpen?: (c: Citation) => void
  compact?: boolean
}) {
  const label = compact ? shortLabel(c) : chipLabel(c)
  const width = compact ? 'max-w-[11rem]' : 'max-w-[15rem] sm:max-w-[22rem]'
  const base = width + ' inline-flex min-w-0 items-center gap-1 rounded-full px-2 py-0.5 text-[11px] font-medium align-middle transition-colors focus-visible:outline-2 focus-visible:outline-offset-1 focus-visible:outline-brand-500'
  const title = `${c.source_title}${c.page ? ` p.${c.page}` : ''}
“${c.quote}”${c.verified ? '' : ' — not found verbatim in the source; verify before relying on it'}`
  return c.verified ? (
    <button type="button" title={title} onClick={() => onOpen?.(c)}
      className={`${base} cursor-pointer bg-brand-50 text-brand-700 hover:bg-brand-100`}>
      <DocIcon />
      <span className="truncate">{label}</span>
    </button>
  ) : (
    <button type="button" title={title} onClick={() => onOpen?.(c)}
      className={`${base} cursor-pointer border border-dashed border-warn-600 bg-warn-50 text-warn-700 hover:bg-warn-200/40`}>
      <span className="truncate">{label}</span>
      <span className="shrink-0 text-[9.5px] font-semibold uppercase tracking-wide">unverified</span>
    </button>
  )
}

/** Compact chip text: page, else date, else a short title. The full title is on hover and in the source pane. */
function shortLabel(c: Citation) {
  if (c.page) return `p.${c.page}`
  if (c.date) return fmtDate(c.date, true)
  return prettyTitle(c.source_title)
}

export function SourceChips({ citations, onOpen, max = 3, showMore = true, compact = false }: {
  citations: Citation[]
  onOpen?: (c: Citation) => void
  max?: number
  showMore?: boolean
  /** Short "p.4" chips; "+N" expands in place. */
  compact?: boolean
}) {
  const [all, setAll] = useState(false)
  if (!citations.length) return null
  const shown = all ? citations : citations.slice(0, max)
  const more = citations.length - shown.length
  return (
    <span className="inline-flex max-w-full min-w-0 flex-wrap items-center gap-1">
      {shown.map((c, i) => <SourceChip key={`${c.source_id}-${i}`} citation={c} onOpen={onOpen} compact={compact} />)}
      {showMore && more > 0 && (
        <button type="button" onClick={() => setAll(true)} title={`Show ${more} more source${more === 1 ? '' : 's'}`}
          className="cursor-pointer rounded-full px-1 text-[11px] font-medium text-slate-400 hover:bg-slate-100 hover:text-slate-600">+{more}</button>
      )}
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
