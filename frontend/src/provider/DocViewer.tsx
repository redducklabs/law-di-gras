// Minimal document viewer overlay: the browser's PDF viewer in an iframe.
// Provider side uses token-scoped URLs so only shared documents can load.
import { useEffect } from 'react'

export interface OpenedDoc { url: string; title: string; page?: number | null }

export default function DocViewer({ doc, onClose }: { doc: OpenedDoc | null; onClose: () => void }) {
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => e.key === 'Escape' && onClose()
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [onClose])
  if (!doc) return null
  return (
    <div className="fixed inset-0 z-50 flex justify-end bg-slate-900/40" onClick={onClose}>
      <div className="flex h-full w-full max-w-3xl flex-col bg-white shadow-xl" onClick={(e) => e.stopPropagation()}>
        <div className="flex items-center justify-between border-b border-slate-200 px-4 py-3">
          <span className="truncate text-sm font-medium text-slate-900">{doc.title}{doc.page ? ` · p.${doc.page}` : ''}</span>
          <button type="button" onClick={onClose} className="rounded px-2 py-1 text-sm text-slate-500 hover:bg-slate-100">Close</button>
        </div>
        <iframe title={doc.title} src={`${doc.url}${doc.page ? `#page=${doc.page}` : ''}`} className="flex-1" />
      </div>
    </div>
  )
}
