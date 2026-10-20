import { Link } from 'react-router-dom'

export default function NotFound() {
  return (
    <section className="page">
      <h1>Page not found</h1>
      <p>
        This page wandered off campus. <Link to="/products">Head back to the shop →</Link>
      </p>
    </section>
  )
}
