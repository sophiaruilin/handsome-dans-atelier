import { Link } from 'react-router-dom'
import { formatPrice } from '../api'
import type { Product } from '../types'
import ColorSwatches from './ColorSwatches'
import FavoriteButton from './FavoriteButton'
import StockBadge from './StockBadge'
import WaitlistForm from './WaitlistForm'

// First sentence of the description, for the card. The full text is on the product page.
const shortDescription = (text: string) => text.match(/^.*?[.!?](\s|$)/)?.[0].trim() ?? text

interface Props {
  product: Product
  mySize?: string | null // when set, the card shows how many are left in the shopper's size
}

export default function ProductCard({ product, mySize }: Props) {
  const href = `/products/${product.product_id}`
  const inMySize = mySize ? product.inventory.find((s) => s.size === mySize) : undefined
  return (
    <article className={`card ${product.stock_status === 'sold_out' ? 'is-sold-out' : ''}`}>
      <FavoriteButton productId={product.product_id} />
      <Link to={href} className="card-link">
        <div className="card-image">
          <img src={product.image_url} alt={product.name} loading="lazy" />
          {inMySize && (
            <span className={`my-size-badge ${inMySize.status}`}>
              {inMySize.quantity === 0 ? `${mySize} sold out` : `${mySize}: ${inMySize.quantity} left`}
            </span>
          )}
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
