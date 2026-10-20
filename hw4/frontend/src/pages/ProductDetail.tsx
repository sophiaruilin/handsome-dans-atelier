import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { formatPrice, getProduct } from '../api'
import ColorSwatches from '../components/ColorSwatches'
import StockBadge from '../components/StockBadge'
import WaitlistForm from '../components/WaitlistForm'
import type { Product } from '../types'

export default function ProductDetail() {
  const { productId = '' } = useParams()
  // Results and the chosen size are tagged with their product id, so moving to another product resets them.
  const [loaded, setLoaded] = useState<{ id: string; product?: Product; error?: string } | null>(null)
  const [choice, setChoice] = useState<{ id: string; size: string } | null>(null)

  useEffect(() => {
    getProduct(productId)
      .then((product) => setLoaded({ id: productId, product }))
      .catch((e: Error) => setLoaded({ id: productId, error: e.message }))
  }, [productId])

  const current = loaded?.id === productId ? loaded : null
  const product = current?.product ?? null
  const error = current?.error ?? ''
  const selected = choice?.id === productId ? choice.size : null
  const setSelected = (size: string) => setChoice({ id: productId, size })

  if (error) {
    return (
      <section className="page">
        <p className="error">{error}</p>
        <Link to="/products">← Back to all products</Link>
      </section>
    )
  }
  if (!product) return <section className="page muted">Loading…</section>

  const size = product.inventory.find((s) => s.size === selected)

  return (
    <section className="page">
      <Link to="/products" className="back">
        ← All products
      </Link>
      <div className="detail">
        <div className="detail-image">
          <img src={product.image_url} alt={product.name} />
        </div>

        <div className="detail-info">
          <p className="eyebrow">{product.garment_type}</p>
          <h1>{product.name}</h1>
          <div className="detail-price">
            <span className="price">{formatPrice(product.price)}</span>
            <StockBadge status={product.stock_status} />
          </div>
          <p>{product.description}</p>

          <h2>Colors</h2>
          <ColorSwatches colors={product.colors} showNames />

          <h2>Size</h2>
          <div className="sizes">
            {product.inventory.map((s) => (
              <button
                key={s.size}
                className={`size ${s.status} ${selected === s.size ? 'selected' : ''}`}
                onClick={() => setSelected(s.size)}
                aria-pressed={selected === s.size}
                title={s.status === 'sold_out' ? 'Sold out: join the waitlist' : `${s.quantity} left`}
              >
                <strong>{s.size}</strong>
                <small>{s.status === 'sold_out' ? 'Sold out' : `${s.quantity} left`}</small>
              </button>
            ))}
          </div>

          {size?.status === 'selling_fast' && (
            <p className="stock selling-fast">
              <span aria-hidden="true">🔥</span> Selling fast! Only {size.quantity} left in {size.size}.
            </p>
          )}
          {size?.status === 'in_stock' && (
            <p className="stock in-stock">
              Size {size.size} is in stock ({size.quantity} available).
            </p>
          )}
          {size?.status === 'sold_out' && (
            <div className="detail-waitlist">
              <p className="stock sold-out">Size {size.size} is sold out.</p>
              <WaitlistForm key={size.size} productId={product.product_id} size={size.size} />
            </div>
          )}
          {!size && <p className="muted">Pick a size to check availability.</p>}
          {product.stock_status === 'sold_out' && !size && <WaitlistForm productId={product.product_id} />}

          <p className="muted visit">
            Want to try it on? Visit us at <strong>57 Broadway, New Haven</strong>.
          </p>

          <ul className="tags">
            {product.search_tags.map((t) => (
              <li key={t}>{t}</li>
            ))}
          </ul>
        </div>
      </div>
    </section>
  )
}
