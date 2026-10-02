// "Improve with AI" for a Next-step draft: S2 writes a grounded draft whose fact segments cite the
// record; anything it could not verify comes back marked. Templates stay the default.
// TODO(contract): switch to the `Draft` type in api/types.ts once S2 commits it.
import type { Citation } from '../api/types'
import type { Step } from './stepRules'

export interface AiDraftSegment {
  text: string
  kind: 'fact' | 'ask' | 'courtesy'
  citations: Citation[]
  verified: boolean
}

export interface AiDraft {
  subject: string
  segments: AiDraftSegment[]
  unverified: string[]
}

export interface AiDraftRequest {
  kind: Step['kind']
  title: string
  why: string
  owner?: string | null
  waiting_on?: string | null
  date?: string | null
  audience: string
  source_ids: string[]
  template_subject: string
  template_body: string
}

export async function requestAiDraft(matterId: string, body: AiDraftRequest): Promise<AiDraft> {
  const res = await fetch(`/api/matters/${encodeURIComponent(matterId)}/draft`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (!res.ok) throw new Error(res.status === 404 ? 'AI drafting is not available yet.' : `Draft failed (${res.status}).`)
  return res.json() as Promise<AiDraft>
}

/** Plain text for copy / mail: segments joined as written. */
export const aiDraftText = (d: AiDraft) => d.segments.map(s => s.text).join('')
