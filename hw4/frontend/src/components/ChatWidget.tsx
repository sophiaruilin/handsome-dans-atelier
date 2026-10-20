import { useEffect, useRef, useState, type FormEvent } from 'react'
import Markdown from 'react-markdown'
import { Link, useMatch } from 'react-router-dom'
import { formatPrice, getChatHistory, sendChat } from '../api'
import { useAuth } from '../auth/context'
import type { ChatMessage, Product } from '../types'
import StockBadge from './StockBadge'

const greeting = (firstName?: string): ChatMessage => ({
  role: 'assistant',
  content: `Hi${firstName ? `, ${firstName}` : ''}! I'm the Campus Customs shop assistant. Ask me about sizes, colors or gift ideas.`,
})

function ChatCard({ product }: { product: Product }) {
  return (
    <Link to={`/products/${product.product_id}`} className="chat-card">
      <img src={product.image_url} alt="" />
      <span>
        <strong>{product.name}</strong>
        <span className="chat-card-meta">
          {formatPrice(product.price)} · <StockBadge status={product.stock_status} />
        </span>
      </span>
    </Link>
  )
}

// Floating chat panel, shown on every page. App remounts it when the shopper logs in or out
// (key = user id), so a logged-in shopper's saved chat loads and a guest starts fresh.
// It sends the product being viewed, if any, so "does this come in pink?" needs no extra detail.
export default function ChatWidget() {
  const { user } = useAuth()
  const [open, setOpen] = useState(false)
  const [messages, setMessages] = useState<ChatMessage[]>([greeting(user?.first_name)])
  const [draft, setDraft] = useState('')
  const [sending, setSending] = useState(false)
  const listRef = useRef<HTMLDivElement>(null)
  const productId = useMatch('/products/:productId')?.params.productId

  useEffect(() => {
    if (!user) return
    getChatHistory()
      .then((saved) => saved.length && setMessages([greeting(user.first_name), ...saved]))
      .catch(() => {})
  }, [user])

  useEffect(() => {
    listRef.current?.scrollTo({ top: listRef.current.scrollHeight })
  }, [messages, open, sending])

  async function send(e: FormEvent) {
    e.preventDefault()
    const text = draft.trim()
    if (!text || sending) return
    const history = messages.slice(1) // skip the greeting
    setMessages((m) => [...m, { role: 'user', content: text }])
    setDraft('')
    setSending(true)
    try {
      const res = await sendChat(text, history, productId)
      setMessages((m) => [...m, { role: 'assistant', content: res.reply, products: res.products }])
    } catch (err) {
      const reason = err instanceof Error ? err.message : ''
      setMessages((m) => [
        ...m,
        { role: 'assistant', content: reason || "Sorry, I can't reach the shop right now. Please try again in a moment." },
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
              <div key={i} className={`bubble ${m.role}`}>
                {m.role === 'assistant' ? <Markdown>{m.content}</Markdown> : m.content}
                {!!m.products?.length && (
                  <div className="chat-cards">
                    {m.products.map((p) => (
                      <ChatCard key={p.product_id} product={p} />
                    ))}
                  </div>
                )}
              </div>
            ))}
            {sending && <p className="bubble assistant typing">Looking that up…</p>}
          </div>
          <form className="chat-input" onSubmit={send}>
            <input
              value={draft}
              onChange={(e) => setDraft(e.target.value)}
              placeholder={productId ? 'Ask about this item…' : 'Ask about sizes, colors, gifts…'}
              aria-label="Message"
              maxLength={2000}
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
