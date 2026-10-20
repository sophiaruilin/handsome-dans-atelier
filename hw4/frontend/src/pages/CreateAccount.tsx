import { useState, type ChangeEvent, type FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import type { SignupForm } from '../api'
import { useAuth } from '../auth/context'
import { passwordRules } from '../auth/passwordRules'

const EMPTY: SignupForm = { first_name: '', last_name: '', email: '', password: '', confirm_password: '' }

// Fields match the users table (first_name, last_name, email, password_hash).
export default function CreateAccount() {
  const { signup } = useAuth()
  const navigate = useNavigate()
  const [form, setForm] = useState<SignupForm>(EMPTY)
  const [showPassword, setShowPassword] = useState(false)
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  const set = (field: keyof SignupForm) => (e: ChangeEvent<HTMLInputElement>) =>
    setForm((f) => ({ ...f, [field]: e.target.value }))

  const rules = passwordRules(form.password, form.email, form.first_name, form.last_name)
  const matches = form.confirm_password.length > 0 && form.password === form.confirm_password
  const ready = rules.every((r) => r.ok) && matches

  async function submit(e: FormEvent) {
    e.preventDefault()
    if (!ready) return
    setError('')
    setBusy(true)
    try {
      await signup(form)
      navigate('/', { replace: true })
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Something went wrong.')
    } finally {
      setBusy(false)
    }
  }

  return (
    <section className="page auth">
      <h1>Join the Bulldog crowd</h1>
      <p className="muted">Save your chats and get back-in-stock alerts in one place.</p>
      <form onSubmit={submit} className="auth-form">
        <div className="row">
          <label>
            First name
            <input required autoComplete="given-name" value={form.first_name} onChange={set('first_name')} />
          </label>
          <label>
            Last name
            <input required autoComplete="family-name" value={form.last_name} onChange={set('last_name')} />
          </label>
        </div>
        <label>
          Email
          <input
            type="email"
            required
            autoComplete="email"
            placeholder="you@yale.edu"
            value={form.email}
            onChange={set('email')}
          />
        </label>
        <label>
          Password
          <input
            type={showPassword ? 'text' : 'password'}
            required
            autoComplete="new-password"
            value={form.password}
            onChange={set('password')}
            aria-describedby="password-rules"
          />
        </label>
        <ul id="password-rules" className="rules">
          {rules.map((r) => (
            <li key={r.label} className={r.ok ? 'ok' : ''}>
              {r.ok ? '✓' : '○'} {r.label}
            </li>
          ))}
        </ul>
        <label>
          Confirm password
          <input
            type={showPassword ? 'text' : 'password'}
            required
            autoComplete="new-password"
            value={form.confirm_password}
            onChange={set('confirm_password')}
          />
        </label>
        {form.confirm_password && (
          <p className={matches ? 'match ok' : 'match error'}>
            {matches ? '✓ Passwords match' : "Passwords don't match yet"}
          </p>
        )}
        <label className="checkbox">
          <input type="checkbox" checked={showPassword} onChange={(e) => setShowPassword(e.target.checked)} />
          Show passwords
        </label>
        {error && (
          <p className="error" role="alert">
            {error}
          </p>
        )}
        <button type="submit" className="btn" disabled={!ready || busy}>
          {busy ? 'Creating account…' : 'Create account'}
        </button>
      </form>
      <p>
        Already have an account? <Link to="/login">Log in</Link>
      </p>
    </section>
  )
}
