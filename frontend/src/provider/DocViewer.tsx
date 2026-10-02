// Minimal document viewer overlay: the browser's PDF viewer in an iframe.
// Provider side uses token-scoped URLs so only shared documents can load.
import { useEffect } from 'react'
import { prettyTitle } from '../components'

export interface OpenedDoc { url: string; title: string; page?: number | null }

export default function DocViewer({ doc, onClose }: { doc: OpenedDoc | null; onClose: () => void }) {
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => e.key === 'Escape' && onClose()
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [onClose])
  if (!doc) return null
  return (
    <div className="fixed inset-0 z-50 flex justify-end bg-slate-900/25" onClick={onClose}>
      <div className="flex h-full w-full max-w-3xl flex-col bg-surface shadow-pop" onClick={(e) => e.stopPropagation()}>
        <div className="flex items-center justify-between gap-4 border-b border-line px-5 py-3.5">
          <span className="truncate text-[14px] font-semibold text-slate-900">{prettyTitle(doc.title)}{doc.page ? ` · p.${doc.page}` : ''}</span>
          <button type="button" onClick={onClose} aria-label="Close" className="grid h-8 w-8 shrink-0 cursor-pointer place-items-center rounded-lg text-slate-500 hover:bg-slate-100 hover:text-slate-900"><svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.8"><path d="M4 4l8 8M12 4l-8 8" /></svg></button>
        </div>
        <iframe title={doc.title} src={`${doc.url}${doc.page ? `#page=${doc.page}` : ''}`} className="flex-1 bg-page" />
      </div>
    </div>
  )
}
