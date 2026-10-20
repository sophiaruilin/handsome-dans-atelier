import { useEffect, useState, type ReactNode } from 'react'
import * as api from '../api'
import type { User } from '../types'
import { AuthContext } from './context'

// Asks the back end who is logged in (from the session cookie) on page load.
export default function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api
      .getMe()
      .then(setUser)
      .catch(() => setUser(null))
      .finally(() => setLoading(false))
  }, [])

  const value = {
    user,
    loading,
    login: async (email: string, password: string) => {
      const u = await api.login(email, password)
      setUser(u)
      return u
    },
    signup: async (form: api.SignupForm) => {
      const u = await api.signup(form)
      setUser(u)
      return u
    },
    logout: async () => {
      await api.logout()
      setUser(null)
    },
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
