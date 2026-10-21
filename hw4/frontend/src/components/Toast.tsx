import { useEffect, useState } from 'react'
import { onToast } from '../dan/toast'

// Small confirmation at the bottom of the screen ("Added to your bag").
export default function Toast() {
  const [msg, setMsg] = useState<{ text: string; id: number } | null>(null)
  useEffect(() => onToast((text) => setMsg({ text, id: Date.now() })), [])
  useEffect(() => {
    if (!msg) return
    const t = window.setTimeout(() => setMsg(null), 2600)
    return () => window.clearTimeout(t)
  }, [msg])
  if (!msg) return null
  return (
    <div className="toast" role="status" key={msg.id}>
      {msg.text}
    </div>
  )
}
