// Dev preview of the firm Case Brief on the fictional fixture. Open /src/dev/brief.html.
import { StrictMode, useState } from 'react'
import { createRoot } from 'react-dom/client'
import '../index.css'
import type { Citation } from '../api/types'
import { Drawer, chipLabel } from '../components'
import { CaseBrief } from '../firm'
import { fixture } from './fixture'

function Preview() {
  const [cite, setCite] = useState<Citation | null>(null)
  return (
    <>
      <CaseBrief data={fixture} onOpenSource={setCite} onShare={() => alert('share')} onSearch={q => alert(q)} />
      <Drawer open={!!cite} onClose={() => setCite(null)} title={cite ? chipLabel(cite) : ''} subtitle="SourcePane mounts here (integration)">
        <blockquote className="m-5 border-l-4 border-warn-600 bg-warn-50 p-3 text-[13px]">{cite?.quote}</blockquote>
      </Drawer>
    </>
  )
}

createRoot(document.getElementById('root')!).render(<StrictMode><Preview /></StrictMode>)
