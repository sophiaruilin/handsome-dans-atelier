import { useEffect, useState } from 'react'
import { getProducts } from '../api'
import type { Product } from '../types'

// Live products for a list of ids (saved items, recently viewed), in the same order.
export function useProductsById(ids: string[]): { products: Product[]; loading: boolean } {
  const [all, setAll] = useState<Product[] | null>(null)
  useEffect(() => {
    getProducts()
      .then(setAll)
      .catch(() => setAll([]))
  }, [])
  const byId = new Map((all ?? []).map((p) => [p.product_id, p]))
  return { products: ids.map((id) => byId.get(id)).filter((p): p is Product => !!p), loading: all === null }
}
