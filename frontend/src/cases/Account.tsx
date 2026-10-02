// Signed-in user + Sign out, shown only when firm sign-in is enabled.
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../auth/auth'

export function Account() {
  const { authEnabled, user, logout } = useAuth()
  const navigate = useNavigate()
  if (!authEnabled) return null
  return (
    <div className="flex items-center gap-2 text-[12.5px]">
      {user && <span className="hidden text-slate-500 sm:inline">{user}</span>}
      <button type="button" onClick={async () => { await logout(); navigate('/login') }}
        className="cursor-pointer rounded-md border border-line bg-surface px-2.5 py-1 font-medium text-slate-600 hover:bg-page hover:text-slate-900">
        Sign out
      </button>
    </div>
  )
}
