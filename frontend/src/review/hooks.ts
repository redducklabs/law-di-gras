import { useEffect, useState } from 'react'
import type { AuditReport, CaseReview } from '../api/types'


const url = (matterId: string) => `/api/matters/${encodeURIComponent(matterId)}/review`
const POLL_MS = 3000
const live = (s?: string | null) => s === 'queued' || s === 'running'

/** GET the last completed review plus `run` (null when none yet); POST starts a background run. */
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
  /** Built-in audit of the review (S6). Missing route or no report → null, silently. */
  audit: async (matterId: string): Promise<AuditReport | null> => {
    try {
      const res = await fetch(`/api/matters/${encodeURIComponent(matterId)}/audit?target=review`)
      if (!res.ok) return null
      return await res.json()
    } catch {
      return null
    }
  },
}

/** Cached review for a matter; polls every 3 s while a background run is in flight. */
export function useReview(matterId: string | undefined) {
  const [review, setReview] = useState<CaseReview | null>(null)
  const [loading, setLoading] = useState(false)
  const [tick, setTick] = useState(0)

  useEffect(() => {
    if (!matterId) return
    let alive = true
    setLoading(true)
    reviewApi.get(matterId).then(r => alive && setReview(r)).catch(() => {}).finally(() => alive && setLoading(false))
    return () => { alive = false }
  }, [matterId, tick])

  const running = live(review?.run?.status)
  useEffect(() => {
    if (!matterId || !running) return
    const t = setInterval(() => {
      reviewApi.get(matterId).then(r => r && setReview(r)).catch(() => {})
    }, POLL_MS)
    return () => clearInterval(t)
  }, [matterId, running])

  const run = (force = false) => {
    if (!matterId) return
    reviewApi.run(matterId, force).then(setReview).catch(() => setTick(t => t + 1))
  }
  return { review, loading: loading && !review, running, run }
}

/** Audit report for the review's findings; polls while the audit runs. Re-fetches when the review changes. */
export function useReviewAudit(matterId: string | undefined, reviewStamp: string | undefined) {
  const [audit, setAudit] = useState<AuditReport | null>(null)
  useEffect(() => {
    if (!matterId || !reviewStamp) return
    let alive = true
    let timer: ReturnType<typeof setTimeout> | undefined
    const load = () => reviewApi.audit(matterId).then(a => {
      if (!alive) return
      setAudit(a)
      if (a && live(a.run.status)) timer = setTimeout(load, POLL_MS)
    })
    load()
    return () => { alive = false; if (timer) clearTimeout(timer) }
  }, [matterId, reviewStamp])
  return audit
}
