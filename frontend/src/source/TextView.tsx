// Notes, emails, tasks, calendar entries, expenses: full text with the cited span marked.
import { useEffect, useRef } from 'react'
import type { Citation, SourceDetail } from '../api/types'
import { Badge, fmtDate, prettyTitle } from '../components'
import { KIND_LABEL, MetaRow, Notice, QuoteBlock } from './parts'
import { decodeEntities as d, resolveSpan } from './text'

export function TextView({ source, citation }: { source: SourceDetail; citation: Citation }) {
  const text = source.text ?? ''
  const span = resolveSpan(text, citation.quote, citation.char_start, citation.char_end)
  const mark = useRef<HTMLElement>(null)

  useEffect(() => {
    requestAnimationFrame(() => mark.current?.scrollIntoView({ block: 'center', behavior: 'smooth' }))
  }, [source.id, span?.[0], span?.[1]])

  return (
    <div className="space-y-3.5 p-5">
      <div>
        <MetaRow items={[
          <Badge key="k" tone="brand">{KIND_LABEL[source.kind]}</Badge>,
          source.date ? fmtDate(source.date, true) : null,
          source.author,
        ]} />
        <h3 className="mt-2 text-[15px] font-semibold leading-snug text-slate-900">{prettyTitle(source.title)}</h3>
      </div>

      {!citation.verified && <QuoteBlock citation={citation} />}
      {citation.verified && !span && (
        <Notice tone="warn">The cited words could not be located in this record's current text. Quote: “{citation.quote}”</Notice>
      )}
      {source.has_file && <Notice>This record also has an attached file; the text below is its extracted content.</Notice>}

      <article className="whitespace-pre-wrap break-words rounded-lg border border-line bg-page px-4 py-3.5 font-sans text-[13px] leading-relaxed text-slate-700">
        {span ? (
          <>
            {d(text.slice(0, span[0]))}
            <mark ref={mark}
              className={`rounded-[3px] px-0.5 text-slate-900 ${citation.verified ? 'bg-yellow-200 ring-1 ring-yellow-400/70' : 'bg-warn-50 ring-1 ring-warn-600'}`}>
              {d(text.slice(span[0], span[1]))}
            </mark>
            {d(text.slice(span[1]))}
          </>
        ) : d(text) || <span className="text-slate-400">This record has no text.</span>}
      </article>
    </div>
  )
}
