import { Link } from 'react-router-dom'
import { formatPrice } from '../api'
import type { Product } from '../types'
import StockBadge from './StockBadge'

// A compact horizontal row of products ("You might also like", "Recently viewed").
export default function ProductStrip({ title, products }: { title: string; products: Product[] }) {
  if (!products.length) return null
  return (
    <section className="strip">
      <h2>{title}</h2>
      <div className="strip-row">
        {products.map((p) => (
          <Link key={p.product_id} to={`/products/${p.product_id}`} className="strip-item">
            <div className="strip-image">
              <img src={p.image_url} alt="" loading="lazy" />
            </div>
            <strong>{p.name}</strong>
            <span>
              {formatPrice(p.price)} · <StockBadge status={p.stock_status} />
            </span>
          </Link>
        ))}
      </div>
    </section>
  )
}
