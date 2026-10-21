export type StockStatus = 'in_stock' | 'selling_fast' | 'sold_out'

export interface SizeStock {
  size: string
  quantity: number
  status: StockStatus
}

export interface Product {
  product_id: string
  name: string
  garment_type: string
  description: string
  colors: string[]
  search_tags: string[]
  image_url: string
  price: number
  total_stock: number
  stock_status: StockStatus
  inventory: SizeStock[]
}

export interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
  products?: Product[] // cards shown under an assistant reply
  pageResults?: PageResults // search this reply put on the page (website only, not sent back)
}

export interface User {
  id: number
  first_name: string
  last_name: string
  name: string
  email: string
}

export interface SearchFilters {
  query: string
  garment_type: string
  color: string
  max_price: number | null
  size: string
  in_stock_only: boolean
}

// Search matches the chat sends to the page (API contract: ChatResponse.page_results).
export interface PageResults {
  title: string
  shopper_message: string
  filters: SearchFilters
  total_matches: number
  products: Product[]
}
