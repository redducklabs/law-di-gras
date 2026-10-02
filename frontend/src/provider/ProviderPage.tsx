// Provider page at /p/:token. Everything shown is already filtered server-side.
import { useState } from 'react'
import { useParams } from 'react-router-dom'
import { Card, Fonts, Skeleton } from '../components'
import DocViewer, { type OpenedDoc } from './DocViewer'
import ProviderViewBody from './ProviderViewBody'
import { shareApi, useProviderView } from './api'

export default function ProviderPage() {
  const { token } = useParams()
  const { view, error, loading } = useProviderView(token)
  const [doc, setDoc] = useState<OpenedDoc | null>(null)

  return (
    <div className="min-h-screen bg-page text-slate-900">
      <Fonts />
      <div className="border-b border-line bg-surface">
        <div className="mx-auto flex max-w-4xl items-center gap-2 px-4 py-3 text-[12px] text-slate-500 sm:px-6">
          <svg width="14" height="14" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.6" className="text-ok-600" aria-hidden>
            <rect x="3" y="7" width="10" height="7" rx="1.5" /><path d="M5.5 7V5a2.5 2.5 0 015 0v2" />
          </svg>
          Private case update · shared by the patient's attorney
        </div>
      </div>
      <div className="mx-auto max-w-4xl px-4 py-6 sm:px-6 sm:py-8">
        {loading && (
          <div className="space-y-4">
            <Skeleton className="h-4 w-40" />
            <Skeleton className="h-8 w-72" />
            <div className="grid gap-3 sm:grid-cols-2"><Skeleton className="h-36 rounded-xl" /><Skeleton className="h-36 rounded-xl" /></div>
            <Skeleton className="h-40 rounded-xl" />
          </div>
        )}
        {error && (
          <Card className="mx-auto max-w-md text-center">
            <h1 className="text-[16px] font-semibold">
              {error === 'notfound' ? 'This link is no longer active' : 'Could not load this case update'}
            </h1>
            <p className="mt-1 text-[13px] text-slate-500">Contact the law firm for a new link.</p>
          </Card>
        )}
        {view && token && (
          <>
            <ProviderViewBody
              view={view}
              onOpenDoc={(id, title, page) => setDoc({ url: shareApi.sharedFileUrl(token, id), title, page })}
            />
            <p className="mt-8 text-center text-[11.5px] text-slate-400">
              Contents are limited to what the attorney chose to share. Questions? Reply to the firm directly.
            </p>
          </>
        )}
      </div>
      <DocViewer doc={doc} onClose={() => setDoc(null)} />
    </div>
  )
}
