import { useState, type FormEvent } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '../auth/context'

export default function Login() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const from = (useLocation().state as { from?: string } | null)?.from ?? '/'
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  async function submit(e: FormEvent) {
    e.preventDefault()
    setError('')
    setBusy(true)
    try {
      await login(email, password)
      navigate(from, { replace: true })
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Something went wrong.')
      setPassword('')
    } finally {
      setBusy(false)
    }
  }

  return (
    <section className="page auth">
      <h1>Welcome back</h1>
      <p className="muted">Log in to pick up your chat where you left off.</p>
      <form onSubmit={submit} className="auth-form">
        <label>
          Email
          <input
            type="email"
            required
            autoComplete="email"
            placeholder="you@yale.edu"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
        </label>
        <label>
          Password
          <input
            type="password"
            required
            autoComplete="current-password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
        </label>
        {error && (
          <p className="error" role="alert">
            {error}
          </p>
        )}
        <button type="submit" className="btn" disabled={busy}>
          {busy ? 'Logging in…' : 'Log in'}
        </button>
      </form>
      <p>
        New here? <Link to="/create-account">Create an account</Link>
      </p>
    </section>
  )
}
