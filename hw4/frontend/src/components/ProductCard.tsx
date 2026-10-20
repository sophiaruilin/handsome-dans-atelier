import { Link } from 'react-router-dom'
import { formatPrice } from '../api'
import type { Product } from '../types'
import ColorSwatches from './ColorSwatches'
import StockBadge from './StockBadge'
import WaitlistForm from './WaitlistForm'

// First sentence of the description, for the card. The full text is on the product page.
const shortDescription = (text: string) => text.match(/^.*?[.!?](\s|$)/)?.[0].trim() ?? text

export default function ProductCard({ product }: { product: Product }) {
  const href = `/products/${product.product_id}`
  return (
    <article className={`card ${product.stock_status === 'sold_out' ? 'is-sold-out' : ''}`}>
      <Link to={href} className="card-link">
        <div className="card-image">
          <img src={product.image_url} alt={product.name} loading="lazy" />
        </div>
        <div className="card-body">
          <p className="eyebrow">{product.garment_type}</p>
          <h3>{product.name}</h3>
          <p className="card-desc">{shortDescription(product.description)}</p>
          <div className="card-meta">
            <span className="price">{formatPrice(product.price)}</span>
            <StockBadge status={product.stock_status} />
          </div>
          <ColorSwatches colors={product.colors} />
        </div>
      </Link>
      {product.stock_status === 'sold_out' && (
        <div className="card-waitlist">
          <WaitlistForm productId={product.product_id} />
        </div>
      )}
    </article>
  )
}
