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
}

export interface User {
  id: number
  first_name: string
  last_name: string
  name: string
  email: string
}
