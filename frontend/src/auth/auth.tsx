// Firm sign-in state. Session is an HttpOnly cookie set by POST /api/auth/login;
// the client only asks /api/auth/me who is signed in. Provider links (/p/:token) never use this.
import { createContext, useCallback, useContext, useEffect, useState, type ReactNode } from 'react'
import { Navigate, useLocation } from 'react-router-dom'

export interface AuthState {
  loading: boolean
  user: string | null
  authEnabled: boolean
  signedIn: boolean
  login: (username: string, password: string) => Promise<string | null> // error message or null
  logout: () => Promise<void>
}

const Ctx = createContext<AuthState | null>(null)

async function post(path: string, body?: unknown) {
  return fetch(path, {
    method: 'POST',
    credentials: 'same-origin',
    headers: { 'Content-Type': 'application/json' },
    body: body ? JSON.stringify(body) : undefined,
  })
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [loading, setLoading] = useState(true)
  const [user, setUser] = useState<string | null>(null)
  const [authEnabled, setAuthEnabled] = useState(true)

  useEffect(() => {
    fetch('/api/auth/me', { credentials: 'same-origin' })
      .then(async (r) => {
        const j = await r.json().catch(() => ({}))
        setAuthEnabled(j.auth_enabled !== false)
        setUser(r.ok ? j.user ?? null : null)
      })
      .catch(() => setUser(null))
      .finally(() => setLoading(false))
  }, [])

  const login = useCallback(async (username: string, password: string) => {
    try {
      const r = await post('/api/auth/login', { username, password })
      const j = await r.json().catch(() => ({}))
      if (!r.ok) return j.detail ?? 'Sign-in failed. Try again.'
      setAuthEnabled(j.auth_enabled !== false)
      setUser(j.user ?? null)
      return null
    } catch {
      return 'Could not reach the server. Try again.'
    }
  }, [])

  const logout = useCallback(async () => {
    await post('/api/auth/logout').catch(() => undefined)
    setUser(null)
  }, [])

  const signedIn = !authEnabled || !!user
  return <Ctx.Provider value={{ loading, user, authEnabled, signedIn, login, logout }}>{children}</Ctx.Provider>
}

export function useAuth(): AuthState {
  const v = useContext(Ctx)
  if (!v) throw new Error('useAuth must be used inside <AuthProvider>')
  return v
}

/** Renders children when signed in (or auth is disabled); otherwise redirects to /login?next=… */
export function RequireAuth({ children }: { children: ReactNode }) {
  const { loading, signedIn } = useAuth()
  const loc = useLocation()
  if (loading) {
    return <div className="grid min-h-screen place-items-center bg-page"><div className="h-6 w-6 animate-spin rounded-full border-2 border-brand-200 border-t-brand-600" /></div>
  }
  if (!signedIn) return <Navigate to={`/login?next=${encodeURIComponent(loc.pathname + loc.search)}`} replace />
  return <>{children}</>
}
