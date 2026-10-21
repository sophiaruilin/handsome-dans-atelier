import { useCallback, useEffect, useState, type ReactNode } from 'react'
import { ShopperPrefsContext } from './context'

const KEY = 'campus-customs-prefs'
const MAX_RECENT = 8

interface Stored {
  mySize: string | null
  favorites: string[]
  recent: string[]
}

function load(): Stored {
  try {
    const s = JSON.parse(localStorage.getItem(KEY) ?? '{}')
    return {
      mySize: typeof s.mySize === 'string' ? s.mySize : null,
      favorites: Array.isArray(s.favorites) ? s.favorites : [],
      recent: Array.isArray(s.recent) ? s.recent : [],
    }
  } catch {
    return { mySize: null, favorites: [], recent: [] }
  }
}

// My size, saved items and recently viewed, kept in this browser (works for guests too).
export default function ShopperPrefsProvider({ children }: { children: ReactNode }) {
  const [prefs, setPrefs] = useState<Stored>(load)

  useEffect(() => {
    localStorage.setItem(KEY, JSON.stringify(prefs))
  }, [prefs])

  const addRecent = useCallback(
    (id: string) =>
      setPrefs((p) => (p.recent[0] === id ? p : { ...p, recent: [id, ...p.recent.filter((r) => r !== id)].slice(0, MAX_RECENT) })),
    [],
  )

  const value = {
    ...prefs,
    setMySize: (mySize: string | null) => setPrefs((p) => ({ ...p, mySize })),
    isFavorite: (id: string) => prefs.favorites.includes(id),
    toggleFavorite: (id: string) =>
      setPrefs((p) => ({
        ...p,
        favorites: p.favorites.includes(id) ? p.favorites.filter((f) => f !== id) : [id, ...p.favorites],
      })),
    addRecent,
  }
  return <ShopperPrefsContext.Provider value={value}>{children}</ShopperPrefsContext.Provider>
}
