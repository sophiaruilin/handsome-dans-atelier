import type { ChatMessage, PageContext, PageResults, Product, User } from './types'

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

// The back end runs the PydanticAI shop agent. For logged-in shoppers it saves the chat and uses
// the saved history as memory (the history sent here is only used for guests).
export const sendChat = (message: string, history: ChatMessage[], page: PageContext) =>
  request<{ reply: string; products: Product[]; page_results: PageResults | null; tools_used: string[] }>(
    '/api/chat',
    postJson({
      message,
      history: history.map(({ role, content, products }) => ({ role, content, products: products ?? [] })),
      page,
    }),
  )

export const getChatHistory = () => request<ChatMessage[]>('/api/chat/history')

export const clearChatHistory = () => request<void>('/api/chat/history', { method: 'DELETE' })

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
