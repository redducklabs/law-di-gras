// S4 data layer: provider sharing. UI files in this folder hold no fetch logic,
// so the S3 restyle can change markup freely.
import { useCallback, useEffect, useRef, useState } from 'react'
import { api } from '../api/client'
import type { Provider, ProviderView, ShareSettings } from '../api/types'

const enc = encodeURIComponent

export interface ShareDocument { id: string; title: string | null; date: string | null; suggested: boolean }

async function json<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(path, { ...init, headers: { 'Content-Type': 'application/json', ...init?.headers } })
  if (!res.ok) throw new Error(`${res.status} ${await res.text()}`)
  return res.json() as Promise<T>
}

export const shareApi = {
  documents: (matterId: string, contactId: string) =>
    json<ShareDocument[]>(`/api/matters/${enc(matterId)}/share/${enc(contactId)}/documents`),
  preview: (matterId: string, settings: ShareSettings) =>
    json<ProviderView>(`/api/matters/${enc(matterId)}/share/${enc(settings.contact_id)}/preview`, {
      method: 'POST', body: JSON.stringify(settings),
    }),
  sharedFileUrl: (token: string, sourceId: string) => `/api/share/${enc(token)}/sources/${enc(sourceId)}/file`,
}

export const shareLink = (token: string) => `${window.location.origin}/p/${token}`

/** Provider page: load the view once per token (each load logs a view server-side). */
export function useProviderView(token: string | undefined) {
  const [view, setView] = useState<ProviderView | null>(null)
  const [error, setError] = useState<string | null>(null)
  const loaded = useRef<string | null>(null)
  useEffect(() => {
    if (!token || loaded.current === token) return
    loaded.current = token
    api.providerView(token).then(setView).catch((e) => setError(e.status === 404 ? 'notfound' : String(e)))
  }, [token])
  return { view, error, loading: !view && !error }
}

export function useProviders(matterId: string | undefined, enabled: boolean) {
  const [providers, setProviders] = useState<Provider[] | null>(null)
  const [error, setError] = useState<string | null>(null)
  useEffect(() => {
    if (!matterId || !enabled) return
    api.providers(matterId).then(setProviders).catch((e) => setError(String(e)))
  }, [matterId, enabled])
  return { providers, error }
}

/**
 * Share panel state for one provider: settings auto-save on every change
 * (so the link always reflects what the attorney sees), with a live preview.
 */
export function useShare(matterId: string | undefined, contactId: string | null) {
  const [settings, setSettings] = useState<ShareSettings | null>(null)
  const [documents, setDocuments] = useState<ShareDocument[]>([])
  const [preview, setPreview] = useState<ProviderView | null>(null)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const seq = useRef(0)

  useEffect(() => {
    setSettings(null); setPreview(null); setDocuments([]); setError(null)
    if (!matterId || !contactId) return
    let alive = true
    Promise.all([api.shareSettings(matterId, contactId), shareApi.documents(matterId, contactId)])
      .then(([s, docs]) => {
        if (!alive) return
        setSettings(s); setDocuments(docs)
        return shareApi.preview(matterId, s).then((p) => alive && setPreview(p))
      })
      .catch((e) => alive && setError(String(e)))
    return () => { alive = false }
  }, [matterId, contactId])

  const save = useCallback(async (next: ShareSettings) => {
    if (!matterId) return null
    const my = ++seq.current
    setSettings(next); setSaving(true)
    try {
      const [saved, p] = await Promise.all([api.saveShareSettings(matterId, next), shareApi.preview(matterId, next)])
      if (my === seq.current) { setSettings(saved); setPreview(p) }
      return saved
    } catch (e) {
      setError(String(e))
      return null
    } finally {
      if (my === seq.current) setSaving(false)
    }
  }, [matterId])

  return { settings, documents, preview, saving, error, save }
}
