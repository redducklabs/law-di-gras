// Data loading + loading/empty/error states around CaseBrief. Integration mounts this at "/".
import { useCallback, useEffect, useState } from 'react'
import { ApiError, api } from '../api/client'
import type { Citation, Dashboard, MatterSummary } from '../api/types'
import { Card, Fonts, Skeleton } from '../components'
import { CaseBrief } from './CaseBrief'

type State =
  | { kind: 'loading' }
  | { kind: 'empty'; matter: MatterSummary | null }
  | { kind: 'digesting'; matter: MatterSummary }
  | { kind: 'error'; message: string }
  | { kind: 'ready'; data: Dashboard }

export function FirmPage({ matterId, onOpenSource, onShare, onSearch, focusDate }: {
  matterId?: string
  onOpenSource?: (c: Citation) => void
  onShare?: (data: Dashboard) => void
  onSearch?: (q: string, data: Dashboard) => void
  /** Zoom the timeline to this date (chat deeplinks). */
  focusDate?: string | null
}) {
  const [state, setState] = useState<State>({ kind: 'loading' })

  const load = useCallback(async () => {
    setState({ kind: 'loading' })
    try {
      const matters = await api.matters()
      const matter = matters.find(m => m.id === matterId) ?? matters[0] ?? null
      if (!matter) return setState({ kind: 'empty', matter: null })
      try {
        setState({ kind: 'ready', data: await api.dashboard(matter.id) })
      } catch (e) {
        if (e instanceof ApiError && e.status === 404) setState({ kind: 'empty', matter })
        else throw e
      }
    } catch (e) {
      setState({ kind: 'error', message: e instanceof Error ? e.message : String(e) })
    }
  }, [matterId])

  const digest = useCallback(async (matter: MatterSummary, force = false) => {
    setState({ kind: 'digesting', matter })
    try { setState({ kind: 'ready', data: await api.digest(matter.id, force) }) }
    catch (e) { setState({ kind: 'error', message: e instanceof Error ? e.message : String(e) }) }
  }, [])

  useEffect(() => { load() }, [load])

  if (state.kind === 'ready') {
    const d = state.data
    return (
      <CaseBrief data={d} onOpenSource={onOpenSource} focusDate={focusDate}
        onShare={onShare && (() => onShare(d))}
        onSearch={onSearch && (q => onSearch(q, d))}
        onRefresh={() => digest(d.matter, true)} />
    )
  }
  if (state.kind === 'loading') return <BriefSkeleton />
  return (
    <div className="grid min-h-screen place-items-center bg-page px-4">
      <Fonts />
      <Card className="w-full max-w-md text-center">
        {state.kind === 'digesting' && (
          <>
            <Spinner />
            <h1 className="mt-3 text-[16px] font-semibold">Reading the case file…</h1>
            <p className="mt-1 text-[13px] text-slate-500">
              Pulling facts from {state.matter.title || state.matter.display_number} and checking every quote against its source. This runs once; the brief is cached after.
            </p>
          </>
        )}
        {state.kind === 'empty' && (
          <>
            <h1 className="text-[16px] font-semibold">{state.matter ? 'No brief yet for this matter' : 'No matter synced yet'}</h1>
            <p className="mt-1 text-[13px] text-slate-500">
              {state.matter ? 'Digest the case file to build the brief. Every fact will link to its source.' : 'Sync the matter from Clio first.'}
            </p>
            {state.matter && (
              <button type="button" onClick={() => digest(state.matter!)}
                className="mt-4 cursor-pointer rounded-lg bg-brand-700 px-4 py-2 text-[13px] font-semibold text-white hover:bg-brand-800">
                Build case brief
              </button>
            )}
          </>
        )}
        {state.kind === 'error' && (
          <>
            <h1 className="text-[16px] font-semibold text-danger-700">Couldn’t load the case brief</h1>
            <p className="mt-1 break-words text-[12.5px] text-slate-500">{state.message.slice(0, 300)}</p>
            <button type="button" onClick={load}
              className="mt-4 cursor-pointer rounded-lg border border-line px-4 py-2 text-[13px] font-semibold hover:bg-page">Try again</button>
          </>
        )}
      </Card>
    </div>
  )
}

function Spinner() {
  return <div className="mx-auto h-8 w-8 animate-spin rounded-full border-[3px] border-brand-100 border-t-brand-600" />
}

function BriefSkeleton() {
  return (
    <div className="min-h-screen bg-page">
      <Fonts />
      <div className="mx-auto max-w-[1280px] px-4 py-5 sm:px-8 sm:py-6">
        <div className="mb-5 flex items-center gap-3.5">
          <Skeleton className="h-12 w-12 rounded-full" />
          <div className="space-y-2"><Skeleton className="h-5 w-48" /><Skeleton className="h-3.5 w-72" /></div>
        </div>
        <Skeleton className="h-36 w-full rounded-xl" />
        <div className="mt-5 grid grid-cols-1 gap-5 lg:grid-cols-12">
          <Skeleton className="h-64 rounded-xl lg:col-span-7" />
          <Skeleton className="h-64 rounded-xl lg:col-span-5" />
        </div>
        <div className="mt-5 grid grid-cols-2 gap-5 lg:grid-cols-4">
          {[0, 1, 2, 3].map(i => <Skeleton key={i} className="h-32 rounded-xl" />)}
        </div>
      </div>
    </div>
  )
}
