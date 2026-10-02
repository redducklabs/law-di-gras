// Firm sign-in page. On success goes to ?next= (same-origin path) or /cases.
import { useEffect, useState, type FormEvent } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { Fonts } from '../components'
import { useAuth } from './auth'

function safeNext(n: string | null) {
  return n && n.startsWith('/') && !n.startsWith('//') && !n.startsWith('/login') ? n : '/cases'
}

export default function LoginPage() {
  const { login, signedIn, loading } = useAuth()
  const navigate = useNavigate()
  const [params] = useSearchParams()
  const next = safeNext(params.get('next'))
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(params.get('error') ? "That username and password didn't match." : null)
  const [busy, setBusy] = useState(false)

  useEffect(() => {
    if (!loading && signedIn) navigate(next, { replace: true })
  }, [loading, signedIn, next, navigate])

  const submit = async (e: FormEvent) => {
    e.preventDefault()
    if (!username.trim() || !password) { setError('Enter your username and password.'); return }
    setBusy(true); setError(null)
    const err = await login(username, password)
    setBusy(false)
    if (err) { setError(err); setPassword('') } else navigate(next, { replace: true })
  }

  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-page px-4 py-10">
      <Fonts />
      <div className="w-full max-w-[380px]">
        <div className="mb-6 flex flex-col items-center text-center">
          <img src="/redducklawyer-logo.png" alt="" width={88} height={88} className="mb-3 h-[88px] w-[88px]" />
          <h1 className="text-[22px] font-semibold tracking-tight text-slate-900">Red Duck Lawyer</h1>
          <p className="mt-1 text-[13px] text-slate-500">Case briefs for your PI matters. Sign in to continue.</p>
        </div>

        <form onSubmit={submit} noValidate className="rounded-xl border border-line bg-surface p-6 shadow-card">
          {error && (
            <div role="alert" className="mb-4 rounded-lg border border-danger-200 bg-danger-50 px-3 py-2 text-[13px] text-danger-700">{error}</div>
          )}
          <label htmlFor="login-user" className="mb-1 block text-[12.5px] font-medium text-slate-700">Username</label>
          <input
            id="login-user" name="username" autoComplete="username" autoFocus value={username}
            onChange={(e) => setUsername(e.target.value)}
            className="mb-4 w-full rounded-lg border border-line bg-white px-3 py-2 text-[14px] text-slate-900 outline-none focus:border-brand-500 focus:ring-2 focus:ring-brand-100"
          />
          <label htmlFor="login-pass" className="mb-1 block text-[12.5px] font-medium text-slate-700">Password</label>
          <input
            id="login-pass" name="password" type="password" autoComplete="current-password" value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="mb-5 w-full rounded-lg border border-line bg-white px-3 py-2 text-[14px] text-slate-900 outline-none focus:border-brand-500 focus:ring-2 focus:ring-brand-100"
          />
          <button
            type="submit" disabled={busy}
            className="w-full cursor-pointer rounded-lg bg-brand-600 px-3 py-2.5 text-[14px] font-semibold text-white hover:bg-brand-700 disabled:cursor-wait disabled:opacity-70"
          >
            {busy ? 'Signing in…' : 'Sign in'}
          </button>
        </form>
        <p className="mt-4 text-center text-[12px] text-slate-400">Treating providers open their shared link directly; no sign-in needed.</p>
      </div>
    </div>
  )
}
