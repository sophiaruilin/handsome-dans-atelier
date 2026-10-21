import { useEffect, useMemo, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { getProducts } from '../api'
import { useChatResults } from '../chat/context'
import ChatResults from '../components/ChatResults'
import { colorFamily, COLOR_FAMILIES, swatchFor } from '../components/colorFamilies'
import ProductCard from '../components/ProductCard'
import Shield from '../components/Shield'
import { SIZES, usePrefs } from '../prefs/context'
import type { Product } from '../types'

// Group the catalogue's free-text garment types into a few shopper-friendly styles.
const STYLES: { label: string; match: (g: string) => boolean }[] = [
  { label: 'All styles', match: () => true },
  { label: 'Hoodies', match: (g) => g.includes('hood') },
  { label: 'Crewnecks', match: (g) => g.includes('crew') && !g.includes('t-shirt') && !g.includes('hood') },
  { label: 'T-shirts', match: (g) => g.includes('t-shirt') || (g.includes('shirt') && !g.includes('sweat')) },
  { label: 'Quarter-zips', match: (g) => g.includes('quarter-zip') },
  { label: 'Jackets & fleece', match: (g) => g.includes('jacket') || g.includes('fleece') },
]

const SORTS: { label: string; compare: (a: Product, b: Product) => number }[] = [
  { label: 'Featured', compare: (a, b) => Number(!!b.dan_note) - Number(!!a.dan_note) },
  { label: 'Price: low to high', compare: (a, b) => a.price - b.price || a.name.localeCompare(b.name) },
  { label: 'Price: high to low', compare: (a, b) => b.price - a.price || a.name.localeCompare(b.name) },
  {
    label: 'Selling fast first',
    compare: (a, b) => Number(b.stock_status === 'selling_fast') - Number(a.stock_status === 'selling_fast'),
  },
  { label: 'Name A–Z', compare: (a, b) => a.name.localeCompare(b.name) },
]

const GROUPS: { key: NonNullable<Product['affiliation_group']>; label: string; shields: boolean }[] = [
  { key: 'college', label: 'Residential Colleges', shields: true },
  { key: 'school', label: 'Graduate & Professional Schools', shields: true },
  { key: 'team', label: 'Varsity Teams', shields: false },
  { key: 'family', label: 'For the Family', shields: false },
]

const FITS = [
  { key: 'all', label: 'Everyone' },
  { key: 'womens', label: "Women's" },
  { key: 'mens', label: "Men's" },
] as const

type FitKey = (typeof FITS)[number]['key']

export default function Products() {
  const [products, setProducts] = useState<Product[]>([])
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)
  const [style, setStyle] = useState(STYLES[0].label)
  const [params] = useSearchParams()
  // Links like /products?affiliation=Saybrook (the college shields on Home) start pre-filtered.
  const [affiliation, setAffiliation] = useState<string | null>(params.get('affiliation'))
  const [fit, setFit] = useState<FitKey>('all')
  const [color, setColor] = useState<string | null>(null)
  const [picksOnly, setPicksOnly] = useState(false)
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

  // Affiliation names present in the catalogue, grouped, with counts (only offer filters that have products).
  const affiliations = useMemo(() => {
    const byGroup = new Map<string, Map<string, number>>()
    for (const p of products) {
      if (!p.affiliation_group || !p.affiliation) continue
      const g = byGroup.get(p.affiliation_group) ?? new Map<string, number>()
      g.set(p.affiliation, (g.get(p.affiliation) ?? 0) + 1)
      byGroup.set(p.affiliation_group, g)
    }
    return byGroup
  }, [products])

  const shown = useMemo(() => {
    const activeStyle = STYLES.find((s) => s.label === style) ?? STYLES[0]
    const q = query.trim().toLowerCase()
    const compare = (SORTS.find((s) => s.label === sort) ?? SORTS[0]).compare
    return products
      .filter((p) => {
        if (!activeStyle.match(p.garment_type.toLowerCase())) return false
        if (affiliation && p.affiliation !== affiliation) return false
        // Unisex styles count for everyone, so they appear under both women's and men's.
        if (fit !== 'all' && p.fit !== fit && p.fit !== 'unisex') return false
        if (color && colorFamily(p.colors) !== color) return false
        if (picksOnly && !p.dan_note) return false
        // "My size": only styles the shopper can actually buy right now.
        if (mySize && !p.inventory.some((s) => s.size === mySize && s.quantity > 0)) return false
        if (!q) return true
        const haystack = [p.name, p.description, p.affiliation ?? '', ...p.colors, ...p.search_tags].join(' ').toLowerCase()
        return q.split(/\s+/).every((word) => haystack.includes(word))
      })
      .sort(compare)
  }, [products, style, affiliation, fit, color, picksOnly, query, sort, mySize])

  const activeFilters = [
    style !== STYLES[0].label && { label: style, clear: () => setStyle(STYLES[0].label) },
    affiliation && { label: affiliation, clear: () => setAffiliation(null) },
    fit !== 'all' && { label: FITS.find((f) => f.key === fit)!.label, clear: () => setFit('all') },
    color && { label: color, clear: () => setColor(null) },
    picksOnly && { label: "Dan's Picks", clear: () => setPicksOnly(false) },
  ].filter(Boolean) as { label: string; clear: () => void }[]

  function clearAll() {
    setStyle(STYLES[0].label)
    setAffiliation(null)
    setFit('all')
    setColor(null)
    setPicksOnly(false)
    setQuery('')
  }

  return (
    <section className="page">
      <div className="page-head">
        <p className="eyebrow">The Campus Customs collection</p>
        <h1>Shop the collection</h1>
        <p className="lead">
          Every college, every school, every team, every member of the Bulldog family. Or just ask Handsome Dan (bottom
          right), and his picks appear right here.
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
        <div className="shop-layout">
          <aside className="filters" aria-label="Filters">
            <div className="filter-block">
              <h2>Style</h2>
              <div className="chips">
                {STYLES.map((s) => (
                  <button key={s.label} className={`chip ${style === s.label ? 'active' : ''}`} onClick={() => setStyle(s.label)}>
                    {s.label}
                  </button>
                ))}
              </div>
            </div>

            <div className="filter-block">
              <h2>Fit</h2>
              <div className="chips">
                {FITS.map((f) => (
                  <button key={f.key} className={`chip ${fit === f.key ? 'active' : ''}`} onClick={() => setFit(f.key)}>
                    {f.label}
                  </button>
                ))}
              </div>
              <p className="filter-note">Unisex styles appear under both.</p>
            </div>

            <div className="filter-block">
              <h2>Color</h2>
              <div className="color-filters">
                {COLOR_FAMILIES.map((c) => (
                  <button
                    key={c}
                    className={`color-chip ${color === c ? 'active' : ''}`}
                    onClick={() => setColor(color === c ? null : c)}
                    aria-pressed={color === c}
                  >
                    <span className="swatch" style={{ background: swatchFor(c) }} />
                    {c}
                  </button>
                ))}
              </div>
            </div>

            <div className="filter-block">
              <h2>Affiliation</h2>
              {GROUPS.map((g) => {
                const names = [...(affiliations.get(g.key) ?? new Map<string, number>()).entries()].sort((a, b) =>
                  a[0].localeCompare(b[0]),
                )
                if (!names.length) return null
                return (
                  <details key={g.key} open={g.key === 'college' || names.some(([n]) => n === affiliation)}>
                    <summary>{g.label}</summary>
                    <ul className="affiliations">
                      {names.map(([name, count]) => (
                        <li key={name}>
                          <button
                            className={`affiliation ${affiliation === name ? 'active' : ''}`}
                            onClick={() => setAffiliation(affiliation === name ? null : name)}
                            aria-pressed={affiliation === name}
                          >
                            {g.shields ? (
                              <Shield name={name} />
                            ) : (
                              <span className="affiliation-dot" aria-hidden="true">
                                ✦
                              </span>
                            )}
                            <span>{name.replace(' (Forest School)', '')}</span>
                            <small>{count}</small>
                          </button>
                        </li>
                      ))}
                    </ul>
                  </details>
                )
              })}
            </div>

            <label className="picks-toggle">
              <input type="checkbox" checked={picksOnly} onChange={(e) => setPicksOnly(e.target.checked)} />
              <span>🐾 Handsome Dan's Picks only</span>
            </label>
          </aside>

          <div className="shop-main">
            <div className="toolbar">
              <input
                type="search"
                className="search"
                placeholder="Search: hockey, Saybrook, Mom, gray…"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
              />
              <select className="sort" value={sort} onChange={(e) => setSort(e.target.value)} aria-label="Sort products">
                {SORTS.map((s) => (
                  <option key={s.label}>{s.label}</option>
                ))}
              </select>
            </div>

            {activeFilters.length > 0 && (
              <div className="active-filters">
                {activeFilters.map((f) => (
                  <button key={f.label} className="active-filter" onClick={f.clear}>
                    {f.label} ×
                  </button>
                ))}
                <button className="link-button" onClick={clearAll}>
                  Clear all
                </button>
              </div>
            )}

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
                {shown.length === 0 && (
                  <p className="muted">No matches. Try removing a filter, or ask Handsome Dan for ideas.</p>
                )}
              </>
            )}
          </div>
        </div>
      )}
    </section>
  )
}
