// Pure helpers for locating a quote in source text. No case content.

const QUOTE_MAP: Record<string, string> = {
  '‘': "'", '’': "'", '‚': "'", '‛': "'",
  '“': '"', '”': '"', '„': '"', '‟': '"',
  '–': '-', '—': '-', ' ': ' ', '�': '?',
}

/** Lowercased, quote-folded, whitespace-collapsed text plus a map back to original offsets. */
function normalize(s: string): { norm: string; map: number[] } {
  let norm = ''
  const map: number[] = []
  let prevSpace = true
  for (let i = 0; i < s.length; i++) {
    let ch = QUOTE_MAP[s[i]] ?? s[i]
    if (/\s/.test(ch)) {
      if (prevSpace) continue
      ch = ' '
      prevSpace = true
    } else prevSpace = false
    norm += ch.toLowerCase()
    map.push(i)
  }
  return { norm, map }
}

/** Find [start, end) of `quote` in `text`, tolerant of whitespace and curly quotes. */
export function findQuote(text: string, quote: string): [number, number] | null {
  if (!quote.trim()) return null
  const exact = text.indexOf(quote)
  if (exact >= 0) return [exact, exact + quote.length]
  const t = normalize(text)
  const q = normalize(quote).norm.trim()
  if (!q) return null
  // Replacement chars ('?') in either side match anything.
  let at = t.norm.indexOf(q)
  if (at < 0 && q.includes('?')) {
    const re = new RegExp(q.replace(/[.*+^${}()|[\]\\]/g, '\\$&').replace(/\?/g, '.'))
    at = t.norm.search(re)
  }
  if (at < 0) return null
  return [t.map[at], t.map[at + q.length - 1] + 1]
}

/** Resolve the highlighted range: trust offsets when they match the quote, else search. */
export function resolveSpan(text: string, quote: string, start?: number | null, end?: number | null): [number, number] | null {
  if (start != null && end != null && end > start && end <= text.length) {
    const slice = text.slice(start, end)
    if (slice === quote || normalize(slice).norm.trim() === normalize(quote).norm.trim()) return [start, end]
  }
  return findQuote(text, quote) ?? (start != null && end != null && end > start && end <= text.length ? [start, end] : null)
}

const STOP = new Set(['and', 'the', 'for', 'with', 'from', 'that', 'this', 'was', 'were', 'are', 'has', 'have', 'did', 'does', 'what', 'when', 'who', 'how', 'any', 'not'])

/** Query words worth bolding in a snippet (3+ chars, no stopwords). */
export function queryTerms(q: string): string[] {
  return [...new Set(q.toLowerCase().split(/[^\p{L}\p{N}$]+/u).filter(w => w.length > 2 && !STOP.has(w)))]
}

const ENTITIES: Record<string, string> = { amp: '&', lt: '<', gt: '>', quot: '"', apos: "'", nbsp: ' ', '#39': "'" }

/** Display-only: decode HTML entities that Clio leaves in note/email text. Offsets stay on the raw text. */
export const decodeEntities = (s: string) =>
  s.replace(/&(amp|lt|gt|quot|apos|nbsp|#39);/g, (_, k: string) => ENTITIES[k])
