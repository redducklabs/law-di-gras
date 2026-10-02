// Case stage stepper.

/** Canonical PI stages. The digest's `stage` is matched against these (case-insensitive). */
export const STAGES = ['Intake', 'Treating', 'Pre-demand', 'Demand', 'Negotiation', 'Litigation', 'Resolved']

// Free-text stages the digest may emit → stepper index. First matching keyword wins.
const STAGE_ALIASES: [RegExp, number][] = [
  [/settle|resolv|closed|disburs/, 6],
  [/litigat|suit|filed|discovery|trial|deposition/, 5],
  [/negotiat|offer|mediat/, 4],
  [/demand sent|demand served|demand out/, 3],
  [/pre-?demand|demand prep|treatment complete|records|demand/, 2],
  [/treat|medical/, 1],
  [/intake|new|investigat|sign/, 0],
]

export function stageIndex(stage: string) {
  const s = stage.trim().toLowerCase()
  const exact = STAGES.findIndex(x => x.toLowerCase() === s)
  if (exact >= 0) return exact
  return STAGE_ALIASES.find(([re]) => re.test(s))?.[1] ?? -1
}

export function StageStepper({ stage }: { stage: string }) {
  const cur = stageIndex(stage)
  return (
    <>
      <ol className="hidden items-start gap-1 sm:flex" aria-label="Case stage">
        {STAGES.map((s, i) => (
          <li key={s} className="flex flex-1 flex-col gap-1.5" aria-current={i === cur ? 'step' : undefined}>
            <div className={`h-1.5 rounded-full ${i <= cur ? 'bg-brand-500' : 'bg-line'} ${i === cur ? 'ring-4 ring-brand-500/15' : ''}`} />
            <span className={`text-[11px] ${i === cur ? 'font-semibold text-brand-700' : i < cur ? 'text-slate-600' : 'text-slate-400'}`}>{s}</span>
          </li>
        ))}
      </ol>
      <div className="sm:hidden">
        <div className="flex items-baseline justify-between text-[12px]">
          <span className="font-semibold text-brand-700">{stage}</span>
          {cur >= 0 && <span className="text-slate-400">Stage {cur + 1} of {STAGES.length}</span>}
        </div>
        <div className="mt-1.5 h-1.5 rounded-full bg-line">
          <div className="h-1.5 rounded-full bg-brand-500" style={{ width: `${((cur + 1) / STAGES.length) * 100}%` }} />
        </div>
      </div>
    </>
  )
}
