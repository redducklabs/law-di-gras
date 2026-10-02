// Shared display helpers (dates, money, names). Pure functions, no case content.

export const DAY = 86_400_000

/** Parse an ISO date or datetime; date-only strings are treated as local noon. */
export function parseDate(iso?: string | null): Date | null {
  if (!iso) return null
  const d = new Date(iso.length === 10 ? `${iso}T12:00:00` : iso)
  return Number.isNaN(d.getTime()) ? null : d
}

export function fmtDate(iso?: string | null, withYear = false): string {
  const d = parseDate(iso)
  if (!d) return '—'
  return d.toLocaleDateString('en-US', withYear
    ? { month: 'short', day: 'numeric', year: 'numeric' }
    : { month: 'short', day: 'numeric' })
}

export function fmtDateTime(iso?: string | null): string {
  const d = parseDate(iso)
  if (!d) return '—'
  return d.toLocaleString('en-US', { month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit' })
}

/** Whole days from today to the date (negative = past). */
export function daysFromToday(iso?: string | null, today = new Date()): number | null {
  const d = parseDate(iso)
  if (!d) return null
  const a = new Date(today.getFullYear(), today.getMonth(), today.getDate()).getTime()
  const b = new Date(d.getFullYear(), d.getMonth(), d.getDate()).getTime()
  return Math.round((b - a) / DAY)
}

export function relDays(n: number): string {
  if (n === 0) return 'today'
  if (n === 1) return 'tomorrow'
  if (n === -1) return 'yesterday'
  return n > 0 ? `in ${n} days` : `${-n} days ago`
}

export const money = (n?: number | null) =>
  n == null ? '—' : n.toLocaleString('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 })

export const initials = (name: string) =>
  name.split(/[\s,]+/).filter(Boolean).map(p => p[0]).slice(0, 2).join('').toUpperCase()
