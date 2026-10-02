// "Ask the case": right-docked, multi-turn chat over the record. Owned by S5.
// Answers cite [n] → citation chips; deeplinks render as action buttons that
// App.tsx resolves (scroll to a section, focus the timeline, open share, …).
import { useEffect, useRef, useState, type CSSProperties, type FormEvent, type KeyboardEvent } from 'react'
import type { ChatResponse, ChatTurn, Citation, DeepLink } from '../api/types'
import { ApiError, api } from '../api/client'
import { SourceChip } from '../components'
import { AnswerMarkdown } from '../source/AnswerMarkdown'
import { chatMockEnabled, mockChat } from './mock'

export interface ChatPanelProps {
  matterId: string
  open: boolean
  onClose: () => void
  onOpenCitation: (c: Citation) => void
  onNavigate: (link: DeepLink) => void
}

type Msg =
  | { role: 'user'; content: string }
  | { role: 'assistant'; content: string; response: ChatResponse }
  | { role: 'error'; content: string }

const STARTERS = ["What's overdue?", 'What coverage is there?', 'When did we last talk to the client?']

export function ChatPanel({ matterId, open, onClose, onOpenCitation, onNavigate }: ChatPanelProps) {
  const [msgs, setMsgs] = useState<Msg[]>([])
  const [draft, setDraft] = useState('')
  const [busy, setBusy] = useState(false)
  const [unavailable, setUnavailable] = useState(false)
  const list = useRef<HTMLDivElement>(null)
  const input = useRef<HTMLTextAreaElement>(null)

  useEffect(() => { if (open) setTimeout(() => input.current?.focus(), 150) }, [open])
  useEffect(() => { setMsgs([]); setUnavailable(false) }, [matterId])
  useEffect(() => {
    const el = list.current
    if (el) requestAnimationFrame(() => el.scrollTo({ top: el.scrollHeight, behavior: 'smooth' }))
  }, [msgs, busy])

  const send = async (text: string) => {
    const q = text.trim()
    if (!q || busy || !matterId) return
    const history: ChatTurn[] = [
      ...msgs.flatMap(m => m.role === 'error' ? [] : [{ role: m.role, content: m.content } as ChatTurn]),
      { role: 'user', content: q },
    ]
    setMsgs(m => [...m, { role: 'user', content: q }])
    setDraft('')
    setBusy(true)
    try {
      const r = chatMockEnabled() ? await mockChat(matterId, { messages: history }) : await api.chat(matterId, { messages: history })
      setUnavailable(false)
      setMsgs(m => [...m, { role: 'assistant', content: r.answer_markdown, response: r }])
    } catch (e) {
      console.error('chat failed', e)
      const notYet = e instanceof ApiError && e.status === 404
      if (notYet) setUnavailable(true)
      setMsgs(m => [...m, {
        role: 'error',
        content: notYet ? 'Chat not available yet. Use Find in case for cited passages in the meantime.'
          : 'Could not answer right now. Try again in a moment.',
      }])
    } finally { setBusy(false) }
  }

  const onSubmit = (e: FormEvent) => { e.preventDefault(); send(draft) }
  const onKey = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send(draft) }
  }

  return (
    <aside aria-label="Ask the case" aria-hidden={!open}
      className={`fixed inset-y-0 right-0 z-40 flex w-full max-w-[420px] flex-col border-l border-line bg-surface shadow-pop transition-transform duration-200 ease-out ${open ? 'translate-x-0' : 'pointer-events-none translate-x-full'}`}>
      <header className="flex items-start justify-between gap-3 border-b border-line px-5 py-4">
        <div className="min-w-0">
          <h2 className="flex items-center gap-2 text-[15px] font-semibold text-slate-900">
            <ChatIcon /> Ask the case
          </h2>
          <div className="mt-0.5 text-[12px] text-slate-500">Draft for attorney review · cited answers only</div>
        </div>
        <div className="flex shrink-0 items-center gap-1">
          {msgs.length > 0 && (
            <button type="button" onClick={() => setMsgs([])} disabled={busy}
              className="cursor-pointer rounded-lg px-2 py-1.5 text-[12px] font-medium text-slate-500 hover:bg-slate-100 hover:text-slate-900 disabled:opacity-40">
              New chat
            </button>
          )}
          <button type="button" onClick={onClose} aria-label="Close"
            className="grid h-8 w-8 cursor-pointer place-items-center rounded-lg text-slate-500 hover:bg-slate-100 hover:text-slate-900">
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.8"><path d="M4 4l8 8M12 4l-8 8" /></svg>
          </button>
        </div>
      </header>

      <div ref={list} className="min-h-0 flex-1 space-y-4 overflow-y-auto px-5 py-4">
        {msgs.length === 0 && (
          <div className="pt-2">
            <p className="text-[13px] leading-relaxed text-slate-600">
              Ask about this matter in plain words. Every answer cites the record, and links take you to the part of the brief it comes from.
            </p>
            <div className="mt-4 text-[10.5px] font-semibold uppercase tracking-wide text-slate-500">Try</div>
            <div className="mt-2 flex flex-col items-start gap-2">
              {STARTERS.map(s => (
                <button key={s} type="button" onClick={() => send(s)} disabled={busy || !matterId}
                  className="cursor-pointer rounded-full border border-brand-200 bg-brand-50/60 px-3 py-1.5 text-[12.5px] font-medium text-brand-700 hover:bg-brand-100 disabled:opacity-50">
                  {s}
                </button>
              ))}
            </div>
          </div>
        )}

        {msgs.map((m, i) => m.role === 'user' ? (
          <div key={i} className="flex justify-end">
            <div className="max-w-[85%] rounded-2xl rounded-br-md bg-brand-600 px-3.5 py-2 text-[13px] leading-relaxed whitespace-pre-wrap text-white">{m.content}</div>
          </div>
        ) : m.role === 'error' ? (
          <div key={i} className="rounded-lg border border-warn-200 bg-warn-50 px-3.5 py-2.5 text-[12.5px] text-warn-700">{m.content}</div>
        ) : (
          <AssistantMessage key={i} r={m.response} onOpenCitation={onOpenCitation} onNavigate={onNavigate} />
        ))}

        {busy && (
          <div className="flex items-center gap-2.5 text-[12.5px] text-slate-500">
            <span className="flex gap-1">
              {[0, 150, 300].map(d => <span key={d} style={{ animationDelay: `${d}ms` }} className="h-1.5 w-1.5 animate-bounce rounded-full bg-brand-500" />)}
            </span>
            Reading the record…
          </div>
        )}
      </div>

      <form onSubmit={onSubmit} className="border-t border-line px-4 py-3">
        <div className="flex items-end gap-2 rounded-xl border border-line bg-page px-3 py-2 focus-within:border-brand-500 focus-within:bg-surface">
          <textarea ref={input} rows={1} value={draft} onChange={e => setDraft(e.target.value)} onKeyDown={onKey}
            placeholder={unavailable ? 'Chat not available yet' : 'Ask about this case…'}
            className="max-h-32 min-h-[22px] flex-1 resize-none bg-transparent text-[13px] leading-relaxed text-slate-900 placeholder:text-slate-400 focus:outline-none"
            style={{ fieldSizing: 'content' } as CSSProperties} />
          <button type="submit" disabled={busy || !draft.trim() || !matterId} aria-label="Send"
            className="grid h-7 w-7 shrink-0 cursor-pointer place-items-center rounded-lg bg-brand-600 text-white hover:bg-brand-700 disabled:cursor-default disabled:opacity-40">
            <svg width="13" height="13" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="2"><path d="M8 13V3M3.5 7.5L8 3l4.5 4.5" /></svg>
          </button>
        </div>
        <div className="mt-1.5 px-1 text-[10.5px] text-slate-400">Enter to send · Shift+Enter for a new line</div>
      </form>
    </aside>
  )
}

function AssistantMessage({ r, onOpenCitation, onNavigate }: {
  r: ChatResponse
  onOpenCitation: (c: Citation) => void
  onNavigate: (link: DeepLink) => void
}) {
  return (
    <div className="space-y-2.5">
      <AnswerMarkdown markdown={r.answer_markdown} citations={r.citations} onOpen={onOpenCitation} />
      {r.citations.length > 0 && (
        <div className="flex flex-wrap items-center gap-1.5">
          {r.citations.map((c, i) => (
            <span key={i} className="inline-flex min-w-0 items-center gap-1 text-[11px] text-slate-400">
              <span className="tabular-nums">{i + 1}</span>
              <SourceChip citation={c} onOpen={onOpenCitation} />
            </span>
          ))}
        </div>
      )}
      {r.links.length > 0 && (
        <div className="flex flex-wrap gap-1.5 pt-0.5">
          {r.links.map((l, i) => (
            <button key={i} type="button" onClick={() => onNavigate(l)}
              className="cursor-pointer rounded-lg border border-line bg-surface px-2.5 py-1 text-[12px] font-medium text-slate-700 shadow-card hover:border-brand-200 hover:bg-brand-50 hover:text-brand-700">
              {l.label.replace(/\s*→\s*$/, '')} →
            </button>
          ))}
        </div>
      )}
    </div>
  )
}

function ChatIcon() {
  return (
    <svg width="15" height="15" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.6" className="text-brand-600" aria-hidden>
      <path d="M2.5 3.5h11v7h-6l-3 2.5v-2.5h-2z" strokeLinejoin="round" />
    </svg>
  )
}
