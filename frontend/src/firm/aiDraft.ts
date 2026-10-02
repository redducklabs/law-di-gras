// "Improve with AI" for a Next-step draft: S2 writes a grounded draft whose fact segments cite the
// record; anything it could not verify comes back marked. Templates stay the default.
import { ApiError, api } from '../api/client'
import type { Draft, DraftSegment } from '../api/types'
import type { Step } from './stepRules'

export async function requestAiDraft(matterId: string, step: Step): Promise<Draft> {
  try {
    return await api.draft(matterId, step.actionIndex != null ? { action_index: step.actionIndex } : { title: step.title })
  } catch (e) {
    if (e instanceof ApiError && e.status === 404) throw new Error('No AI draft available for this item.')
    throw new Error(e instanceof ApiError ? `Draft failed (${e.status}).` : String(e))
  }
}

/** Separator before segment i: a paragraph break when the kind changes (greeting → facts → ask →
 *  sign-off), a space within a run, nothing if the text already carries whitespace. */
export function segmentSep(segs: DraftSegment[], i: number) {
  if (i === 0) return ''
  const prev = segs[i - 1].text, cur = segs[i].text
  if (/\s$/.test(prev) || /^\s/.test(cur)) return ''
  return segs[i - 1].kind !== segs[i].kind ? '\n\n' : ' '
}

/** Plain text for copy / mail. */
export const aiDraftText = (d: Draft) => d.segments.map((s, i) => segmentSep(d.segments, i) + s.text).join('')
