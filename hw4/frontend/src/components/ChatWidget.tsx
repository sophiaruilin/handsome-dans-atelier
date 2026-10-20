import { useEffect, useRef, useState, type FormEvent } from 'react'
import { useMatch } from 'react-router-dom'
import { sendChat } from '../api'
import type { ChatMessage } from '../types'

const GREETING: ChatMessage = {
  role: 'assistant',
  content: "Hi! I'm the Campus Customs shop assistant. Ask me about sizes, colors or gift ideas.",
}

// Floating chat panel, shown on every page. It sends the product being viewed, if any,
// so the Problem 5 agent can answer "does this come in navy?" without being told which item.
export default function ChatWidget() {
  const [open, setOpen] = useState(false)
  const [messages, setMessages] = useState<ChatMessage[]>([GREETING])
  const [draft, setDraft] = useState('')
  const [sending, setSending] = useState(false)
  const listRef = useRef<HTMLDivElement>(null)
  const productId = useMatch('/products/:productId')?.params.productId

  useEffect(() => {
    listRef.current?.scrollTo({ top: listRef.current.scrollHeight })
  }, [messages, open])

  async function send(e: FormEvent) {
    e.preventDefault()
    const text = draft.trim()
    if (!text || sending) return
    const history = messages.slice(1) // skip the canned greeting
    setMessages((m) => [...m, { role: 'user', content: text }])
    setDraft('')
    setSending(true)
    try {
      const res = await sendChat(text, history, productId)
      setMessages((m) => [...m, { role: 'assistant', content: res.reply }])
    } catch {
      setMessages((m) => [
        ...m,
        { role: 'assistant', content: "Sorry, I can't reach the shop right now. Please try again in a moment." },
      ])
    } finally {
      setSending(false)
    }
  }

  return (
    <div className="chat">
      {open && (
        <section className="chat-panel" aria-label="Shop assistant chat">
          <header>
            <div>
              <strong>Shop assistant</strong>
              <small>Campus Customs</small>
            </div>
            <button className="chat-close" onClick={() => setOpen(false)} aria-label="Close chat">
              ×
            </button>
          </header>
          <div className="chat-messages" ref={listRef}>
            {messages.map((m, i) => (
              <p key={i} className={`bubble ${m.role}`}>
                {m.content}
              </p>
            ))}
            {sending && <p className="bubble assistant typing">…</p>}
          </div>
          <form className="chat-input" onSubmit={send}>
            <input
              value={draft}
              onChange={(e) => setDraft(e.target.value)}
              placeholder="Ask about sizes, colors, gifts…"
              aria-label="Message"
              autoFocus
            />
            <button type="submit" className="btn btn-small" disabled={sending || !draft.trim()}>
              Send
            </button>
          </form>
        </section>
      )}
      <button className="chat-toggle" onClick={() => setOpen((o) => !o)} aria-expanded={open}>
        {open ? '×' : '💬'}
        <span className="sr-only">{open ? 'Close chat' : 'Open chat'}</span>
      </button>
    </div>
  )
}
