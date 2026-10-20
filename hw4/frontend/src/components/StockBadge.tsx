import type { StockStatus } from '../types'

export default function StockBadge({ status }: { status: StockStatus }) {
  if (status === 'selling_fast') {
    return (
      <span className="stock selling-fast">
        <span aria-hidden="true">🔥</span> Selling fast!
      </span>
    )
  }
  if (status === 'sold_out') return <span className="stock sold-out">Sold out</span>
  return <span className="stock in-stock">In stock</span>
}
