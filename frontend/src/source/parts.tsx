// Small presentational pieces shared by the source views.
import { useState, type ReactNode } from 'react'
import type { Citation, SourceKind } from '../api/types'
import { Badge } from '../components'

export const KIND_LABEL: Record<SourceKind, string> = {
  note: 'Note', communication: 'Email', task: 'Task', calendar_entry: 'Calendar',
  expense: 'Expense', document: 'Document', custom_field: 'Matter field', contact: 'Contact', matter: 'Matter',
}

export function MetaRow({ items }: { items: ReactNode[] }) {
  const shown = items.filter(Boolean)
  return (
    <div className="flex flex-wrap items-center gap-x-2 gap-y-1 text-[12px] text-slate-500">
      {shown.map((it, i) => (
        <span key={i} className="inline-flex items-center gap-2">
          {i > 0 && <span className="text-slate-300">·</span>}
          {it}
        </span>
      ))}
    </div>
  )
}

/** The cited words, with a clear verified / unverified state. */
export function QuoteBlock({ citation, note }: { citation: Citation; note?: ReactNode }) {
  const ok = citation.verified
  const quote = citation.quote.replace(/\s+/g, ' ').trim()
  const long = quote.length > 320
  const [open, setOpen] = useState(false)
  return (
    <figure className={`rounded-lg border-l-[3px] px-3.5 py-2.5 ${ok ? 'border-brand-500 bg-brand-50/60' : 'border-warn-600 bg-warn-50'}`}>
      <figcaption className="mb-1 flex flex-wrap items-center gap-2 text-[10.5px] font-semibold uppercase tracking-wide">
        {ok
          ? <span className="text-brand-700">Cited passage</span>
          : <Badge tone="warn" className="normal-case tracking-normal">Quote not found verbatim in source</Badge>}
        {note}
      </figcaption>
      <blockquote className={`text-[13px] leading-relaxed ${ok ? 'text-slate-800' : 'text-warn-700'} ${long && !open ? 'line-clamp-3' : ''}`}>
        “{quote}”
      </blockquote>
      {long && (
        <button type="button" onClick={() => setOpen(o => !o)}
          className="mt-1 cursor-pointer text-[12px] font-medium text-brand-700 hover:underline">
          {open ? 'Show less' : 'Show full passage'}
        </button>
      )}
    </figure>
  )
}

export function Notice({ tone = 'neutral', children }: { tone?: 'neutral' | 'warn' | 'danger'; children: ReactNode }) {
  const cls = tone === 'warn' ? 'border-warn-200 bg-warn-50 text-warn-700'
    : tone === 'danger' ? 'border-danger-200 bg-danger-50 text-danger-700'
    : 'border-line bg-page text-slate-600'
  return <div className={`rounded-lg border px-3.5 py-2.5 text-[12.5px] ${cls}`}>{children}</div>
}

export function Spinner({ label }: { label: string }) {
  return (
    <div className="flex items-center gap-2.5 py-8 text-[13px] text-slate-500">
      <span className="h-4 w-4 animate-spin rounded-full border-2 border-brand-200 border-t-brand-600" />
      {label}
    </div>
  )
}

export function IconButton({ onClick, disabled, label, children }: {
  onClick: () => void; disabled?: boolean; label: string; children: ReactNode
}) {
  return (
    <button type="button" onClick={onClick} disabled={disabled} aria-label={label} title={label}
      className="grid h-7 w-7 cursor-pointer place-items-center rounded-md border border-line bg-surface text-slate-600 hover:bg-slate-50 hover:text-slate-900 disabled:cursor-default disabled:opacity-40">
      {children}
    </button>
  )
}

export const Chevron = ({ dir }: { dir: 'left' | 'right' }) => (
  <svg width="12" height="12" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden>
    <path d={dir === 'left' ? 'M10 3L5 8l5 5' : 'M6 3l5 5-5 5'} />
  </svg>
)
