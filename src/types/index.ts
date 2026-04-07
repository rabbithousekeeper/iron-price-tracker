export interface Product {
  id: string
  nameJa: string
  nameEn: string
  category: 'scrap' | 'flat' | 'long' | 'pipe' | 'stainless'
  unit: string
  basePrice: number
  volatility: number
  color: string
  description: string
}

export interface PriceRecord {
  productId: string
  month: string
  monthLabel: string
  price: number
}

export interface PriceSnapshot {
  product: Product
  currentPrice: number
  previousPrice: number
  changeAmount: number
  changePercent: number
  trend: 'up' | 'down' | 'flat'
  history: PriceRecord[]
  ytdMin: number
  ytdMax: number
}

export type SortKey = 'name' | 'price' | 'change' | 'changePercent'
export type SortDirection = 'asc' | 'desc'

export interface TableSort {
  key: SortKey
  direction: SortDirection
}
