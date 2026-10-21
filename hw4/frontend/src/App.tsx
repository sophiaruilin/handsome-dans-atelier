import { Route, Routes } from 'react-router-dom'
import { useAuth } from './auth/context'
import ChatWidget from './components/ChatWidget'
import DanCartwheel from './components/DanCartwheel'
import SeasonSwitcher from './components/SeasonSwitcher'
import Toast from './components/Toast'
import NavBar from './components/NavBar'
import About from './pages/About'
import CreateAccount from './pages/CreateAccount'
import Home from './pages/Home'
import Login from './pages/Login'
import NotFound from './pages/NotFound'
import ProductDetail from './pages/ProductDetail'
import Bag from './pages/Bag'
import Products from './pages/Products'
import Saved from './pages/Saved'

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
          <Route path="/saved" element={<Saved />} />
          <Route path="/bag" element={<Bag />} />
          <Route path="/login" element={<Login />} />
          <Route path="/create-account" element={<CreateAccount />} />
          <Route path="*" element={<NotFound />} />
        </Routes>
      </main>
      <footer className="footer">
        <img src="/art/harkness.svg" alt="" className="footer-tower" />
        <p className="footer-name">Yale Bulldog Blue by Campus Customs</p>
        <p>57 Broadway, New Haven, CT 06511 · Reserve online, pick up in store</p>
        <p className="muted">Officially licensed Yale merchandise · Lux et Veritas, and a really good hoodie.</p>
        <SeasonSwitcher />
      </footer>
      <Toast />
      <DanCartwheel />
      {/* Remount on login/logout so the chat matches who is signed in. */}
      {!loading && <ChatWidget key={user?.id ?? 'guest'} />}
    </>
  )
}
