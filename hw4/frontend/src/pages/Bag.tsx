import { useState, type FormEvent } from 'react'
import { Link } from 'react-router-dom'
import { formatPrice, reserveOrder } from '../api'
import { useAuth } from '../auth/context'
import { useBag } from '../cart/context'
import Dan from '../components/Dan'
import TelegramReceipt from '../components/TelegramReceipt'
import { danDo } from '../dan/danBus'
import type { Order } from '../types'

const GIFT_NOTE_MAX = 240

export default function Bag() {
  const bag = useBag()
  const { user } = useAuth()
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [giftWrap, setGiftWrap] = useState(false)
  const [giftNote, setGiftNote] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [order, setOrder] = useState<Order | null>(null)

  // Logged-in shoppers don't need to type their details.
  const shopperName = name || (user ? `${user.first_name} ${user.last_name}` : '')
  const shopperEmail = email || user?.email || ''

  async function reserve(e: FormEvent) {
    e.preventDefault()
    setBusy(true)
    setError('')
    try {
      const placed = await reserveOrder({
        items: bag.items.map(({ product_id, size, quantity }) => ({ product_id, size, quantity })),
        name: shopperName,
        email: shopperEmail,
        gift_wrap: giftWrap,
        gift_note: giftWrap ? giftNote : '',
      })
      setOrder(placed)
      bag.clear()
      window.scrollTo({ top: 0, behavior: 'smooth' })
      danDo('cartwheel') // the big finish
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Something went wrong. Please try again.')
    } finally {
      setBusy(false)
    }
  }

  if (order) {
    return (
      <section className="page">
        <TelegramReceipt order={order} />
      </section>
    )
  }

  if (bag.items.length === 0) {
    return (
      <section className="page">
        <div className="empty">
          <Dan size={120} />
          <h1>Your bag is empty</h1>
          <p>Handsome Dan is sitting here very patiently. Find something worthy of him.</p>
          <Link to="/products" className="btn">
            Shop the collection
          </Link>
        </div>
      </section>
    )
  }

  return (
    <section className="page">
      <div className="page-head">
        <p className="eyebrow">Reserve online · Pick up at 57 Broadway</p>
        <h1>Your bag</h1>
      </div>
      <div className="bag-layout">
        <ul className="bag-items">
          {bag.items.map((i) => (
            <li key={`${i.product_id}-${i.size}`} className="bag-item">
              <Link to={`/products/${i.product_id}`}>
                <img src={i.image_url} alt={i.name} />
              </Link>
              <div>
                <Link to={`/products/${i.product_id}`} className="bag-name">
                  {i.name}
                </Link>
                <p className="muted">Size {i.size}</p>
                <div className="stepper" aria-label={`Quantity of ${i.name}`}>
                  <button onClick={() => bag.setQuantity(i.product_id, i.size, i.quantity - 1)} disabled={i.quantity <= 1}>
                    −
                  </button>
                  <span>{i.quantity}</span>
                  <button onClick={() => bag.setQuantity(i.product_id, i.size, i.quantity + 1)} disabled={i.quantity >= i.max}>
                    +
                  </button>
                </div>
              </div>
              <div className="bag-line-end">
                <strong>{formatPrice(i.price * i.quantity)}</strong>
                <button className="link-button" onClick={() => bag.remove(i.product_id, i.size)}>
                  Remove
                </button>
              </div>
            </li>
          ))}
        </ul>

        <form className="checkout" onSubmit={reserve}>
          <h2>Reserve for pickup</h2>
          <p className="muted">
            No payment online: we set your items aside at <strong>57 Broadway</strong> for 3 days, and you pay when you pick
            them up.
          </p>

          <label className={`gift-toggle ${giftWrap ? 'on' : ''}`}>
            <input type="checkbox" checked={giftWrap} onChange={(e) => setGiftWrap(e.target.checked)} />
            <span className="toile-swatch" aria-hidden="true" />
            <span>
              <strong>Gift wrap in Campus Customs toile</strong>
              <small>Free · with a handwritten card</small>
            </span>
          </label>
          {giftWrap && (
            <div className="gift-note">
              <label>
                Gift card message
                <textarea
                  value={giftNote}
                  maxLength={GIFT_NOTE_MAX}
                  onChange={(e) => setGiftNote(e.target.value)}
                  placeholder="Congrats on surviving your first midterms! Love, Mom"
                  rows={3}
                />
              </label>
              <small className="muted">
                {giftNote.length}/{GIFT_NOTE_MAX}
              </small>
              <div className="gift-card-preview">
                <p className="handwritten">{giftNote || 'Your message, in our finest penmanship.'}</p>
              </div>
            </div>
          )}

          <label>
            Name for the reservation
            <input required value={shopperName} onChange={(e) => setName(e.target.value)} autoComplete="name" />
          </label>
          <label>
            Email for your confirmation
            <input
              required
              type="email"
              value={shopperEmail}
              onChange={(e) => setEmail(e.target.value)}
              autoComplete="email"
              placeholder="you@yale.edu"
            />
          </label>

          <p className="checkout-total">
            Subtotal <strong>{formatPrice(bag.subtotal)}</strong>
          </p>
          {error && (
            <p className="error" role="alert">
              {error}
            </p>
          )}
          <button type="submit" className="btn btn-brass" disabled={busy}>
            {busy ? 'Reserving…' : `Reserve ${bag.count} ${bag.count === 1 ? 'item' : 'items'} for pickup`}
          </button>
        </form>
      </div>
    </section>
  )
}
