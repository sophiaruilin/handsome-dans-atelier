import type { ChatMessage, Product, User } from './types'

// Relative URLs: Vite proxies /api and /media to the FastAPI back end (see vite.config.ts).
async function request<T>(url: string, init?: RequestInit): Promise<T> {
  const res = await fetch(url, init)
  if (!res.ok) {
    const body = await res.json().catch(() => null)
    // FastAPI sends a string for our own errors and a list for validation errors (e.g. a malformed email).
    const detail =
      typeof body?.detail === 'string'
        ? body.detail
        : Array.isArray(body?.detail) && body.detail[0]?.msg
          ? String(body.detail[0].msg).replace(/^value is not a valid email address: /, '')
          : `Request failed (${res.status})`
    throw new Error(detail)
  }
  if (res.status === 204) return undefined as T
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

// The back end runs the PydanticAI shop agent and, for logged-in shoppers, saves the chat.
export const sendChat = (message: string, history: ChatMessage[], productId?: string) =>
  request<{ reply: string; products: Product[]; tools_used: string[] }>(
    '/api/chat',
    postJson({
      message,
      history: history.map(({ role, content }) => ({ role, content })),
      product_id: productId ?? null,
    }),
  )

export const getChatHistory = () => request<ChatMessage[]>('/api/chat/history')

// Accounts. The session lives in an HttpOnly cookie that the browser sends automatically.
export const getMe = () => request<User | null>('/api/auth/me')

export const login = (email: string, password: string) => request<User>('/api/auth/login', postJson({ email, password }))

export interface SignupForm {
  first_name: string
  last_name: string
  email: string
  password: string
  confirm_password: string
}

export const signup = (form: SignupForm) => request<User>('/api/auth/signup', postJson(form))

export const logout = () => request<void>('/api/auth/logout', { method: 'POST' })

export const formatPrice = (price: number) => `$${price.toFixed(2)}`
