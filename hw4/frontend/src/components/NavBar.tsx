import { Link, NavLink, useNavigate } from 'react-router-dom'
import { useAuth } from '../auth/context'
import { useBag } from '../cart/context'
import { useDanJump } from '../dan/useDanJump'
import { usePrefs } from '../prefs/context'
import Dan from './Dan'

const MAIN_LINKS = [
  { to: '/', label: 'Home', end: true },
  { to: '/products', label: 'Shop' },
  { to: '/about', label: 'About Us' },
]

// Masthead (title + Handsome Dan as the logo) and the sticky navigation bar.
export default function NavBar() {
  const { user, loading, logout } = useAuth()
  const { favorites } = usePrefs()
  const { count } = useBag()
  const jumping = useDanJump()
  const navigate = useNavigate()

  async function handleLogout() {
    await logout()
    navigate('/')
  }

  return (
    <>
      <header className="masthead">
        <p className="masthead-strip">
          Officially licensed Yale merchandise <span aria-hidden="true">✦</span> 57 Broadway, New Haven{' '}
          <span aria-hidden="true">✦</span> Reserve online, pick up in store
        </p>
        <Link to="/" className="masthead-title">
          <span className="ornament" aria-hidden="true">
            ❦
          </span>
          <span>
            <span className="wordmark">Campus Customs</span>
            <span className="subtitle">Yale Bulldog Blue · Outfitters to the Bulldog Nation</span>
          </span>
          <span className="ornament flip" aria-hidden="true">
            ❦
          </span>
        </Link>
        <Link to="/" className={`masthead-dan ${jumping ? 'jumping' : ''}`} aria-label="Home">
          <Dan size={96} />
          <span className="dan-caption">Look as handsome as Dan.</span>
          {jumping && (
            <span className="woof" aria-hidden="true">
              Woof!
            </span>
          )}
        </Link>
      </header>

      <nav className="navbar" aria-label="Main">
        <div className="nav-links">
          {MAIN_LINKS.map((l) => (
            <NavLink key={l.to} to={l.to} end={l.end}>
              {l.label}
            </NavLink>
          ))}
        </div>
        <div className="nav-account">
          <NavLink to="/saved" className="nav-icon" aria-label={`Saved items (${favorites.length})`}>
            <span aria-hidden="true">♥</span> Saved
            {favorites.length > 0 && <span className="badge">{favorites.length}</span>}
          </NavLink>
          <NavLink to="/bag" className={`nav-icon ${jumping ? 'bump' : ''}`} aria-label={`Bag (${count} items)`}>
            <span aria-hidden="true">👜</span> Bag
            {count > 0 && <span className="badge">{count}</span>}
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
              <NavLink to="/create-account" className="btn btn-small btn-nav">
                Create account
              </NavLink>
            </>
          )}
        </div>
      </nav>
      <div className="awning" aria-hidden="true" />
    </>
  )
}
