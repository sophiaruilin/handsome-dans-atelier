import { useState, type FormEvent } from 'react'
import { joinWaitlist } from '../api'

interface Props {
  productId: string
  size?: string
}

export default function WaitlistForm({ productId, size }: Props) {
  const [email, setEmail] = useState('')
  const [status, setStatus] = useState<'idle' | 'saving' | 'done' | 'error'>('idle')
  const [message, setMessage] = useState('')

  async function submit(e: FormEvent) {
    e.preventDefault()
    setStatus('saving')
    try {
      const res = await joinWaitlist(productId, email, size)
      setStatus('done')
      setMessage(res.message)
    } catch (err) {
      setStatus('error')
      setMessage(err instanceof Error ? err.message : 'Something went wrong.')
    }
  }

  if (status === 'done') return <p className="waitlist-done">✓ {message}</p>

  return (
    <form className="waitlist" onSubmit={submit}>
      <label>
        <span>Get an email when {size ? `size ${size} is` : "it's"} back in stock</span>
        <input
          type="email"
          required
          placeholder="you@yale.edu"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
        />
      </label>
      <button type="submit" className="btn btn-small" disabled={status === 'saving'}>
        {status === 'saving' ? 'Adding…' : 'Add to waitlist'}
      </button>
      {status === 'error' && <p className="error">{message}</p>}
    </form>
  )
}
