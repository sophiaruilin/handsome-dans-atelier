import { useEffect, useRef, useState, type FormEvent } from 'react'
import Markdown from 'react-markdown'
import { Link, useLocation, useMatch, useNavigate } from 'react-router-dom'
import { clearChatHistory, formatPrice, getChatHistory, sendChat } from '../api'
import { useAuth } from '../auth/context'
import { useChatResults } from '../chat/context'
import type { ChatMessage, PageContext, PageResults, Product } from '../types'
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
  const chatResults = useChatResults()
  const navigate = useNavigate()
  const { pathname } = useLocation()

  // Put a search on the Products page (the cards there open the single-item page as usual).
  function showOnPage(results: PageResults) {
    chatResults.show(results)
    if (pathname !== '/products') navigate('/products')
    else window.scrollTo({ top: 0, behavior: 'smooth' })
  }

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
      // Ids only: the back end looks up the product itself, so "do you have this in pink?" works.
      const page: PageContext = {
        path: pathname,
        product_id: productId ?? null,
        results_title: pathname === '/products' ? (chatResults.results?.title ?? null) : null,
      }
      const res = await sendChat(text, history, page)
      const pageResults = res.page_results ?? undefined
      setMessages((m) => [...m, { role: 'assistant', content: res.reply, products: res.products, pageResults }])
      if (pageResults) showOnPage(pageResults)
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

  async function newChat() {
    if (user && !window.confirm('Start a new chat? This clears your saved chat history.')) return
    if (user) await clearChatHistory().catch(() => {})
    setMessages([greeting(user?.first_name)])
  }

  return (
    <div className="chat">
      {open && (
        <section className="chat-panel" aria-label="Shop assistant chat">
          <header>
            <div>
              <strong>Shop assistant</strong>
              <small>{user ? '💾 Chat saved to your account' : 'Guest chat · log in to save it'}</small>
            </div>
            <div className="chat-actions">
              <button className="chat-new" onClick={newChat} disabled={sending || messages.length < 2}>
                New chat
              </button>
              <button className="chat-close" onClick={() => setOpen(false)} aria-label="Close chat">
                ×
              </button>
            </div>
          </header>
          <div className="chat-messages" ref={listRef}>
            {messages.map((m, i) => (
              <div key={i} className={`bubble ${m.role}`}>
                {m.role === 'assistant' ? <Markdown>{m.content}</Markdown> : m.content}
                {m.pageResults && (
                  <button type="button" className="on-page-note" onClick={() => showOnPage(m.pageResults!)}>
                    📍 {m.pageResults.total_matches} {m.pageResults.total_matches === 1 ? 'match' : 'matches'} showing
                    on the page{pathname === '/products' && chatResults.results === m.pageResults ? '' : ' · view'}
                  </button>
                )}
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
