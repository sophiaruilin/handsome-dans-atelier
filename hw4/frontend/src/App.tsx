import { Route, Routes } from 'react-router-dom'
import { useAuth } from './auth/context'
import ChatWidget from './components/ChatWidget'
import NavBar from './components/NavBar'
import About from './pages/About'
import CreateAccount from './pages/CreateAccount'
import Home from './pages/Home'
import Login from './pages/Login'
import NotFound from './pages/NotFound'
import ProductDetail from './pages/ProductDetail'
import Products from './pages/Products'

export default function App() {
  const { user, loading } = useAuth()
  return (
    <>
      <NavBar />
      <main>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/products" element={<Products />} />
          <Route path="/products/:productId" element={<ProductDetail />} />
          <Route path="/about" element={<About />} />
          <Route path="/login" element={<Login />} />
          <Route path="/create-account" element={<CreateAccount />} />
          <Route path="*" element={<NotFound />} />
        </Routes>
      </main>
      <footer className="footer">
        <p>
          <strong>Yale Bulldog Blue by Campus Customs</strong> · 57 Broadway, New Haven, CT 06511
        </p>
        <p className="muted">Officially licensed Yale merchandise.</p>
      </footer>
      {/* Remount on login/logout so the chat matches who is signed in. */}
      {!loading && <ChatWidget key={user?.id ?? 'guest'} />}
    </>
  )
}
