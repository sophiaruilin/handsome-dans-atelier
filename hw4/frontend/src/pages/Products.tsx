import { useEffect, useMemo, useState } from 'react'
import { getProducts } from '../api'
import ChatResults from '../components/ChatResults'
import ProductCard from '../components/ProductCard'
import { useChatResults } from '../chat/context'
import { SIZES, usePrefs } from '../prefs/context'
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

const SORTS: { label: string; compare: (a: Product, b: Product) => number }[] = [
  { label: 'Featured', compare: () => 0 },
  { label: 'Price: low to high', compare: (a, b) => a.price - b.price || a.name.localeCompare(b.name) },
  { label: 'Price: high to low', compare: (a, b) => b.price - a.price || a.name.localeCompare(b.name) },
  {
    label: 'Selling fast first',
    compare: (a, b) => Number(b.stock_status === 'selling_fast') - Number(a.stock_status === 'selling_fast'),
  },
  { label: 'Name A–Z', compare: (a, b) => a.name.localeCompare(b.name) },
]

export default function Products() {
  const [products, setProducts] = useState<Product[]>([])
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState('All')
  const [query, setQuery] = useState('')
  const [sort, setSort] = useState(SORTS[0].label)
  const chat = useChatResults()
  const { mySize, setMySize } = usePrefs()

  useEffect(() => {
    getProducts()
      .then(setProducts)
      .catch((e: Error) => setError(e.message))
      .finally(() => setLoading(false))
  }, [])

  const shown = useMemo(() => {
    const active = FILTERS.find((f) => f.label === filter) ?? FILTERS[0]
    const q = query.trim().toLowerCase()
    const compare = (SORTS.find((s) => s.label === sort) ?? SORTS[0]).compare
    return products
      .filter((p) => {
        if (!active.match(p.garment_type.toLowerCase())) return false
        // "My size": only styles the shopper can actually buy right now.
        if (mySize && !p.inventory.some((s) => s.size === mySize && s.quantity > 0)) return false
        if (!q) return true
        const haystack = [p.name, p.description, ...p.colors, ...p.search_tags].join(' ').toLowerCase()
        return q.split(/\s+/).every((word) => haystack.includes(word))
      })
      .sort(compare)
  }, [products, filter, query, sort, mySize])

  return (
    <section className="page">
      <div className="page-head">
        <h1>Shop the collection</h1>
        <p className="lead">
          Every team, every college, every member of the Bulldog family. Tip: ask the shop assistant (bottom right) and
          its picks appear right here.
        </p>
      </div>

      <div className="size-bar" role="group" aria-label="My size">
        <span className="size-bar-label">
          <strong>My size</strong>
          <small>{mySize ? `Showing what's in stock in ${mySize}` : 'Pick yours to hide sold-out styles'}</small>
        </span>
        {SIZES.map((s) => (
          <button
            key={s}
            className={`size-pill ${mySize === s ? 'active' : ''}`}
            onClick={() => setMySize(mySize === s ? null : s)}
            aria-pressed={mySize === s}
          >
            {s}
          </button>
        ))}
        {mySize && (
          <button className="size-clear" onClick={() => setMySize(null)}>
            Clear
          </button>
        )}
      </div>

      {chat.results && (
        <ChatResults results={chat.results} version={chat.version} onClear={chat.clear} mySize={mySize} />
      )}

      {!chat.results && (
        <>
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
            <select className="sort" value={sort} onChange={(e) => setSort(e.target.value)} aria-label="Sort products">
              {SORTS.map((s) => (
                <option key={s.label}>{s.label}</option>
              ))}
            </select>
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
                {mySize && ` in stock in size ${mySize}`}
              </p>
              <div className="grid">
                {shown.map((p) => (
                  <ProductCard key={p.product_id} product={p} mySize={mySize} />
                ))}
              </div>
              {shown.length === 0 && <p className="muted">No matches. Try another search, or ask our shop assistant.</p>}
            </>
          )}
        </>
      )}
    </section>
  )
}
