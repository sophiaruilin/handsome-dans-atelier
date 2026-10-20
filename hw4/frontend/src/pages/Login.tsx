import { useState, type FormEvent } from 'react'
import { Link } from 'react-router-dom'

// Form only for now: the back end gets login and sign-up routes when accounts are wired in.
export default function Login() {
  const [note, setNote] = useState('')

  function submit(e: FormEvent) {
    e.preventDefault()
    setNote('Accounts are coming soon. For now, browse as a guest.')
  }

  return (
    <section className="page auth">
      <h1>Welcome back</h1>
      <p className="muted">Log in to pick up your chat where you left off.</p>
      <form onSubmit={submit} className="auth-form">
        <label>
          Email
          <input type="email" required autoComplete="email" placeholder="you@yale.edu" />
        </label>
        <label>
          Password
          <input type="password" required autoComplete="current-password" />
        </label>
        <button type="submit" className="btn">
          Log in
        </button>
        {note && <p className="muted">{note}</p>}
      </form>
      <p>
        New here? <Link to="/create-account">Create an account</Link>
      </p>
    </section>
  )
}
