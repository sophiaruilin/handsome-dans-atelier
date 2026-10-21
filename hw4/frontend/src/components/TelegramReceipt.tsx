import { Link } from 'react-router-dom'
import { formatPrice } from '../api'
import type { Order } from '../types'
import Dan from './Dan'

const caps = (s: string) => s.toUpperCase()

function longDate(iso: string) {
  return new Date(`${iso}T12:00:00`).toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric' })
}

// The order confirmation as a Victorian telegram from Handsome Dan, with typewriter tape
// strips, "STOP"s, a rubber stamp and the gift card tucked underneath.
export default function TelegramReceipt({ order }: { order: Order }) {
  const placed = new Date(order.created_at.replace(' ', 'T') + 'Z')
  const count = order.items.reduce((n, i) => n + i.quantity, 0)
  const lines = [
    `TO ${caps(order.name)}`,
    'RESERVATION CONFIRMED STOP',
    `${count} ${count === 1 ? 'ITEM' : 'ITEMS'} HELD FOR YOU AT 57 BROADWAY NEW HAVEN STOP`,
    `PICK UP AND PAY IN STORE BY ${caps(longDate(order.pickup_by))} STOP`,
    ...(order.gift_wrap ? ['WRAPPED IN OUR FINEST TOILE WITH YOUR CARD STOP'] : []),
    'BOOLA BOOLA STOP',
  ]

  return (
    <div className="telegram-wrap">
      <article className="telegram" aria-label={`Order ${order.order_number} confirmation`}>
        <header className="telegram-head">
          <span className="telegram-seal">
            <Dan size={54} />
          </span>
          <div>
            <p className="telegram-company">Campus Customs Telegraph Co.</p>
            <p className="telegram-sub">Received at 57 Broadway, New Haven, Conn. · Yale Bulldog Blue</p>
          </div>
        </header>
        <dl className="telegram-meta">
          <div>
            <dt>No.</dt>
            <dd>{order.order_number}</dd>
          </div>
          <div>
            <dt>Date</dt>
            <dd>{placed.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}</dd>
          </div>
          <div>
            <dt>Time</dt>
            <dd>{placed.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' })}</dd>
          </div>
          <div>
            <dt>Class</dt>
            <dd>Urgent · Paws-itively</dd>
          </div>
        </dl>

        <div className="telegram-body">
          {lines.map((l) => (
            <p key={l} className="tape">
              {l}
            </p>
          ))}
          <ul className="telegram-items">
            {order.items.map((i) => (
              <li key={`${i.product_id}-${i.size}`} className="tape">
                <span>
                  {i.quantity} X {caps(i.name)} SIZE {i.size}
                </span>
                <span>{formatPrice(i.unit_price * i.quantity)}</span>
              </li>
            ))}
            <li className="tape total">
              <span>TOTAL DUE AT PICKUP</span>
              <span>{formatPrice(order.subtotal)}</span>
            </li>
          </ul>
          <p className="tape signature">HANDSOME DAN</p>
        </div>

        <div className="telegram-stamp" aria-hidden="true">
          <span>Reserved</span>
          <small>57 Broadway</small>
        </div>
        <p className="telegram-foot">Confirmation also sent to {order.email}. Please present this message at the counter.</p>
      </article>

      {order.gift_wrap && (
        <div className="gift-card-preview telegram-gift">
          <p className="gift-card-label">Tucked inside the toile wrapping:</p>
          <p className="handwritten">{order.gift_note || 'Boola Boola!'}</p>
        </div>
      )}

      <Link to="/products" className="btn">
        Keep shopping
      </Link>
    </div>
  )
}
