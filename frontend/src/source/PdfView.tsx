// Cited PDF page with the quote's rects highlighted. Paging, OCR label, open-full link.
import { useEffect, useLayoutEffect, useRef, useState } from 'react'
import { Document, Page, pdfjs } from 'react-pdf'
import workerUrl from 'pdfjs-dist/build/pdf.worker.min.mjs?url'
import type { Citation, SourceDetail } from '../api/types'
import { api } from '../api/client'
import { Badge, fmtDate } from '../components'
import { Chevron, IconButton, KIND_LABEL, MetaRow, Notice, QuoteBlock, Spinner } from './parts'

pdfjs.GlobalWorkerOptions.workerSrc = workerUrl

export function PdfView({ source, citation }: { source: SourceDetail; citation: Citation }) {
  const firstRectPage = citation.rects[0]?.page
  const startPage = citation.page ?? firstRectPage ?? 1
  const [page, setPage] = useState(startPage)
  const [numPages, setNumPages] = useState<number | null>(source.page_count ?? null)
  const [width, setWidth] = useState(0)
  const [failed, setFailed] = useState(false)
  const box = useRef<HTMLDivElement>(null)
  const firstMark = useRef<HTMLDivElement>(null)

  useEffect(() => setPage(startPage), [startPage, source.id])

  useLayoutEffect(() => {
    const el = box.current
    if (!el) return
    const ro = new ResizeObserver(([e]) => setWidth(Math.floor(e.contentRect.width)))
    ro.observe(el)
    return () => ro.disconnect()
  }, [])

  const rects = citation.rects.filter(r => r.page === page)
  const citedPages = [...new Set(citation.rects.map(r => r.page))]
  const ocr = source.pages.find(p => p.page_no === page)?.ocr
  const fileUrl = api.sourceFileUrl(source.id)
  const total = numPages ?? source.page_count ?? 1

  const scrollToMark = () => {
    requestAnimationFrame(() => firstMark.current?.scrollIntoView({ block: 'center', behavior: 'smooth' }))
  }

  return (
    <div>
      {/* Pinned: what this is, the cited words, and page controls stay visible while the page scrolls. */}
      <div className="sticky top-0 z-10 space-y-3 border-b border-line bg-surface/95 px-5 pb-3 pt-4 backdrop-blur">
      <MetaRow items={[
        <Badge key="k" tone="brand">{KIND_LABEL[source.kind]}</Badge>,
        source.date ? `Filed in Clio ${fmtDate(source.date, true)}` : null,
        source.author,
        `${total} page${total === 1 ? '' : 's'}`,
      ]} />

      <QuoteBlock citation={citation} note={citation.verified && !citation.rects.length
        ? <span className="font-medium normal-case tracking-normal text-slate-500">No highlight position available</span>
        : null} />

      <div className="flex items-center justify-between gap-3">
        <div className="flex items-center gap-1.5">
          <IconButton label="Previous page" disabled={page <= 1} onClick={() => setPage(p => p - 1)}><Chevron dir="left" /></IconButton>
          <span className="min-w-[6.5rem] text-center text-[12.5px] tabular-nums text-slate-600">Page {page} of {total}</span>
          <IconButton label="Next page" disabled={page >= total} onClick={() => setPage(p => p + 1)}><Chevron dir="right" /></IconButton>
          {page !== startPage && (
            <button type="button" onClick={() => setPage(startPage)}
              className="ml-1 cursor-pointer rounded-md px-2 py-1 text-[12px] font-medium text-brand-700 hover:bg-brand-50">
              Back to cited page
            </button>
          )}
        </div>
        <div className="flex items-center gap-2">
          {ocr && <Badge tone="warn" className="font-medium">Scanned page, OCR text</Badge>}
          <a href={`${fileUrl}#page=${page}`} target="_blank" rel="noreferrer"
            className="text-[12px] font-medium text-brand-700 hover:underline">Open full PDF ↗</a>
        </div>
      </div>

      {citedPages.length > 1 && (
        <div className="flex flex-wrap items-center gap-1.5 text-[12px] text-slate-500">
          Highlighted on
          {citedPages.map(p => (
            <button key={p} type="button" onClick={() => setPage(p)}
              className={`cursor-pointer rounded-full px-2 py-0.5 font-medium ${p === page ? 'bg-brand-600 text-white' : 'bg-brand-50 text-brand-700 hover:bg-brand-100'}`}>
              p.{p}
            </button>
          ))}
        </div>
      )}

      </div>

      <div className="bg-page p-4 sm:p-5">
      <div ref={box} className="overflow-hidden rounded-md border border-line bg-white shadow-card">
        {failed ? (
          <div className="p-4"><Notice tone="danger">Could not load this PDF. <a className="font-medium underline" href={fileUrl} target="_blank" rel="noreferrer">Open the file</a> instead.</Notice></div>
        ) : (
          <Document file={fileUrl} onLoadSuccess={d => setNumPages(d.numPages)} onLoadError={() => setFailed(true)}
            loading={<div className="px-4"><Spinner label="Loading document…" /></div>}>
            {width > 0 && (
              <div className="relative">
                <Page pageNumber={page} width={width} renderTextLayer={false} renderAnnotationLayer={false}
                  onRenderSuccess={scrollToMark}
                  loading={<div style={{ height: width * 1.29 }} className="px-4"><Spinner label={`Rendering page ${page}…`} /></div>} />
                {rects.map((r, i) => (
                  <div key={i} ref={i === 0 ? firstMark : undefined}
                    className={`pointer-events-none absolute rounded-[2px] mix-blend-multiply ${citation.verified ? 'bg-yellow-300/55 ring-1 ring-yellow-500/50' : 'bg-amber-300/40 ring-1 ring-dashed ring-warn-600'}`}
                    style={{
                      left: `${r.x0 * 100}%`, top: `${r.y0 * 100}%`,
                      width: `${(r.x1 - r.x0) * 100}%`, height: `${(r.y1 - r.y0) * 100}%`,
                    }} />
                ))}
              </div>
            )}
          </Document>
        )}
      </div>
      </div>
    </div>
  )
}
