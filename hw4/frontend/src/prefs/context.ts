import { createContext, useContext } from 'react'

export const SIZES = ['XS', 'S', 'M', 'L', 'XL', 'XXL'] as const

export interface ShopperPrefs {
  mySize: string | null
  setMySize: (size: string | null) => void
  favorites: string[] // product ids, most recent first
  isFavorite: (productId: string) => boolean
  toggleFavorite: (productId: string) => void
  recent: string[] // recently viewed product ids, most recent first
  addRecent: (productId: string) => void
}

export const ShopperPrefsContext = createContext<ShopperPrefs | null>(null)

export function usePrefs(): ShopperPrefs {
  const ctx = useContext(ShopperPrefsContext)
  if (!ctx) throw new Error('usePrefs must be used inside <ShopperPrefsProvider>')
  return ctx
}
