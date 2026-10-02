// Editable draft for a Next step. Copy, open in the user's mail app, or save a calendar file.
// Nothing leaves the browser on its own and nothing is written to Clio.
import { useEffect, useState } from 'react'
import type { Citation, Dashboard } from '../api/types'
import { Badge, Drawer, SourceChips } from '../components'
import { draftFor, icsFor, mailtoHref } from './drafts'
import type { Step } from './stepRules'

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

  useEffect(() => {
    if (!draft) return
    setSubject(draft.subject); setBody(draft.body); setCopied(false)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [step])

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

  return (
    <Drawer open={!!step} onClose={onClose} width={600}
      title={draft?.action ?? ''}
      subtitle={step && <span>{step.title}</span>}
      footer={
        <div className="flex flex-wrap items-center gap-2">
          <button type="button" onClick={copy}
            className="cursor-pointer rounded-lg bg-brand-700 px-3.5 py-2 text-[13px] font-semibold text-white hover:bg-brand-800">
            {copied ? 'Copied ✓' : 'Copy draft'}
          </button>
          <a href={draft ? mailtoHref({ ...draft, subject, body }) : undefined}
            className="rounded-lg border border-line px-3.5 py-2 text-[13px] font-semibold text-slate-700 hover:bg-page">
            Open in email
          </a>
          {ics && (
            <button type="button" onClick={saveIcs}
              className="cursor-pointer rounded-lg border border-line px-3.5 py-2 text-[13px] font-semibold text-slate-700 hover:bg-page">
              Add to calendar
            </button>
          )}
        </div>
      }>
      {step && draft && (
        <div className="space-y-4 px-5 py-4">
          <div className="flex flex-wrap items-center gap-2 text-[12.5px]">
            <Badge tone="warn">Draft · review before sending</Badge>
            <span className="text-slate-500">For <b className="text-slate-800">{draft.audience}</b></span>
          </div>
          <div className={`rounded-lg px-3 py-2 text-[12.5px] ${step.tone === 'danger' ? 'bg-danger-50 text-danger-700' : 'bg-page text-slate-600'}`}>
            <span className="font-semibold">{step.why}</span>
            {step.citations.length > 0 && <span className="ml-2"><SourceChips citations={step.citations} onOpen={onOpenSource} max={2} /></span>}
          </div>
          <label className="block">
            <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-400">Subject</span>
            <input value={subject} onChange={e => setSubject(e.target.value)}
              className="mt-1 w-full rounded-lg border border-line px-3 py-2 text-[13.5px] outline-none focus:border-brand-500 focus:ring-2 focus:ring-brand-500/15" />
          </label>
          <label className="block">
            <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-400">Message</span>
            <textarea value={body} onChange={e => setBody(e.target.value)} rows={14}
              className="mt-1 w-full resize-y rounded-lg border border-line px-3 py-2 font-sans text-[13.5px] leading-relaxed outline-none focus:border-brand-500 focus:ring-2 focus:ring-brand-500/15" />
          </label>
          <p className="text-[11.5px] text-slate-400">Fill in the [bracketed] fields. Nothing is sent from this app or saved to Clio.</p>
        </div>
      )}
    </Drawer>
  )
}
