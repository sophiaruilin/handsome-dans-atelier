import { Link, NavLink, useNavigate } from 'react-router-dom'
import { useAuth } from '../auth/context'
import { usePrefs } from '../prefs/context'

const MAIN_LINKS = [
  { to: '/', label: 'Home', end: true },
  { to: '/products', label: 'Products' },
  { to: '/about', label: 'About Us' },
]

export default function NavBar() {
  const { user, loading, logout } = useAuth()
  const { favorites } = usePrefs()
  const navigate = useNavigate()

  async function handleLogout() {
    await logout()
    navigate('/')
  }

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
        <NavLink to="/saved" className="nav-saved" aria-label={`Saved items (${favorites.length})`}>
          <span aria-hidden="true">♥</span> Saved
          {favorites.length > 0 && <span className="badge">{favorites.length}</span>}
        </NavLink>
        {loading ? null : user ? (
          <>
            <span className="greeting">Hi, {user.first_name}!</span>
            <button className="btn btn-small btn-nav" onClick={handleLogout}>
              Log out
            </button>
          </>
        ) : (
          <>
            <NavLink to="/login">Log in</NavLink>
            <NavLink to="/create-account" className="btn btn-small">
              Create account
            </NavLink>
          </>
        )}
      </nav>
    </header>
  )
}
