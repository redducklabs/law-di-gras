// Integration owns routing and the cross-stream wiring. Streams own the pieces.
import { useEffect, useState } from 'react'
import { Route, Routes, useNavigate, useParams } from 'react-router-dom'
import { api } from './api/client'
import type { Citation, Dashboard, DeepLink } from './api/types'
import { ChatPanel } from './chat/ChatPanel'
import { Drawer, chipLabel } from './components'
import { FirmPage } from './firm'
import ProviderPage from './provider/ProviderPage'
import SharePanel from './provider/SharePanel'
import { SourcePane } from './source/SourcePane'

type Pane = { citation: Citation | null; query: string | null; from?: string | null }

// Briefly highlight a section the chat linked to.
function flashSection(id: string) {
  const el = document.getElementById(id)
  if (!el) return
  el.scrollIntoView({ behavior: 'smooth', block: 'start' })
  el.animate(
    [{ boxShadow: '0 0 0 3px rgb(99 102 241 / 0.55)' }, { boxShadow: '0 0 0 3px rgb(99 102 241 / 0)' }],
    { duration: 1600, easing: 'ease-out' },
  )
}

function Firm() {
  const { id: routeId } = useParams()
  const navigate = useNavigate()
  const [matterId, setMatterId] = useState<string | null>(routeId ?? null)
  const [pane, setPane] = useState<Pane | null>(null)
  const [shareOpen, setShareOpen] = useState(false)
  const [chatOpen, setChatOpen] = useState(false)
  const [focusDate, setFocusDate] = useState<string | null>(null)

  // The chat and search need the matter id before any share/search click.
  useEffect(() => {
    if (routeId) { setMatterId(routeId); return }
    api.matters().then(ms => { if (ms[0]) setMatterId(ms[0].id) }).catch(() => {})
  }, [routeId])

  const onNavigate = (link: DeepLink) => {
    switch (link.kind) {
      case 'section': if (link.section) flashSection(link.section); break
      case 'timeline':
        if (link.date) { setFocusDate(null); requestAnimationFrame(() => setFocusDate(link.date!)) }
        flashSection('timeline'); break
      case 'source': if (link.citation) openCitation(link.citation); break
      case 'share': setShareOpen(true); break
      case 'route': if (link.path) navigate(link.path); break
    }
  }

  const openCitation = (c: Citation) => setPane(p => ({ citation: c, query: null, from: p?.query ?? p?.from ?? null }))
  const track = (d: Dashboard) => setMatterId(d.matter.id)

  return (
    <>
      <FirmPage
        matterId={routeId}
        focusDate={focusDate}
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
      {matterId && (
        <ChatPanel matterId={matterId} open={chatOpen} onClose={() => setChatOpen(false)}
          onOpenCitation={openCitation} onNavigate={onNavigate} />
      )}
      {matterId && !chatOpen && (
        <button type="button" onClick={() => setChatOpen(true)}
          className="fixed bottom-5 right-5 z-30 cursor-pointer rounded-full bg-brand-700 px-4 py-2.5 text-[13px] font-semibold text-white shadow-pop hover:bg-brand-800">
          Ask the case
        </button>
      )}
    </>
  )
}

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Firm />} />
      <Route path="/matters/:id" element={<Firm />} />
      <Route path="/p/:token" element={<ProviderPage />} />
    </Routes>
  )
}
