// Source pane body, rendered inside the firm page's right Drawer. Owned by S5.
// Contract (App.tsx mounts it): either `citation` (open that source at the
// highlighted span) or `query` (Find in case results) is set.
import { Component, useEffect, useState, type ReactNode } from 'react'
import type { Citation, SourceDetail } from '../api/types'
import { api } from '../api/client'
import { FindAsk } from './FindAsk'
import { Notice, QuoteBlock, Spinner } from './parts'
import { PageFallback, PdfView } from './PdfView'
import { TextView } from './TextView'

export interface SourcePaneProps {
  matterId: string
  citation: Citation | null
  query: string | null
  onOpenCitation: (c: Citation) => void
  /** Optional: return to the previous results list (set when opened from Find in case). */
  onBack?: () => void
}

export function SourcePane({ matterId, citation, query, onOpenCitation, onBack }: SourcePaneProps) {
  if (citation) {
    return (
      <>
        {onBack && (
          <div className="border-b border-line-soft px-5 py-2">
            <button type="button" onClick={onBack}
              className="cursor-pointer text-[12.5px] font-medium text-brand-700 hover:underline">← Back to results</button>
          </div>
        )}
        <CitationView citation={citation} />
      </>
    )
  }
  if (query) return <FindAsk matterId={matterId} query={query} onOpenCitation={onOpenCitation} />
  return null
}

function CitationView({ citation }: { citation: Citation }) {
  const [source, setSource] = useState<SourceDetail | null>(null)
  const [err, setErr] = useState(false)

  useEffect(() => {
    let live = true
    setSource(null); setErr(false)
    api.source(citation.source_id).then(s => live && setSource(s)).catch(() => live && setErr(true))
    return () => { live = false }
  }, [citation.source_id])

  if (err) {
    return (
      <div className="space-y-3 p-5">
        <Notice tone="danger">This record could not be loaded from the case file.</Notice>
        <QuoteBlock citation={citation} />
      </div>
    )
  }
  if (!source) return <div className="px-5"><Spinner label="Opening the record…" /></div>
  return source.has_file && source.kind === 'document'
    ? (
      <PdfBoundary key={`${source.id}:${citation.page}`} fallback={
        <div className="p-5">
          <PageFallback source={source} citation={citation} fileUrl={api.sourceFileUrl(source.id)} page={citation.page ?? citation.rects[0]?.page ?? 1} />
        </div>
      }>
        <PdfView source={source} citation={citation} />
      </PdfBoundary>
    )
    : <TextView source={source} citation={citation} />
}

/** A PDF that pdf.js cannot handle must never take the whole app down: show the extracted text instead. */
class PdfBoundary extends Component<{ fallback: ReactNode; children: ReactNode }, { failed: boolean }> {
  state = { failed: false }
  static getDerivedStateFromError() { return { failed: true } }
  componentDidCatch(error: unknown) { console.error('PDF viewer crashed; showing extracted text', error) }
  render() { return this.state.failed ? this.props.fallback : this.props.children }
}
