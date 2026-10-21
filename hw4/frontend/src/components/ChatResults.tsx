import { formatPrice } from '../api'
import type { PageResults, SearchFilters } from '../types'
import ProductCard from './ProductCard'

// Human-readable chips for the filters the agent searched with.
function filterChips(f: SearchFilters): string[] {
  const chips = []
  if (f.query) chips.push(`“${f.query}”`)
  if (f.garment_type) chips.push(f.garment_type)
  if (f.color) chips.push(f.color)
  if (f.max_price !== null) chips.push(`under ${formatPrice(f.max_price)}`)
  if (f.size) chips.push(`size ${f.size.toUpperCase()} in stock`)
  if (f.in_stock_only) chips.push('in stock')
  return chips
}

interface Props {
  results: PageResults
  version: number
  onClear: () => void
}

// Products the shop assistant found, rendered with the same ProductCard as the full catalogue,
// so clicking one opens the single-item page exactly like any other card.
export default function ChatResults({ results, version, onClear }: Props) {
  return (
    <section className="chat-results" aria-live="polite">
      <div className="chat-results-head">
        <div>
          <p className="eyebrow">💬 From your chat with the shop assistant</p>
          <h2>{results.title}</h2>
          <p className="muted">
            You asked: <em>“{results.shopper_message}”</em> · {results.total_matches}{' '}
            {results.total_matches === 1 ? 'match' : 'matches'}
          </p>
          <ul className="tags">
            {filterChips(results.filters).map((c) => (
              <li key={c}>{c}</li>
            ))}
          </ul>
        </div>
        <button className="btn btn-small btn-outline" onClick={onClear}>
          Show all products
        </button>
      </div>
      {/* key={version} remounts the grid on each new search so the cards animate in again. */}
      <div className="grid" key={version}>
        {results.products.map((p, i) => (
          <div key={p.product_id} className="pop-in" style={{ animationDelay: `${Math.min(i, 12) * 45}ms` }}>
            <ProductCard product={p} />
          </div>
        ))}
      </div>
    </section>
  )
}
