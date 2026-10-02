// The four case numbers as one quiet strip under the status line. One color: unverified values turn amber.
import type { ReactNode } from 'react'
import type { Citation, Dashboard, Fact } from '../api/types'
import { SourceChips, money } from '../components'

export function KpiStrip({ data: d, onOpenSource }: { data: Dashboard; onOpenSource?: (c: Citation) => void }) {
  const k = d.kpis
  const cov = k.coverage
  return (
    <div className="grid grid-cols-2 overflow-hidden rounded-xl border border-line bg-line shadow-card [gap:1px] lg:grid-cols-4">
      <Cell fact={k.case_value} label="Case value (draft)" sub="Draft range · attorney review" onOpen={onOpenSource} />
      <Cell fact={cov[0]} label="Coverage / policy limits" onOpen={onOpenSource}
        sub={cov.length > 1 ? `+${cov.length - 1} more polic${cov.length > 2 ? 'ies' : 'y'}` : undefined} />
      <Cell fact={k.specials} label="Medical specials" sub={liensSub(k.liens)} onOpen={onOpenSource} />
      <Cell fact={k.firm_spent} label="Firm costs advanced" onOpen={onOpenSource} />
    </div>
  )
}

function Cell({ fact, label, sub, onOpen }: { fact?: Fact | null; label: string; sub?: ReactNode; onOpen?: (c: Citation) => void }) {
  const v = fact?.value ?? ''
  const size = v.length <= 14 ? 'text-[20px]' : v.length <= 28 ? 'text-[16px]' : 'text-[13.5px] leading-snug'
  return (
    <div className="flex min-w-0 flex-col bg-surface px-4 py-3">
      <div className="truncate text-[12px] text-slate-500" title={fact?.label ?? label}>{label}</div>
      {fact ? (
        <>
          <div title={v} className={`mt-0.5 line-clamp-2 font-semibold tracking-tight tabular-nums ${size} ${fact.verified ? 'text-slate-900' : 'text-warn-700'}`}>{v}</div>
          <div className="mt-auto flex min-w-0 flex-wrap items-center gap-x-2 gap-y-1 pt-1">
            {sub && <span className="truncate text-[11.5px] text-slate-500">{sub}</span>}
            <SourceChips citations={fact.citations} onOpen={onOpen} max={1} compact />
          </div>
        </>
      ) : (
        <div className="mt-0.5 text-[13px] text-slate-400">Not found in the record</div>
      )}
    </div>
  )
}

function liensSub(liens?: Fact[]) {
  if (!liens?.length) return undefined
  const total = liens.reduce((s, f) => s + (f.amount ?? 0), 0)
  return `${liens.length} lien${liens.length === 1 ? '' : 's'}${total ? ` · ${money(total)}` : ''}`
}
