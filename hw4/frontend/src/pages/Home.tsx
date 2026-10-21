import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { getProducts } from '../api'
import { askChat } from '../chat/askChat'
import Dan from '../components/Dan'
import ProductCard from '../components/ProductCard'
import ProductStrip from '../components/ProductStrip'
import Shield from '../components/Shield'
import { usePrefs } from '../prefs/context'
import { useProductsById } from '../prefs/useProducts'
import type { Product } from '../types'

// Text from output/site_copy.md (Sophia's approved draft).
const HIGHLIGHTS = [
  {
    title: 'Find your people.',
    body: 'Twelve residential colleges, dozens of varsity teams and every graduate and professional school. Wear the name of the place where you found your crew.',
    art: '/art/college.svg',
  },
  {
    title: 'Built for New Haven weather.',
    body: 'Hoodies, crewnecks, quarter-zips and fleece, layered for late-night problem sets and cold walks across Cross Campus.',
    art: '/art/elm.svg',
  },
  {
    title: 'For the ones cheering you on.',
    body: "Yale Mom, Yale Dad, Yale Grandpa and more. Because every Bulldog's success is a family achievement.",
    art: '/art/yale-bowl.svg',
  },
]

// Hero: Victorian engravings of campus landmarks in tiles of navy and white, like toile.
const TILES = [
  { art: '/art/harkness.svg', label: 'Harkness Tower', color: 'navy', tall: true },
  { art: '/art/sterling.svg', label: 'Sterling Memorial Library', color: 'ivory' },
  { art: '/art/beinecke.svg', label: 'Beinecke Library', color: 'toile' },
  { art: '/art/payne-whitney.svg', label: 'Payne Whitney Gym', color: 'navy', tall: true },
  { art: '/art/rotunda.svg', label: 'The Rotunda', color: 'toile' },
  { art: '/art/connecticut-hall.svg', label: 'Connecticut Hall', color: 'ivory' },
  { art: '/art/phelps-gate.svg', label: 'Phelps Gate', color: 'ivory' },
  { art: '/art/yale-bowl.svg', label: 'The Yale Bowl', color: 'navy' },
]

const COLLEGES = ['Benjamin Franklin', 'Berkeley', 'Branford', 'Davenport', 'Grace Hopper', 'Jonathan Edwards', 'Morse', 'Pierson', 'Saybrook', 'Timothy Dwight', 'Trumbull']

export default function Home() {
  const { recent, mySize } = usePrefs()
  const { products: recentProducts } = useProductsById(recent.slice(0, 6))
  const [picks, setPicks] = useState<Product[]>([])

  useEffect(() => {
    getProducts()
      .then((all) => setPicks(all.filter((p) => p.dan_note)))
      .catch(() => setPicks([]))
  }, [])

  return (
    <>
      <section className="hero-tiles">
        {TILES.slice(0, 4).map((t, i) => (
          <figure key={t.label} className={`tile ${t.color} ${t.tall ? 'tall' : ''} t${i}`}>
            <img src={t.art} alt="" />
            <figcaption>{t.label}</figcaption>
          </figure>
        ))}
        <div className="hero-center">
          <p className="eyebrow">Officially licensed Yale merchandise · 57 Broadway, New Haven</p>
          <h1>
            Wear the blue.
            <br />
            <span>Join the story.</span>
          </h1>
          <p className="hero-sub">
            From your first week on Old Campus to the day you walk at Commencement, Campus Customs makes the gear that says{' '}
            <em>you belong here</em>.
          </p>
          <div className="hero-actions">
            <Link to="/products" className="btn btn-big">
              Shop the collection →
            </Link>
            <button className="btn btn-outline btn-big" onClick={() => askChat('Help me find a gift for a Yale student.')}>
              💬 Ask Handsome Dan
            </button>
          </div>
        </div>
        {TILES.slice(4).map((t, i) => (
          <figure key={t.label} className={`tile ${t.color} t${i + 4}`}>
            <img src={t.art} alt="" />
            <figcaption>{t.label}</figcaption>
          </figure>
        ))}
      </section>

      <section className="page highlights">
        {HIGHLIGHTS.map((h) => (
          <article key={h.title} className="highlight">
            <img src={h.art} alt="" />
            <h2>{h.title}</h2>
            <p>{h.body}</p>
          </article>
        ))}
      </section>

      {picks.length > 0 && (
        <section className="page picks">
          <div className="picks-head">
            <Dan size={110} />
            <div>
              <p className="eyebrow">Hand-selected by the mascot himself</p>
              <h2>Handsome Dan's Picks</h2>
              <p className="handwritten picks-byline">
                "If you want to look as handsome as Dan, start here. I know a thing or two about handsome." 🐾
              </p>
            </div>
          </div>
          <div className="grid">
            {picks.slice(0, 8).map((p) => (
              <ProductCard key={p.product_id} product={p} mySize={mySize} />
            ))}
          </div>
        </section>
      )}

      <section className="page college-row">
        <h2>Rep your residential college</h2>
        <div className="college-shields">
          {COLLEGES.map((c) => (
            <Link key={c} to={`/products?affiliation=${encodeURIComponent(c)}`} className="college-shield">
              <Shield name={c} size={40} />
              <span>{c}</span>
            </Link>
          ))}
        </div>
      </section>

      {recentProducts.length > 0 && (
        <div className="page recent-home">
          <ProductStrip title="Pick up where you left off" products={recentProducts} />
        </div>
      )}

      <section className="band">
        <p>
          <em>Lux et Veritas, and a really good hoodie.</em> Come see us at <strong>57 Broadway</strong>, steps from campus.
        </p>
        <p className="muted">Questions about sizing or gifts? Handsome Dan is waiting in the chat, bottom right.</p>
      </section>
    </>
  )
}
