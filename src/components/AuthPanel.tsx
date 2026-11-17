import { useState } from 'react'
import { ArrowRight, LoaderCircle, LogOut } from 'lucide-react'
import { api } from '../api/client'

export function AuthPanel({ onChanged }: { onChanged: () => void }) {
  const [mode, setMode] = useState<'login' | 'register'>('login')
  const [role, setRole] = useState<'buyer' | 'seller'>('buyer')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [name, setName] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [loggedIn, setLoggedIn] = useState(Boolean(api.getToken()))

  const submit = async (event: React.FormEvent) => {
    event.preventDefault()
    setLoading(true)
    setError('')
    try {
      if (mode === 'register') {
        await api.register({ email, password, displayName: name || email.split('@')[0], role })
      }
      await api.login(email, password)
      setLoggedIn(true)
      onChanged()
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Authentication failed')
    } finally {
      setLoading(false)
    }
  }

  const logout = async () => {
    setLoading(true)
    try {
      await api.logout()
    } finally {
      setLoggedIn(false)
      setLoading(false)
      onChanged()
    }
  }

  if (loggedIn) return <aside className="account-note">
    <div className="eyebrow">CONNECTED ACCOUNT</div>
    <h3>Signed in securely.</h3>
    <p>Your cart and role-protected operations use the AURORA X API. Demo catalogue and checkout fallback remain available outside the session.</p>
    <button className="button button-secondary" type="button" onClick={logout} disabled={loading}>
      <LogOut size={15} /> {loading ? 'Signing out...' : 'Sign out'}
    </button>
  </aside>

  return <aside className="account-note">
    <div className="eyebrow">AURORA ACCOUNT</div>
    <div className="account-auth-tabs">
      <button type="button" className={mode === 'login' ? 'selected' : ''} onClick={() => setMode('login')}>Sign in</button>
      <button type="button" className={mode === 'register' ? 'selected' : ''} onClick={() => setMode('register')}>Register</button>
    </div>
    <form onSubmit={submit} className="account-auth-form">
      {mode === 'register' && <label className="field-label">Display name<input value={name} onChange={(event) => setName(event.target.value)} required /></label>}
      {mode === 'register' && <label className="field-label">Account type<select value={role} onChange={(event) => setRole(event.target.value as 'buyer' | 'seller')}><option value="buyer">Buyer</option><option value="seller">Seller</option></select></label>}
      <label className="field-label">Email<input type="email" value={email} onChange={(event) => setEmail(event.target.value)} required /></label>
      <label className="field-label">Password<input type="password" minLength={8} value={password} onChange={(event) => setPassword(event.target.value)} required /></label>
      {error && <small className="account-auth-error">{error}</small>}
      <button className="button button-primary" type="submit" disabled={loading}>
        {loading ? <LoaderCircle size={15} /> : <ArrowRight size={15} />}
        {mode === 'register' ? 'Create account' : 'Sign in'}
      </button>
    </form>
  </aside>
}
