import type { Citation, Dashboard } from '../api/types'
import { Badge, Card, SourceChips, fmtDate, type Tone } from '../components'
import { buildNextSteps, type Step } from './stepRules'

const whyTone: Record<Tone, string> = {
  danger: 'text-danger-700', warn: 'text-warn-700', brand: 'text-brand-700', ok: 'text-ok-700', neutral: 'text-slate-500',
}
const numTone: Record<Tone, string> = {
  danger: 'bg-danger-600 text-white', warn: 'bg-warn-600 text-white', brand: 'bg-brand-600 text-white',
  ok: 'bg-ok-600 text-white', neutral: 'bg-slate-200 text-slate-600',
}

/** The "what do I do now" card. Step 1 is a hero; the rest is a numbered checklist. */
export function NextSteps({ data, onOpenSource }: { data: Dashboard; onOpenSource?: (c: Citation) => void }) {
  const steps = buildNextSteps(data)
  const todo = steps.filter(s => s.group === 'do')
  const waiting = steps.filter(s => s.group === 'waiting')
  const overdue = todo.filter(s => s.tone === 'danger').length
  const [first, ...rest] = todo

  return (
    <Card title="Next steps" className="flex h-full flex-col" extra={
      <div className="flex flex-wrap gap-1.5">
        {overdue > 0 && <Badge tone="danger">{overdue} overdue</Badge>}
        <Badge tone="brand">{todo.length} to do</Badge>
        {waiting.length > 0 && <Badge>{waiting.length} waiting</Badge>}
      </div>
    }>
      {!steps.length && (
        <div className="rounded-lg bg-ok-50 px-4 py-6 text-center text-[13.5px] text-ok-700">
          Nothing overdue, due, or outstanding in the record.
        </div>
      )}

      {first && <Hero step={first} onOpenSource={onOpenSource} />}

      {rest.length > 0 && (
        <ol className="mt-3">
          {rest.map((s, i) => <Row key={i} n={i + 2} step={s} onOpenSource={onOpenSource} />)}
        </ol>
      )}

      {waiting.length > 0 && (
        <div className="mt-4 border-t border-line-soft pt-3">
          <div className="mb-1 text-[11px] font-semibold uppercase tracking-wider text-slate-400">Waiting on others · follow up</div>
          <ul>{waiting.map((s, i) => <Row key={i} step={s} onOpenSource={onOpenSource} />)}</ul>
        </div>
      )}
    </Card>
  )
}

function Hero({ step: s, onOpenSource }: { step: Step; onOpenSource?: (c: Citation) => void }) {
  const ring = s.tone === 'danger' ? 'border-danger-200 bg-danger-50/60' : 'border-brand-200 bg-brand-50/70'
  return (
    <div className={`rounded-xl border-l-4 border ${ring} ${s.tone === 'danger' ? '!border-l-danger-600' : '!border-l-brand-600'} p-4`}>
      <div className="flex items-center gap-2 text-[11px] font-semibold uppercase tracking-wider text-slate-500">
        <span className={`grid h-5 w-5 place-items-center rounded-full text-[11px] ${numTone[s.tone]}`}>1</span>
        Do this next
      </div>
      <div className="mt-2 text-[17px] font-semibold leading-snug text-slate-900">{s.title}</div>
      <div className={`mt-1 text-[13px] font-medium ${whyTone[s.tone]}`}>
        {s.why}{s.owner && <span className="font-normal text-slate-500"> · {s.owner}</span>}
      </div>
      <div className="mt-3 flex flex-wrap items-center gap-2">
        {s.citations[0] && (
          <button type="button" onClick={() => onOpenSource?.(s.citations[0])}
            className="cursor-pointer rounded-lg bg-brand-700 px-3 py-1.5 text-[12.5px] font-semibold text-white shadow-sm hover:bg-brand-800">
            Open in record →
          </button>
        )}
        <SourceChips citations={s.citations} onOpen={onOpenSource} max={2} />
      </div>
    </div>
  )
}

function Row({ n, step: s, onOpenSource }: { n?: number; step: Step; onOpenSource?: (c: Citation) => void }) {
  return (
    <li className="flex items-start gap-3 rounded-lg px-1 py-2 hover:bg-page">
      {n != null
        ? <span className={`mt-px grid h-5 w-5 shrink-0 place-items-center rounded-full text-[11px] font-semibold ${numTone[s.tone]}`}>{n}</span>
        : <span className="mt-[7px] h-1.5 w-1.5 shrink-0 rounded-full bg-slate-300" />}
      <div className="min-w-0 flex-1">
        <div className="text-[13.5px] font-medium text-slate-900">{s.title}</div>
        <div className={`text-[12px] ${whyTone[s.tone]}`}>{s.why}{s.owner && <span className="text-slate-500"> · {s.owner}</span>}</div>
      </div>
      <div className="flex shrink-0 items-center gap-2">
        <span className="hidden sm:inline"><SourceChips citations={s.citations} onOpen={onOpenSource} max={1} /></span>
        {n != null && <span className="w-12 text-right text-[12px] tabular-nums text-slate-500">{fmtDate(s.date)}</span>}
      </div>
    </li>
  )
}
