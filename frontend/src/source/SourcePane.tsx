// Source pane body, rendered inside the firm page's right Drawer. Owned by S5.
// Contract (App.tsx mounts it): either `citation` (open that source at the
// highlighted span) or `query` (Find in case results) is set.
import { useEffect, useState } from 'react'
import type { Citation, SourceDetail } from '../api/types'
import { api } from '../api/client'
import { FindAsk } from './FindAsk'
import { Notice, QuoteBlock, Spinner } from './parts'
import { PdfView } from './PdfView'
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
    ? <PdfView source={source} citation={citation} />
    : <TextView source={source} citation={citation} />
}
