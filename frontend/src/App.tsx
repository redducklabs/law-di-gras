// Integration owns routing and the cross-stream wiring. Streams own the pieces.
import { useState } from 'react'
import { Route, Routes } from 'react-router-dom'
import type { Citation, Dashboard } from './api/types'
import { Drawer, chipLabel } from './components'
import { FirmPage } from './firm'
import ProviderPage from './provider/ProviderPage'
import SharePanel from './provider/SharePanel'
import { SourcePane } from './source/SourcePane'

type Pane = { citation: Citation | null; query: string | null; from?: string | null }

function Firm() {
  const [matterId, setMatterId] = useState<string | null>(null)
  const [pane, setPane] = useState<Pane | null>(null)
  const [shareOpen, setShareOpen] = useState(false)

  const openCitation = (c: Citation) => setPane(p => ({ citation: c, query: null, from: p?.query ?? p?.from ?? null }))
  const track = (d: Dashboard) => setMatterId(d.matter.id)

  return (
    <>
      <FirmPage
        onOpenSource={openCitation}
        onShare={d => { track(d); setShareOpen(true) }}
        onSearch={(q, d) => { track(d); setPane({ citation: null, query: q }) }}
      />
      <Drawer
        open={!!pane}
        onClose={() => setPane(null)}
        width={pane?.citation?.source_kind === 'document' ? 760 : 560}
        title={pane?.citation ? chipLabel(pane.citation) : 'Find in case'}
        subtitle={pane?.query ?? undefined}
      >
        {pane && (
          <SourcePane
            matterId={matterId ?? ''}
            citation={pane.citation}
            query={pane.query}
            onOpenCitation={openCitation}
            onBack={pane.citation && pane.from ? () => setPane({ citation: null, query: pane.from ?? null }) : undefined}
          />
        )}
      </Drawer>
      {matterId && <SharePanel matterId={matterId} open={shareOpen} onClose={() => setShareOpen(false)} />}
    </>
  )
}

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Firm />} />
      <Route path="/p/:token" element={<ProviderPage />} />
    </Routes>
  )
}
