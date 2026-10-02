// Fetch wrappers for every route in the plan's API table. Vite proxies /api.
import type {
  Answer, ChatRequest, ChatResponse, Dashboard, Draft, DraftRequest, MatterSummary, Passage, Provider, ProviderView,
  ShareSettings, SourceDetail,
} from './types'

export class ApiError extends Error {
  status: number
  constructor(status: number, message: string) {
    super(message)
    this.status = status
  }
}

async function req<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(path, {
    ...init,
    headers: { 'Content-Type': 'application/json', ...init?.headers },
  })
  if (!res.ok) throw new ApiError(res.status, await res.text())
  return res.json() as Promise<T>
}

const enc = encodeURIComponent

export const api = {
  matters: () => req<MatterSummary[]>('/api/matters'),
  sync: (matterId: string) =>
    req<{ sources: number; pages: number; chunks: number }>(`/api/matters/${enc(matterId)}/sync`, { method: 'POST' }),

  source: (sourceId: string) => req<SourceDetail>(`/api/sources/${enc(sourceId)}`),
  sourceFileUrl: (sourceId: string) => `/api/sources/${enc(sourceId)}/file`,

  dashboard: (matterId: string) => req<Dashboard>(`/api/matters/${enc(matterId)}/dashboard`),
  digest: (matterId: string, force = false) =>
    req<Dashboard>(`/api/matters/${enc(matterId)}/digest?force=${force}`, { method: 'POST' }),
  search: (matterId: string, q: string) =>
    req<Passage[]>(`/api/matters/${enc(matterId)}/search?q=${enc(q)}`),
  draft: (matterId: string, body: DraftRequest) =>
    req<Draft>(`/api/matters/${enc(matterId)}/draft`, { method: 'POST', body: JSON.stringify(body) }),
  ask: (matterId: string, question: string) =>
    req<Answer>(`/api/matters/${enc(matterId)}/ask`, { method: 'POST', body: JSON.stringify({ question }) }),
  chat: (matterId: string, body: ChatRequest) =>
    req<ChatResponse>(`/api/matters/${enc(matterId)}/chat`, { method: 'POST', body: JSON.stringify(body) }),

  providers: (matterId: string) => req<Provider[]>(`/api/matters/${enc(matterId)}/providers`),
  shareSettings: (matterId: string, contactId: string) =>
    req<ShareSettings>(`/api/matters/${enc(matterId)}/share/${enc(contactId)}`),
  saveShareSettings: (matterId: string, settings: ShareSettings) =>
    req<ShareSettings>(`/api/matters/${enc(matterId)}/share/${enc(settings.contact_id)}`, {
      method: 'PUT', body: JSON.stringify(settings),
    }),
  providerView: (token: string) => req<ProviderView>(`/api/share/${enc(token)}`),
}
