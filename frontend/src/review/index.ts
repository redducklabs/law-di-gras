import { useEffect, useState } from 'react'
import type { CaseReview } from '../api/types'

export { BlindSpots } from './BlindSpots'

const url = (matterId: string) => `/api/matters/${encodeURIComponent(matterId)}/review`

/** GET the cached review (null when none yet); POST runs the agent (2–4 min). */
export const reviewApi = {
  get: async (matterId: string): Promise<CaseReview | null> => {
    const res = await fetch(url(matterId))
    if (res.status === 404) return null
    if (!res.ok) throw new Error(await res.text())
    return res.json()
  },
  run: async (matterId: string, force = false): Promise<CaseReview> => {
    const res = await fetch(`${url(matterId)}${force ? '?force=true' : ''}`, { method: 'POST' })
    if (!res.ok) throw new Error(await res.text())
    return res.json()
  },
}

/** Cached review for a matter, plus a runner for the empty state. */
export function useReview(matterId: string | undefined) {
  const [review, setReview] = useState<CaseReview | null>(null)
  const [loading, setLoading] = useState(false)
  useEffect(() => {
    if (!matterId) return
    let live = true
    setLoading(true)
    reviewApi.get(matterId).then(r => live && setReview(r)).catch(() => {}).finally(() => live && setLoading(false))
    return () => { live = false }
  }, [matterId])
  const run = () => {
    if (!matterId) return
    setLoading(true)
    reviewApi.run(matterId).then(setReview).catch(() => {}).finally(() => setLoading(false))
  }
  return { review, loading, run }
}
