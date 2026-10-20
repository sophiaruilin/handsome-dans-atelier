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
}
