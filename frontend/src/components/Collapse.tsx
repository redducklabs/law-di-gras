// Collapsible sections that open themselves when a chat deeplink scrolls to them.
import { useEffect, useRef, useState, type ReactNode } from 'react'

// App.tsx resolves section deeplinks with el.scrollIntoView(). We wrap it once so the
// target element gets a bubbling 'reveal' event first; collapsed sections listen by id and expand.
let hooked = false
function installRevealHook() {
  if (hooked || typeof Element === 'undefined') return
  hooked = true
  const orig = Element.prototype.scrollIntoView
  Element.prototype.scrollIntoView = function (this: Element, arg?: boolean | ScrollIntoViewOptions) {
    this.dispatchEvent(new CustomEvent('reveal', { bubbles: true }))
    return orig.call(this, arg)
  }
}

/** Call `onReveal` when a deeplink scrolls to the element with this id. */
export function useReveal(id: string, onReveal: () => void) {
  const cb = useRef(onReveal)
  cb.current = onReveal
  useEffect(() => {
    installRevealHook()
    const on = (e: Event) => { if ((e.target as Element | null)?.id === id) cb.current() }
    document.addEventListener('reveal', on)
    return () => document.removeEventListener('reveal', on)
  }, [id])
}

export function Chevron({ open }: { open: boolean }) {
  return (
    <svg width="14" height="14" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden
      className={`shrink-0 text-slate-400 transition-transform duration-300 ${open ? 'rotate-90' : ''}`}>
      <path d="M6 3l5 5-5 5" />
    </svg>
  )
}

/** One row of a stacked disclosure list: title + one-line summary; click to expand (animated). */
export function Disclosure({ id, title, summary, extra, children }: {
  id: string
  title: ReactNode
  summary?: ReactNode
  extra?: ReactNode
  children: ReactNode
}) {
  const [open, setOpen] = useState(false)
  useReveal(id, () => setOpen(true))
  return (
    <section id={id} className="scroll-mt-4 border-t border-line-soft first:border-0">
      <button type="button" onClick={() => setOpen(v => !v)} aria-expanded={open}
        className="flex w-full cursor-pointer items-center gap-3 px-4 py-3 text-left hover:bg-page/60 sm:px-5">
        <Chevron open={open} />
        <span className="shrink-0 text-[14px] font-semibold text-slate-900">{title}</span>
        <span className="min-w-0 flex-1 truncate text-[12.5px] text-slate-500">{summary}</span>
        {extra && <span className="shrink-0">{extra}</span>}
      </button>
      <div className="grid transition-[grid-template-rows] duration-300 ease-out" style={{ gridTemplateRows: open ? '1fr' : '0fr' }}>
        <div className="overflow-hidden" inert={!open}>
          <div className={`px-4 pb-5 pt-1 transition-opacity duration-300 sm:px-5 sm:pl-[3.1rem] ${open ? 'opacity-100' : 'opacity-0'}`}>{children}</div>
        </div>
      </div>
    </section>
  )
}
