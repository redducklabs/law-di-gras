import { useEffect, type ReactNode } from 'react'

/** Right-side drawer with scrim. Full width on phones. Esc closes. */
export function Drawer({ open, onClose, title, subtitle, width = 560, children, footer }: {
  open: boolean
  onClose: () => void
  title: ReactNode
  subtitle?: ReactNode
  width?: number
  children: ReactNode
  footer?: ReactNode
}) {
  useEffect(() => {
    if (!open) return
    const onKey = (e: KeyboardEvent) => e.key === 'Escape' && onClose()
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [open, onClose])

  return (
    <div className={`fixed inset-0 z-50 ${open ? '' : 'pointer-events-none'}`} aria-hidden={!open}>
      <div onClick={onClose}
        className={`absolute inset-0 bg-slate-900/25 transition-opacity duration-200 ${open ? 'opacity-100' : 'opacity-0'}`} />
      <aside role="dialog" aria-modal="true" style={{ maxWidth: width }}
        className={`absolute inset-y-0 right-0 flex w-full flex-col bg-surface shadow-pop transition-transform duration-200 ease-out ${open ? 'translate-x-0' : 'translate-x-full'}`}>
        <header className="flex items-start justify-between gap-4 border-b border-line px-5 py-4">
          <div className="min-w-0">
            <h2 className="truncate text-[15px] font-semibold text-slate-900">{title}</h2>
            {subtitle && <div className="mt-0.5 text-[12.5px] text-slate-500">{subtitle}</div>}
          </div>
          <button type="button" onClick={onClose} aria-label="Close"
            className="-mr-1 grid h-8 w-8 shrink-0 cursor-pointer place-items-center rounded-lg text-slate-500 hover:bg-slate-100 hover:text-slate-900">
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.8"><path d="M4 4l8 8M12 4l-8 8" /></svg>
          </button>
        </header>
        <div className="min-h-0 flex-1 overflow-y-auto">{children}</div>
        {footer && <footer className="border-t border-line px-5 py-3">{footer}</footer>}
      </aside>
    </div>
  )
}
