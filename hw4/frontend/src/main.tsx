import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import AuthProvider from './auth/AuthProvider.tsx'
import ChatResultsProvider from './chat/ChatResultsProvider.tsx'
import ShopperPrefsProvider from './prefs/ShopperPrefsProvider.tsx'
import BagProvider from './cart/BagProvider.tsx'
import './index.css'
import './theme.css'
import App from './App.tsx'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <BrowserRouter>
      <AuthProvider>
        <ChatResultsProvider>
          <ShopperPrefsProvider>
            <BagProvider>
              <App />
            </BagProvider>
          </ShopperPrefsProvider>
        </ChatResultsProvider>
      </AuthProvider>
    </BrowserRouter>
  </StrictMode>,
)
