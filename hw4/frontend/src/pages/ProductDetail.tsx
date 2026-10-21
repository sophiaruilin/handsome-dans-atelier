import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { formatPrice, getProduct, getSimilar } from '../api'
import { askChat } from '../chat/askChat'
import ColorSwatches from '../components/ColorSwatches'
import FavoriteButton from '../components/FavoriteButton'
import ProductStrip from '../components/ProductStrip'
import StockBadge from '../components/StockBadge'
import WaitlistForm from '../components/WaitlistForm'
import { usePrefs } from '../prefs/context'
import { useProductsById } from '../prefs/useProducts'
import type { Product } from '../types'

export default function ProductDetail() {
  const { productId = '' } = useParams()
  const { mySize, setMySize, recent, addRecent } = usePrefs()
  // Results and the chosen size are tagged with their product id, so moving to another product resets them.
  const [loaded, setLoaded] = useState<{ id: string; product?: Product; error?: string } | null>(null)
  const [similar, setSimilar] = useState<{ id: string; products: Product[] } | null>(null)
  const [choice, setChoice] = useState<{ id: string; size: string } | null>(null)
  const { products: recentProducts } = useProductsById(recent.filter((id) => id !== productId).slice(0, 6))

  useEffect(() => {
    getProduct(productId)
      .then((product) => {
        setLoaded({ id: productId, product })
        addRecent(productId)
      })
      .catch((e: Error) => setLoaded({ id: productId, error: e.message }))
    getSimilar(productId)
      .then((products) => setSimilar({ id: productId, products }))
      .catch(() => setSimilar({ id: productId, products: [] }))
  }, [productId, addRecent])

  const current = loaded?.id === productId ? loaded : null
  const product = current?.product ?? null
  const error = current?.error ?? ''
  // Pre-select the shopper's saved size until they pick another one on this page.
  const selected = choice?.id === productId ? choice.size : mySize
  const setSelected = (size: string) => {
    setChoice({ id: productId, size })
    setMySize(size)
  }

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

          <h2>Size {mySize && <small className="muted">· your size is saved ({mySize})</small>}</h2>
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

          <div className="detail-actions">
            <FavoriteButton productId={product.product_id} label />
            <button
              type="button"
              className="btn btn-small btn-outline"
              onClick={() =>
                askChat(
                  size?.status === 'sold_out'
                    ? `Size ${size.size} is sold out. What similar styles do you have in ${size.size}?`
                    : 'Is this a good gift? What would you pair it with?',
                )
              }
            >
              💬 Ask about this item
            </button>
          </div>

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

      <ProductStrip title="You might also like" products={similar?.id === productId ? similar.products : []} />
      <ProductStrip title="Recently viewed" products={recentProducts} />
    </section>
  )
}
