// Editable draft for a Next step. Template by default; "Improve with AI" asks S2 for a grounded
// draft where every fact links to its source. Copy, open in the user's mail app, or save a calendar
// file. Nothing leaves the browser on its own and nothing is written to Clio.
import { Fragment, useEffect, useState } from 'react'
import type { Citation, Dashboard } from '../api/types'
import { Badge, Drawer, SourceChip, SourceChips } from '../components'
import { aiDraftText, requestAiDraft, type AiDraft, type AiDraftSegment } from './aiDraft'
import { draftFor, icsFor, mailtoHref } from './drafts'
import type { Step } from './stepRules'

type Ai = { status: 'idle' } | { status: 'loading' } | { status: 'error'; message: string } | { status: 'ready'; draft: AiDraft }

export function DraftDrawer({ step, data, onClose, onOpenSource }: {
  step: Step | null
  data: Dashboard
  onClose: () => void
  onOpenSource?: (c: Citation) => void
}) {
  const draft = step ? draftFor(step, data) : null
  const [subject, setSubject] = useState('')
  const [body, setBody] = useState('')
  const [copied, setCopied] = useState(false)
  const [ai, setAi] = useState<Ai>({ status: 'idle' })
  const [editing, setEditing] = useState(false)

  useEffect(() => {
    if (!draft) return
    setSubject(draft.subject); setBody(draft.body); setCopied(false); setAi({ status: 'idle' }); setEditing(false)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [step])

  const improve = async () => {
    if (!step || !draft) return
    setAi({ status: 'loading' }); setCopied(false)
    try {
      const d = await requestAiDraft(data.matter.id, {
        kind: step.kind, title: step.title, why: step.why, owner: step.owner, waiting_on: step.waitingOn, date: step.date,
        audience: draft.audience, source_ids: step.citations.map(c => c.source_id),
        template_subject: subject, template_body: body,
      })
      setAi({ status: 'ready', draft: d }); setSubject(d.subject); setBody(aiDraftText(d)); setEditing(false)
    } catch (e) {
      setAi({ status: 'error', message: e instanceof Error ? e.message : String(e) })
    }
  }
  const backToTemplate = () => {
    if (!draft) return
    setAi({ status: 'idle' }); setSubject(draft.subject); setBody(draft.body); setEditing(false)
  }

  const copy = async () => {
    try { await navigator.clipboard.writeText(`Subject: ${subject}\n\n${body}`); setCopied(true) } catch { /* clipboard blocked */ }
  }
  const ics = step ? icsFor(step, data) : null
  const saveIcs = () => {
    if (!ics || !step) return
    const a = document.createElement('a')
    a.href = URL.createObjectURL(new Blob([ics], { type: 'text/calendar' }))
    a.download = `${step.title.replace(/[^\w]+/g, '-').slice(0, 40)}.ics`
    a.click()
    URL.revokeObjectURL(a.href)
  }
  const aiDraft = ai.status === 'ready' ? ai.draft : null
  const btn2 = 'cursor-pointer rounded-lg border border-line px-3.5 py-2 text-[13px] font-semibold text-slate-700 hover:bg-page'

  return (
    <Drawer open={!!step} onClose={onClose} width={620}
      title={aiDraft ? `${draft?.action ?? 'Draft'} · AI` : draft?.action ?? ''}
      subtitle={step && <span>{step.title}</span>}
      footer={
        <div className="flex flex-wrap items-center gap-2">
          <button type="button" onClick={copy}
            className="cursor-pointer rounded-lg bg-brand-700 px-3.5 py-2 text-[13px] font-semibold text-white hover:bg-brand-800">
            {copied ? 'Copied ✓' : 'Copy draft'}
          </button>
          <a href={draft ? mailtoHref({ ...draft, subject, body }) : undefined} className={btn2}>Open in email</a>
          {ics && <button type="button" onClick={saveIcs} className={btn2}>Add to calendar</button>}
        </div>
      }>
      {step && draft && (
        <div className="space-y-4 px-5 py-4">
          <div className="flex flex-wrap items-center gap-2 text-[12.5px]">
            {aiDraft
              ? <Badge tone="brand"><SparkIcon /> AI draft · every fact linked · review before sending</Badge>
              : <Badge tone="warn">Draft · review before sending</Badge>}
            <span className="text-slate-500">For <b className="text-slate-800">{draft.audience}</b></span>
          </div>

          <div className={`rounded-lg px-3 py-2 text-[12.5px] ${step.tone === 'danger' ? 'bg-danger-50 text-danger-700' : 'bg-page text-slate-600'}`}>
            <span className="font-semibold">{step.why}</span>
            {step.citations.length > 0 && <span className="ml-2"><SourceChips citations={step.citations} onOpen={onOpenSource} max={2} /></span>}
          </div>

          {/* AI action row */}
          <div className="flex flex-wrap items-center gap-2">
            {ai.status !== 'ready' && (
              <button type="button" onClick={improve} disabled={ai.status === 'loading'}
                className="inline-flex cursor-pointer items-center gap-1.5 rounded-lg border border-brand-200 bg-brand-50 px-3 py-1.5 text-[12.5px] font-semibold text-brand-700 hover:bg-brand-100 disabled:cursor-wait disabled:opacity-70">
                {ai.status === 'loading' ? <Spinner /> : <SparkIcon />}
                {ai.status === 'loading' ? 'Drafting from the record…' : 'Improve with AI'}
              </button>
            )}
            {aiDraft && (
              <>
                <button type="button" onClick={() => setEditing(v => !v)} className="cursor-pointer text-[12.5px] font-semibold text-brand-700 hover:underline">
                  {editing ? 'Show sources' : 'Edit text'}
                </button>
                <span className="text-slate-300">·</span>
                <button type="button" onClick={backToTemplate} className="cursor-pointer text-[12.5px] text-slate-500 hover:underline">Back to template</button>
              </>
            )}
            {ai.status === 'error' && <span className="text-[12px] text-danger-700">{ai.message}</span>}
          </div>

          {aiDraft && aiDraft.unverified.length > 0 && (
            <div className="rounded-lg border border-dashed border-warn-600 bg-warn-50 px-3 py-2 text-[12.5px] text-warn-700">
              <div className="font-semibold">Verify before sending ({aiDraft.unverified.length})</div>
              <ul className="mt-1 list-disc pl-4">{aiDraft.unverified.map((u, i) => <li key={i}>{u}</li>)}</ul>
            </div>
          )}

          <label className="block">
            <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-400">Subject</span>
            <input value={subject} onChange={e => setSubject(e.target.value)}
              className="mt-1 w-full rounded-lg border border-line px-3 py-2 text-[13.5px] outline-none focus:border-brand-500 focus:ring-2 focus:ring-brand-500/15" />
          </label>

          <div>
            <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-400">Message</span>
            {aiDraft && !editing ? (
              <div className="mt-1 whitespace-pre-wrap rounded-lg border border-line px-3 py-2.5 text-[13.5px] leading-relaxed text-slate-800">
                {aiDraft.segments.map((s, i) => <Segment key={i} s={s} onOpenSource={onOpenSource} />)}
              </div>
            ) : (
              <textarea value={body} onChange={e => setBody(e.target.value)} rows={14}
                className="mt-1 w-full resize-y rounded-lg border border-line px-3 py-2 font-sans text-[13.5px] leading-relaxed outline-none focus:border-brand-500 focus:ring-2 focus:ring-brand-500/15" />
            )}
          </div>
          <p className="text-[11.5px] text-slate-400">
            {aiDraft ? 'Facts are linked to the record; amber text could not be verified.' : 'Fill in the [bracketed] fields.'} Nothing is sent from this app or saved to Clio.
          </p>
        </div>
      )}
    </Drawer>
  )
}

/** One AI segment: fact text gets its source chips; unverified text and "[verify: …]" bits are amber. */
function Segment({ s, onOpenSource }: { s: AiDraftSegment; onOpenSource?: (c: Citation) => void }) {
  const parts = s.text.split(/(\[verify:[^\]]*\])/gi)
  const amber = 'rounded bg-warn-50 px-0.5 text-warn-700 ring-1 ring-warn-600/40'
  return (
    <>
      <span className={s.kind === 'fact' && !s.verified ? amber : s.kind === 'fact' ? 'bg-brand-50/60' : ''}>
        {parts.map((p, i) => /^\[verify:/i.test(p)
          ? <mark key={i} className={amber}>{p}</mark>
          : <Fragment key={i}>{p}</Fragment>)}
      </span>
      {s.kind === 'fact' && s.citations.length > 0 && (
        <span className="mx-1 inline-flex gap-1 align-middle whitespace-normal">
          {s.citations.slice(0, 2).map((c, i) => <SourceChip key={i} citation={c} onOpen={onOpenSource} compact />)}
        </span>
      )}
    </>
  )
}

function SparkIcon() {
  return (
    <svg width="12" height="12" viewBox="0 0 16 16" fill="currentColor" aria-hidden>
      <path d="M8 1l1.6 4.4L14 7l-4.4 1.6L8 13l-1.6-4.4L2 7l4.4-1.6z" />
    </svg>
  )
}

function Spinner() {
  return <span className="h-3 w-3 animate-spin rounded-full border-2 border-brand-200 border-t-brand-700" />
}
