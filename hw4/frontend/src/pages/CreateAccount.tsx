import { useState, type FormEvent } from 'react'
import { Link } from 'react-router-dom'

// Form only for now: fields match the users table (first_name, last_name, email, password).
export default function CreateAccount() {
  const [note, setNote] = useState('')

  function submit(e: FormEvent) {
    e.preventDefault()
    setNote('Accounts are coming soon. For now, browse as a guest.')
  }

  return (
    <section className="page auth">
      <h1>Join the Bulldog crowd</h1>
      <p className="muted">Save your chats and get back-in-stock alerts in one place.</p>
      <form onSubmit={submit} className="auth-form">
        <div className="row">
          <label>
            First name
            <input required autoComplete="given-name" />
          </label>
          <label>
            Last name
            <input required autoComplete="family-name" />
          </label>
        </div>
        <label>
          Email
          <input type="email" required autoComplete="email" placeholder="you@yale.edu" />
        </label>
        <label>
          Password
          <input type="password" required minLength={8} autoComplete="new-password" />
        </label>
        <button type="submit" className="btn">
          Create account
        </button>
        {note && <p className="muted">{note}</p>}
      </form>
      <p>
        Already have an account? <Link to="/login">Log in</Link>
      </p>
    </section>
  )
}
