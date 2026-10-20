import { Link } from 'react-router-dom'

// Text from output/site_copy.md (Sophia's approved draft).
const HIGHLIGHTS = [
  {
    title: 'Find your people.',
    body: 'Twelve residential colleges, dozens of varsity teams and every graduate and professional school. Wear the name of the place where you found your crew.',
  },
  {
    title: 'Built for New Haven weather.',
    body: 'Hoodies, crewnecks, quarter-zips and fleece, layered for late-night problem sets and cold walks across Cross Campus.',
  },
  {
    title: 'For the ones cheering you on.',
    body: "Yale Mom, Yale Dad, Yale Grandpa and more. Because every Bulldog's success is a family achievement.",
  },
]

export default function Home() {
  return (
    <>
      <section className="hero">
        <div className="hero-inner">
          <p className="eyebrow light">Officially licensed Yale merchandise · 57 Broadway, New Haven</p>
          <h1>Wear the blue. Join the story.</h1>
          <p className="hero-sub">
            From your first week on Old Campus to the day you walk at Commencement, Campus Customs makes the gear that
            says <em>you belong here</em>.
          </p>
          <div className="hero-actions">
            <Link to="/products" className="btn btn-light">
              Shop the collection →
            </Link>
            <Link to="/about" className="btn btn-ghost">
              Our story
            </Link>
          </div>
        </div>
      </section>

      <section className="page highlights">
        {HIGHLIGHTS.map((h) => (
          <article key={h.title} className="highlight">
            <h2>{h.title}</h2>
            <p>{h.body}</p>
          </article>
        ))}
      </section>

      <section className="band">
        <p>
          <em>Lux et Veritas, and a really good hoodie.</em> Come see us at <strong>57 Broadway</strong>, steps from
          campus.
        </p>
        <p className="muted">Questions about sizing or gifts? Ask our shop assistant, bottom right.</p>
      </section>
    </>
  )
}
