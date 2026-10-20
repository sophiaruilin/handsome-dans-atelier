import { Link, NavLink } from 'react-router-dom'

const MAIN_LINKS = [
  { to: '/', label: 'Home', end: true },
  { to: '/products', label: 'Products' },
  { to: '/about', label: 'About Us' },
]

export default function NavBar() {
  return (
    <header className="navbar">
      <Link to="/" className="brand">
        <span className="brand-mark">Y</span>
        <span>
          Campus Customs
          <small>Yale Bulldog Blue</small>
        </span>
      </Link>
      <nav className="nav-links">
        {MAIN_LINKS.map((l) => (
          <NavLink key={l.to} to={l.to} end={l.end}>
            {l.label}
          </NavLink>
        ))}
      </nav>
      <nav className="nav-account">
        <NavLink to="/login">Log in</NavLink>
        <NavLink to="/create-account" className="btn btn-small">
          Create account
        </NavLink>
      </nav>
    </header>
  )
}
