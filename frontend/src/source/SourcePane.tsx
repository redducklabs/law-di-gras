// Source pane body, rendered inside the firm page's right Drawer. Owned by S5.
// Contract (App.tsx mounts it): either `citation` (open that source at the
// highlighted span) or `query` (Find in case results) is set.
import type { Citation } from '../api/types'

export interface SourcePaneProps {
  matterId: string
  citation: Citation | null
  query: string | null
  onOpenCitation: (c: Citation) => void
}

export function SourcePane({ citation, query }: SourcePaneProps) {
  return (
    <div className="p-4 text-[13px] text-slate-500">
      {citation ? `“${citation.quote}”` : query ? `Search: ${query}` : null}
    </div>
  )
}
