import type { ChatMessage, Product } from './types'

// Relative URLs: Vite proxies /api and /media to the FastAPI back end (see vite.config.ts).
async function request<T>(url: string, init?: RequestInit): Promise<T> {
  const res = await fetch(url, init)
  if (!res.ok) {
    const body = await res.json().catch(() => null)
    const detail = typeof body?.detail === 'string' ? body.detail : `Request failed (${res.status})`
    throw new Error(detail)
  }
  return res.json() as Promise<T>
}

const postJson = (body: unknown): RequestInit => ({
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(body),
})

export const getProducts = () => request<Product[]>('/api/products')

export const getProduct = (id: string) => request<Product>(`/api/products/${encodeURIComponent(id)}`)

export const joinWaitlist = (productId: string, email: string, size?: string) =>
  request<{ ok: boolean; message: string }>(
    '/api/waitlist',
    postJson({ product_id: productId, email, size: size ?? null }),
  )

// Stub today: the back end returns a canned reply. Problem 5 swaps in the shop agent behind the same route.
export const sendChat = (message: string, history: ChatMessage[], productId?: string) =>
  request<{ reply: string; products: Product[] }>(
    '/api/chat',
    postJson({ message, history, product_id: productId ?? null }),
  )

export const formatPrice = (price: number) => `$${price.toFixed(2)}`
