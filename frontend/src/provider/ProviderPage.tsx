// Provider page at /p/:token. Everything shown is already filtered server-side.
import { useState } from 'react'
import { useParams } from 'react-router-dom'
import DocViewer, { type OpenedDoc } from './DocViewer'
import ProviderViewBody from './ProviderViewBody'
import { shareApi, useProviderView } from './api'

export default function ProviderPage() {
  const { token } = useParams()
  const { view, error, loading } = useProviderView(token)
  const [doc, setDoc] = useState<OpenedDoc | null>(null)

  return (
    <div className="min-h-screen bg-slate-50">
      <div className="mx-auto max-w-4xl px-4 py-8 sm:px-6">
        {loading && (
          <div className="space-y-3">
            <div className="h-8 w-64 animate-pulse rounded bg-slate-200" />
            <div className="h-28 animate-pulse rounded-lg bg-slate-200" />
            <div className="h-40 animate-pulse rounded-lg bg-slate-200" />
          </div>
        )}
        {error && (
          <div className="rounded-lg border border-slate-200 bg-white p-8 text-center">
            <h1 className="text-lg font-semibold text-slate-900">
              {error === 'notfound' ? 'This link is no longer active' : 'Could not load this case update'}
            </h1>
            <p className="mt-1 text-sm text-slate-500">Contact the law firm for a new link.</p>
          </div>
        )}
        {view && token && (
          <>
            <ProviderViewBody
              view={view}
              onOpenDoc={(id, title, page) => setDoc({ url: shareApi.sharedFileUrl(token, id), title, page })}
            />
            <p className="mt-8 text-center text-xs text-slate-400">
              Shared by the firm handling your patient's injury claim. Contents are limited to what the attorney chose to share.
            </p>
          </>
        )}
      </div>
      <DocViewer doc={doc} onClose={() => setDoc(null)} />
    </div>
  )
}
