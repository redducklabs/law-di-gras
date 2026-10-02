// Attorney share panel: drawer opened from the firm header's Share button.
// Usage: <SharePanel matterId={id} open={open} onClose={() => setOpen(false)} />
import { useEffect, useState } from 'react'
import { api } from '../api/client'
import { prettyTitle } from '../components'
import type { ShareSections } from '../api/types'
import DocViewer, { type OpenedDoc } from './DocViewer'
import ProviderViewBody, { fmtDate } from './ProviderViewBody'
import { shareLink, useProviders, useShare } from './api'

const SECTIONS: { key: keyof ShareSections; label: string; hint: string }[] = [
  { key: 'status', label: 'Case status', hint: 'Stage and last activity date' },
  { key: 'coverage', label: 'Coverage', hint: 'Policy limits behind the case' },
  { key: 'requests', label: 'Requests to this office', hint: 'Open items waiting on them' },
  { key: 'treatment', label: 'Their visits and bills', hint: 'Only this provider\'s treatment' },
  { key: 'timeline', label: 'Case milestones', hint: 'Incident, treatment, legal dates; no communications' },
  { key: 'documents', label: 'Records', hint: 'Only the documents ticked below' },
]

function Toggle({ on, onChange, label }: { on: boolean; onChange: (v: boolean) => void; label: string }) {
  return (
    <button
      type="button" role="switch" aria-checked={on} aria-label={label} onClick={() => onChange(!on)}
      className={`relative h-5 w-9 shrink-0 cursor-pointer rounded-full transition-colors ${on ? 'bg-brand-600' : 'bg-slate-300'}`}
    >
      <span className={`absolute top-0.5 h-4 w-4 rounded-full bg-white shadow transition-all ${on ? 'left-4.5' : 'left-0.5'}`} />
    </button>
  )
}

export default function SharePanel({ matterId, open, onClose }: { matterId: string; open: boolean; onClose: () => void }) {
  const { providers, error: provError } = useProviders(matterId, open)
  const [contactId, setContactId] = useState<string | null>(null)
  const { settings, documents, preview, saving, error, save } = useShare(matterId, contactId)
  const [copied, setCopied] = useState(false)
  const [doc, setDoc] = useState<OpenedDoc | null>(null)

  useEffect(() => {
    if (!contactId && providers?.length) setContactId(providers[0].contact_id)
  }, [providers, contactId])
  useEffect(() => setCopied(false), [contactId])

  if (!open) return null
  const provider = providers?.find((p) => p.contact_id === contactId)

  const setSection = (key: keyof ShareSections, v: boolean) =>
    settings && save({ ...settings, sections: { ...settings.sections, [key]: v } })
  const toggleDoc = (id: string) =>
    settings && save({
      ...settings,
      source_ids: settings.source_ids.includes(id) ? settings.source_ids.filter((s) => s !== id) : [...settings.source_ids, id],
    })
  const copy = async () => {
    if (!settings) return
    const s = settings.token ? settings : await save(settings)
    if (!s?.token) return
    await navigator.clipboard.writeText(shareLink(s.token))
    setCopied(true)
  }

  return (
    <>
    <div className="fixed inset-0 z-40 flex justify-end bg-slate-900/25" onClick={onClose}>
      <aside
        className="flex h-full w-full max-w-6xl flex-col bg-page shadow-pop"
        onClick={(e) => e.stopPropagation()}
        aria-label="Share with provider"
      >
        <header className="flex items-center justify-between gap-4 border-b border-line bg-surface px-5 py-4">
          <div>
            <h2 className="text-[15px] font-semibold text-slate-900">Share with a treating provider</h2>
            <p className="text-[12.5px] text-slate-500">You choose what they see. Strategy and attorney notes are never shared.</p>
          </div>
          <button type="button" onClick={onClose} aria-label="Close" className="grid h-8 w-8 shrink-0 cursor-pointer place-items-center rounded-lg text-slate-500 hover:bg-slate-100 hover:text-slate-900"><svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.8"><path d="M4 4l8 8M12 4l-8 8" /></svg></button>
        </header>

        <div className="flex min-h-0 flex-1 flex-col md:flex-row">
          {/* Controls */}
          <div className="w-full shrink-0 space-y-6 overflow-y-auto border-line bg-surface p-5 max-md:max-h-[55vh] max-md:border-b md:w-80 md:border-r">
            <div>
              <label className="mb-1 block text-[11px] font-semibold uppercase tracking-wider text-slate-400" htmlFor="share-provider">Provider</label>
              {provError && <p className="text-sm text-red-700">Could not load providers.</p>}
              {providers && !providers.length && <p className="text-sm text-slate-500">No medical providers found on this matter.</p>}
              {!providers && !provError && <div className="h-9 animate-pulse rounded-lg bg-slate-100" />}
              {!!providers?.length && (
                <select
                  id="share-provider" value={contactId ?? ''} onChange={(e) => setContactId(e.target.value)}
                  className="w-full rounded-lg border border-line bg-surface px-2.5 py-2 text-[13.5px] text-slate-900 outline-none focus:border-brand-500 focus:ring-2 focus:ring-brand-500/15"
                >
                  {providers.map((p) => <option key={p.contact_id} value={p.contact_id}>{p.name}{p.role ? ` — ${p.role}` : ''}</option>)}
                </select>
              )}
            </div>

            {settings && (
              <>
                <div>
                  <p className="mb-2 text-[11px] font-semibold uppercase tracking-wider text-slate-400">What they can see</p>
                  <ul className="space-y-3">
                    {SECTIONS.map((s) => (
                      <li key={s.key} className="flex items-start justify-between gap-3">
                        <div>
                          <p className="text-[13.5px] font-medium text-slate-900">{s.label}</p>
                          <p className="text-[12px] text-slate-500">{s.hint}</p>
                        </div>
                        <Toggle label={s.label} on={settings.sections[s.key]} onChange={(v) => setSection(s.key, v)} />
                      </li>
                    ))}
                  </ul>
                </div>

                {settings.sections.documents && (
                  <div>
                    <p className="mb-2 text-[11px] font-semibold uppercase tracking-wider text-slate-400">Records to share</p>
                    {!documents.length && <p className="text-sm text-slate-500">No documents on this matter.</p>}
                    <ul className="max-h-64 space-y-1 overflow-y-auto">
                      {documents.map((d) => (
                        <li key={d.id}>
                          <label className="flex cursor-pointer items-start gap-2 rounded-md px-1.5 py-1.5 text-[13px] hover:bg-page">
                            <input type="checkbox" className="mt-0.5 accent-brand-600" checked={settings.source_ids.includes(d.id)} onChange={() => toggleDoc(d.id)} />
                            <span className="text-slate-800">
                              {prettyTitle(d.title ?? '')}
                              {d.suggested && <span className="ml-1.5 rounded bg-ok-50 px-1.5 py-px text-[10.5px] font-semibold text-ok-700">their records</span>}
                              {d.date && <span className="block text-xs text-slate-400">{fmtDate(d.date)}</span>}
                            </span>
                          </label>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                <div className="space-y-2 border-t border-line pt-4">
                  <button
                    type="button" onClick={copy}
                    className="w-full cursor-pointer rounded-lg bg-brand-700 px-3 py-2.5 text-[13px] font-semibold text-white shadow-sm hover:bg-brand-800"
                  >
                    {copied ? 'Link copied ✓' : 'Copy provider link'}
                  </button>
                  {settings.token && (
                    <a href={shareLink(settings.token)} target="_blank" rel="noreferrer" className="block truncate text-[12px] text-brand-700 underline">
                      {shareLink(settings.token)}
                    </a>
                  )}
                  <p className="text-xs text-slate-500">
                    {saving ? 'Saving…' : settings.token ? 'Changes apply to the link immediately.' : 'Settings save automatically.'}
                  </p>
                  <p className={`text-xs ${settings.last_viewed_at ? 'font-semibold text-ok-700' : 'text-slate-400'}`}>
                    {settings.last_viewed_at
                      ? `Opened by ${provider?.name ?? 'provider'} ${new Date(settings.last_viewed_at).toLocaleString('en-US', { month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit' })}`
                      : settings.token ? 'Not opened yet' : null}
                  </p>
                </div>
              </>
            )}
            {error && <p className="text-sm text-red-700">Something went wrong saving. Try again.</p>}
          </div>

          {/* Live preview */}
          <div className="min-h-0 flex-1 overflow-y-auto p-4 sm:p-6">
            <p className="mb-3 text-[11px] font-semibold uppercase tracking-wider text-slate-400">Preview: what {provider?.name ?? 'the provider'} sees</p>
            <div className="rounded-2xl border border-dashed border-brand-200 bg-page p-4 sm:p-5">
              {preview
                ? <ProviderViewBody view={preview} compact onOpenDoc={(id, title, page) => setDoc({ url: api.sourceFileUrl(id), title, page })} />
                : <div className="space-y-3"><div className="h-6 w-48 animate-pulse rounded-md bg-slate-200/70" /><div className="h-24 animate-pulse rounded-md bg-slate-200/70" /></div>}
            </div>
          </div>
        </div>
      </aside>
    </div>
    <DocViewer doc={doc} onClose={() => setDoc(null)} />
    </>
  )
}
