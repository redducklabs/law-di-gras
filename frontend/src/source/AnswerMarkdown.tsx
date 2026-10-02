// Cited answer rendering shared by Ask (source pane) and Ask the case (chat).
// Minimal markdown: paragraphs, bullets, headings, **bold**, and [n] markers as citation chips.
import { Fragment, type ReactNode } from 'react'
import type { Citation } from '../api/types'
import { SourceChip, chipLabel } from '../components'

export function AnswerMarkdown({ markdown, citations, onOpen }: {
  markdown: string
  citations: Citation[]
  onOpen: (c: Citation) => void
}) {
  const inline = (s: string): ReactNode[] =>
    s.split(/(\[\d+(?:\s*,\s*\d+)*\]|\*\*[^*]+\*\*)/g).map((part, i) => {
      const cite = part.match(/^\[(\d+(?:\s*,\s*\d+)*)\]$/)
      if (cite) {
        return <Fragment key={i}>{cite[1].split(/\s*,\s*/).map(n => {
          const c = citations[Number(n) - 1]
          return c ? <CiteMark key={n} n={n} c={c} onOpen={onOpen} /> : <sup key={n} className="text-slate-400">[{n}]</sup>
        })}</Fragment>
      }
      if (part.startsWith('**') && part.endsWith('**')) return <strong key={i} className="font-semibold text-slate-900">{part.slice(2, -2)}</strong>
      return part
    })

  // Group lines: consecutive bullets → list, '#' lines → heading, other runs → paragraph.
  type Block = { kind: 'ul' | 'h' | 'p'; lines: string[] }
  const blocks: Block[] = []
  for (const raw of markdown.trim().split('\n')) {
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
    <div className="space-y-2.5 text-[13px] leading-relaxed text-slate-700">
      {blocks.filter(b => b.lines.length).map((b, i) =>
        b.kind === 'ul' ? <ul key={i} className="list-disc space-y-1.5 pl-5 marker:text-slate-300">{b.lines.map((l, j) => <li key={j}>{inline(l)}</li>)}</ul>
        : b.kind === 'h' ? <h4 key={i} className="pt-1 font-semibold text-slate-900">{inline(b.lines[0])}</h4>
        : <p key={i}>{inline(b.lines.join(' '))}</p>)}
    </div>
  )
}

export function SourcesList({ citations, onOpen }: { citations: Citation[]; onOpen: (c: Citation) => void }) {
  if (!citations.length) return null
  return (
    <div className="pt-1">
      <div className="mb-1.5 text-[10.5px] font-semibold uppercase tracking-wide text-slate-500">Sources</div>
      <ol className="space-y-1">
        {citations.map((c, i) => (
          <li key={i} className="flex min-w-0 items-center gap-2 text-[12px] text-slate-500">
            <span className="w-4 shrink-0 text-right tabular-nums">{i + 1}</span>
            <SourceChip citation={c} onOpen={onOpen} />
          </li>
        ))}
      </ol>
    </div>
  )
}

export function CiteMark({ n, c, onOpen }: { n: string; c: Citation; onOpen: (c: Citation) => void }) {
  return (
    <button type="button" onClick={() => onOpen(c)} title={`${chipLabel(c)}\n“${c.quote}”`}
      className={`mx-0.5 inline-grid h-[18px] min-w-[18px] cursor-pointer place-items-center rounded-full px-1 align-[1px] text-[10.5px] font-semibold tabular-nums ${c.verified ? 'bg-brand-50 text-brand-700 hover:bg-brand-100' : 'border border-dashed border-warn-600 bg-warn-50 text-warn-700'}`}>
      {n}
    </button>
  )
}
