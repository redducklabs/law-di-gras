// Dev-only stand-in for POST /chat until S2 lands it. Enabled with ?chatmock=1.
// No case content here: the answer is assembled from live /search passages,
// and deeplinks come from generic keyword → page-section rules.
import { api } from '../api/client'
import type { ChatRequest, ChatResponse, DeepLink, PageSection } from '../api/types'

export const chatMockEnabled = () => {
  try { return new URLSearchParams(window.location.search).has('chatmock') } catch { return false }
}

const SECTION_RULES: [RegExp, PageSection, string][] = [
  [/overdue|deadline|due|task|next step|waiting/i, 'next-steps', 'Jump to Next steps'],
  [/coverage|policy|limit|insur|\blien/i, 'kpis', 'Jump to coverage and KPIs'],
  [/client|contact|talk|call|spoke/i, 'recent', 'Jump to Recent activity'],
  [/injur|diagnos|mri|surgery/i, 'injuries', 'Jump to Injuries'],
  [/treat|provider|visit|bill|special/i, 'treatment', 'Jump to Treatment'],
  [/status|stage|stand/i, 'status', 'Jump to Where the case stands'],
]

export async function mockChat(matterId: string, body: ChatRequest): Promise<ChatResponse> {
  const q = [...body.messages].reverse().find(m => m.role === 'user')?.content ?? ''
  const passages = (await api.search(matterId, q)).slice(0, 4)
  const citations = passages.map(p => p.citation)
  const lines = passages.map((p, i) => `- ${p.snippet.replace(/\s+/g, ' ').replace(/^…/, '').slice(0, 180).trim()}… [${i + 1}]`)
  const links: DeepLink[] = SECTION_RULES.filter(([re]) => re.test(q)).slice(0, 2)
    .map(([, section, label]) => ({ label, kind: 'section', section }))
  if (citations[0]) links.push({ label: 'Open the top passage', kind: 'source', citation: citations[0] })
  return {
    answer_markdown: passages.length
      ? `**Preview (chat service not live):** closest passages in the record.\n\n${lines.join('\n')}`
      : 'No passages in the record match that question.',
    citations,
    links,
  }
}
