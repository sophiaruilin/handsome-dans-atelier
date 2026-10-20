import { useEffect, useMemo, useState } from 'react'
import { getProducts } from '../api'
import ProductCard from '../components/ProductCard'
import type { Product } from '../types'

// Group the catalogue's free-text garment types into a few shopper-friendly filters.
const FILTERS: { label: string; match: (g: string) => boolean }[] = [
  { label: 'All', match: () => true },
  { label: 'Hoodies', match: (g) => g.includes('hood') },
  { label: 'Crewnecks', match: (g) => g.includes('crew') && !g.includes('t-shirt') && !g.includes('hood') },
  { label: 'T-shirts', match: (g) => g.includes('t-shirt') || (g.includes('shirt') && !g.includes('sweat')) },
  { label: 'Quarter-zips', match: (g) => g.includes('quarter-zip') },
  { label: 'Jackets & fleece', match: (g) => g.includes('jacket') || g.includes('fleece') },
]

export default function Products() {
  const [products, setProducts] = useState<Product[]>([])
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState('All')
  const [query, setQuery] = useState('')

  useEffect(() => {
    getProducts()
      .then(setProducts)
      .catch((e: Error) => setError(e.message))
      .finally(() => setLoading(false))
  }, [])

  const shown = useMemo(() => {
    const active = FILTERS.find((f) => f.label === filter) ?? FILTERS[0]
    const q = query.trim().toLowerCase()
    return products.filter((p) => {
      if (!active.match(p.garment_type.toLowerCase())) return false
      if (!q) return true
      const haystack = [p.name, p.description, ...p.colors, ...p.search_tags].join(' ').toLowerCase()
      return q.split(/\s+/).every((word) => haystack.includes(word))
    })
  }, [products, filter, query])

  return (
    <section className="page">
      <div className="page-head">
        <h1>Shop the collection</h1>
        <p className="lead">Every team, every college, every member of the Bulldog family.</p>
      </div>

      <div className="toolbar">
        <div className="chips" role="group" aria-label="Filter by type">
          {FILTERS.map((f) => (
            <button
              key={f.label}
              className={`chip ${filter === f.label ? 'active' : ''}`}
              onClick={() => setFilter(f.label)}
            >
              {f.label}
            </button>
          ))}
        </div>
        <input
          type="search"
          className="search"
          placeholder="Search: hockey, Saybrook, gray…"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
      </div>

      {loading && <p className="muted">Loading products…</p>}
      {error && <p className="error">Couldn't load products: {error}. Is the back end running on port 8000?</p>}
      {!loading && !error && (
        <>
          <p className="muted count">
            {shown.length} {shown.length === 1 ? 'style' : 'styles'}
          </p>
          <div className="grid">
            {shown.map((p) => (
              <ProductCard key={p.product_id} product={p} />
            ))}
          </div>
          {shown.length === 0 && <p className="muted">No matches. Try another search, or ask our shop assistant.</p>}
        </>
      )}
    </section>
  )
}
