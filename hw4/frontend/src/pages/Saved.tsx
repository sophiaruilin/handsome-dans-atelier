import { Link } from 'react-router-dom'
import ProductCard from '../components/ProductCard'
import { usePrefs } from '../prefs/context'
import { useProductsById } from '../prefs/useProducts'

export default function Saved() {
  const { favorites, mySize } = usePrefs()
  const { products, loading } = useProductsById(favorites)

  return (
    <section className="page">
      <div className="page-head">
        <h1>Saved items</h1>
        <p className="lead">Your shortlist, with live prices and stock. Saved in this browser.</p>
      </div>
      {loading && <p className="muted">Loading…</p>}
      {!loading && products.length === 0 && (
        <div className="empty">
          <p className="empty-heart">♡</p>
          <p>Nothing saved yet. Tap the heart on any product to keep it here while you decide.</p>
          <Link to="/products" className="btn">
            Browse products
          </Link>
        </div>
      )}
      <div className="grid">
        {products.map((p) => (
          <ProductCard key={p.product_id} product={p} mySize={mySize} />
        ))}
      </div>
    </section>
  )
}
