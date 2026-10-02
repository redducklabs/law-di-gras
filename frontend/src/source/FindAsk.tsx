// Query mode: Ask (cited answer) + Find in case (ranked passages). Clicking opens the source.
import { Fragment, useEffect, useState, type FormEvent, type ReactNode } from 'react'
import type { Answer, Citation, Passage } from '../api/types'
import { ApiError, api } from '../api/client'
import { SourceChip, chipLabel } from '../components'
import { Notice, Spinner } from './parts'
import { queryTerms } from './text'

// Survives remounts so 'Back to results' keeps the answer and passages.
const memo: { matterId?: string; question?: string; answer?: Answer | null; passages: Record<string, Passage[]> } = { passages: {} }

export function FindAsk({ matterId, query, onOpenCitation }: {
  matterId: string
  query: string
  onOpenCitation: (c: Citation) => void
}) {
  const [q, setQ] = useState(query)
  const [draft, setDraft] = useState(query)
  const [passages, setPassages] = useState<Passage[] | null>(memo.passages[query] ?? null)
  const [searchErr, setSearchErr] = useState<string | null>(null)

  const sameMatter = memo.matterId === matterId
  const [question, setQuestion] = useState(sameMatter ? memo.question ?? '' : '')
  const [answer, setAnswer] = useState<Answer | null>(sameMatter ? memo.answer ?? null : null)
  const [asking, setAsking] = useState(false)
  const [askErr, setAskErr] = useState<string | null>(null)
  const [askAvailable, setAskAvailable] = useState(true)

  useEffect(() => { setQ(query); setDraft(query) }, [query])

  useEffect(() => {
    if (!matterId || !q.trim()) return
    let live = true
    setSearchErr(null)
    if (memo.passages[q]) { setPassages(memo.passages[q]); return }
    setPassages(null)
    api.search(matterId, q).then(r => { memo.passages[q] = r; if (live) setPassages(r) })
      .catch(e => live && setSearchErr(e instanceof Error ? e.message : String(e)))
    return () => { live = false }
  }, [matterId, q])

  const submitFind = (e: FormEvent) => { e.preventDefault(); if (draft.trim()) setQ(draft.trim()) }
  const submitAsk = async (e: FormEvent) => {
    e.preventDefault()
    const text = question.trim()
    if (!text || asking) return
    setAsking(true); setAskErr(null); setAnswer(null)
    try {
      const a = await api.ask(matterId, text)
      Object.assign(memo, { matterId, question: text, answer: a })
      setAnswer(a)
    } catch (err) {
      if (err instanceof ApiError && err.status === 404) setAskAvailable(false)
      else setAskErr('Could not answer right now. Try again, or use the passages below.')
    } finally { setAsking(false) }
  }

  const terms = queryTerms(q)

  return (
    <div className="space-y-5 p-5">
      {askAvailable && (
        <section className="rounded-xl border border-line bg-surface p-4 shadow-card">
          <form onSubmit={submitAsk} className="flex gap-2">
            <input value={question} onChange={e => setQuestion(e.target.value)}
              placeholder="Ask the record a question…"
              className="min-w-0 flex-1 rounded-lg border border-line bg-page px-3 py-2 text-[13px] text-slate-900 placeholder:text-slate-400 focus:border-brand-500 focus:bg-surface focus:outline-none" />
            <button type="submit" disabled={asking || !question.trim()}
              className="shrink-0 cursor-pointer rounded-lg bg-brand-600 px-3.5 py-2 text-[13px] font-semibold text-white hover:bg-brand-700 disabled:cursor-default disabled:opacity-50">
              Ask
            </button>
          </form>
          {asking && <Spinner label="Reading the record…" />}
          {askErr && <div className="mt-3"><Notice tone="danger">{askErr}</Notice></div>}
          {answer && <AnswerView answer={answer} onOpen={onOpenCitation} />}
        </section>
      )}

      <section>
        <form onSubmit={submitFind} className="mb-3 flex items-center gap-2">
          <div className="relative min-w-0 flex-1">
            <svg className="pointer-events-none absolute top-1/2 left-3 -translate-y-1/2 text-slate-400" width="14" height="14" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.8" aria-hidden>
              <circle cx="7" cy="7" r="4.5" /><path d="M10.5 10.5L14 14" />
            </svg>
            <input value={draft} onChange={e => setDraft(e.target.value)} placeholder="Find in case"
              className="w-full rounded-lg border border-line bg-surface py-2 pr-3 pl-8 text-[13px] text-slate-900 placeholder:text-slate-400 focus:border-brand-500 focus:outline-none" />
          </div>
        </form>

        <h3 className="mb-2 text-[11px] font-semibold uppercase tracking-wide text-slate-500">
          Passages{passages ? ` · ${passages.length}` : ''}
        </h3>
        {searchErr ? <Notice tone="danger">Search failed. Is the backend running?</Notice>
          : !passages ? <Spinner label="Searching the record…" />
          : !passages.length ? <Notice>No passages match “{q}”. Try different words.</Notice>
          : (
            <ul className="space-y-2">
              {passages.map((p, i) => (
                <li key={`${p.citation.source_id}-${p.citation.page}-${i}`}>
                  <button type="button" onClick={() => onOpenCitation(p.citation)}
                    className="group block w-full cursor-pointer rounded-xl border border-line bg-surface p-3.5 text-left shadow-card transition-colors hover:border-brand-200 hover:bg-brand-50/30">
                    <div className="mb-1.5 flex items-center justify-between gap-3">
                      <span className="truncate text-[12.5px] font-semibold text-slate-900 group-hover:text-brand-700">{chipLabel(p.citation)}</span>
                      {!p.citation.verified && <span className="shrink-0 text-[10px] font-semibold uppercase text-warn-700">unverified</span>}
                    </div>
                    <p className="line-clamp-3 text-[12.5px] leading-relaxed text-slate-600">
                      <Bold text={p.snippet.replace(/\s+/g, ' ')} terms={terms} />
                    </p>
                  </button>
                </li>
              ))}
            </ul>
          )}
      </section>
    </div>
  )
}

function Bold({ text, terms }: { text: string; terms: string[] }) {
  if (!terms.length) return <>{text}</>
  const re = new RegExp(`(${terms.map(t => t.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')).join('|')})`, 'gi')
  return <>{text.split(re).map((s, i) => i % 2 ? <strong key={i} className="font-semibold text-slate-900">{s}</strong> : s)}</>
}

/** Minimal markdown: paragraphs, bullets, **bold**, and [n] citation markers as chips. */
function AnswerView({ answer, onOpen }: { answer: Answer; onOpen: (c: Citation) => void }) {
  const inline = (s: string): ReactNode[] =>
    s.split(/(\[\d+(?:\s*,\s*\d+)*\]|\*\*[^*]+\*\*)/g).map((part, i) => {
      const cite = part.match(/^\[(\d+(?:\s*,\s*\d+)*)\]$/)
      if (cite) {
        return <Fragment key={i}>{cite[1].split(/\s*,\s*/).map(n => {
          const c = answer.citations[Number(n) - 1]
          return c ? <CiteMark key={n} n={n} c={c} onOpen={onOpen} /> : <sup key={n} className="text-slate-400">[{n}]</sup>
        })}</Fragment>
      }
      if (part.startsWith('**') && part.endsWith('**')) return <strong key={i} className="font-semibold text-slate-900">{part.slice(2, -2)}</strong>
      return part
    })

  // Group lines: consecutive bullets → list, '#' lines → heading, other runs → paragraph.
  type Block = { kind: 'ul' | 'h' | 'p'; lines: string[] }
  const blocks: Block[] = []
  for (const raw of answer.answer_markdown.trim().split('\n')) {
    const line = raw.trimEnd()
    const last = blocks[blocks.length - 1]
    if (!line.trim()) { blocks.push({ kind: 'p', lines: [] }); continue }
    const bullet = line.match(/^\s*(?:[-*]|\d+\.)\s+(.*)/)
    const head = line.match(/^#+\s+(.*)/)
    if (bullet) last?.kind === 'ul' ? last.lines.push(bullet[1]) : blocks.push({ kind: 'ul', lines: [bullet[1]] })
    else if (head) blocks.push({ kind: 'h', lines: [head[1]] })
    else last?.kind === 'p' && last.lines.length ? last.lines.push(line) : blocks.push({ kind: 'p', lines: [line] })
  }
  return (
    <div className="mt-3.5 space-y-2.5 border-t border-line-soft pt-3.5 text-[13px] leading-relaxed text-slate-700">
      <div className="text-[10.5px] font-semibold uppercase tracking-wide text-slate-500">Draft answer · verify against sources</div>
      {blocks.filter(b => b.lines.length).map((b, i) =>
        b.kind === 'ul' ? <ul key={i} className="list-disc space-y-1.5 pl-5 marker:text-slate-300">{b.lines.map((l, j) => <li key={j}>{inline(l)}</li>)}</ul>
        : b.kind === 'h' ? <h4 key={i} className="pt-1 font-semibold text-slate-900">{inline(b.lines[0])}</h4>
        : <p key={i}>{inline(b.lines.join(' '))}</p>)}
      {answer.citations.length > 0 && (
        <div className="pt-1">
          <div className="mb-1.5 text-[10.5px] font-semibold uppercase tracking-wide text-slate-500">Sources</div>
          <ol className="space-y-1">
            {answer.citations.map((c, i) => (
              <li key={i} className="flex items-center gap-2 text-[12px] text-slate-500">
                <span className="w-4 shrink-0 text-right tabular-nums">{i + 1}</span>
                <SourceChip citation={c} onOpen={onOpen} />
              </li>
            ))}
          </ol>
        </div>
      )}
    </div>
  )
}

function CiteMark({ n, c, onOpen }: { n: string; c: Citation; onOpen: (c: Citation) => void }) {
  return (
    <button type="button" onClick={() => onOpen(c)} title={`${chipLabel(c)}\n“${c.quote}”`}
      className={`mx-0.5 inline-grid h-[18px] min-w-[18px] cursor-pointer place-items-center rounded-full px-1 align-[1px] text-[10.5px] font-semibold tabular-nums ${c.verified ? 'bg-brand-50 text-brand-700 hover:bg-brand-100' : 'border border-dashed border-warn-600 bg-warn-50 text-warn-700'}`}>
      {n}
    </button>
  )
}
