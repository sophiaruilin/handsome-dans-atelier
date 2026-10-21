import { useEffect, useState, type ReactNode } from 'react'
import { danDo } from '../dan/danBus'
import { BagContext, type BagItem } from './context'

const KEY = 'campus-customs-bag'

function load(): BagItem[] {
  try {
    const items = JSON.parse(localStorage.getItem(KEY) ?? '[]')
    return Array.isArray(items) ? items : []
  } catch {
    return []
  }
}

// The shopping bag, kept in this browser until the shopper reserves it for pickup.
export default function BagProvider({ children }: { children: ReactNode }) {
  const [items, setItems] = useState<BagItem[]>(load)

  useEffect(() => {
    localStorage.setItem(KEY, JSON.stringify(items))
  }, [items])

  const same = (a: { product_id: string; size: string }, id: string, size: string) => a.product_id === id && a.size === size

  const value = {
    items,
    count: items.reduce((n, i) => n + i.quantity, 0),
    subtotal: items.reduce((n, i) => n + i.quantity * i.price, 0),
    add: (item: BagItem) => {
      setItems((cur) => {
        const existing = cur.find((i) => same(i, item.product_id, item.size))
        if (!existing) return [...cur, item]
        return cur.map((i) =>
          same(i, item.product_id, item.size) ? { ...i, quantity: Math.min(i.quantity + item.quantity, item.max), max: item.max } : i,
        )
      })
      danDo('jump') // Handsome Dan is thrilled
    },
    setQuantity: (id: string, size: string, quantity: number) =>
      setItems((cur) => cur.map((i) => (same(i, id, size) ? { ...i, quantity: Math.max(1, Math.min(quantity, i.max)) } : i))),
    remove: (id: string, size: string) => setItems((cur) => cur.filter((i) => !same(i, id, size))),
    clear: () => setItems([]),
  }
  return <BagContext.Provider value={value}>{children}</BagContext.Provider>
}
