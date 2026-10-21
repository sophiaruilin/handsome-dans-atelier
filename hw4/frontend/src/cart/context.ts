import { createContext, useContext } from 'react'

export interface BagItem {
  product_id: string
  size: string
  quantity: number
  // For display only; the server re-reads prices from the catalogue when the order is placed.
  name: string
  price: number
  image_url: string
  max: number // stock in this size when added
}

export interface Bag {
  items: BagItem[]
  count: number
  subtotal: number
  add: (item: BagItem) => void
  setQuantity: (productId: string, size: string, quantity: number) => void
  remove: (productId: string, size: string) => void
  clear: () => void
}

export const BagContext = createContext<Bag | null>(null)

export function useBag(): Bag {
  const ctx = useContext(BagContext)
  if (!ctx) throw new Error('useBag must be used inside <BagProvider>')
  return ctx
}
