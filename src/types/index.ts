export type ProductCategory =
  | 'scrap'
  | 'flat'
  | 'long'
  | 'pipe'
  | 'stainless'
  | 'petrochemical'
  | 'nonferrous'
  | 'special_steel'

export interface Product {
  id: string
  nameJa: string
  nameEn: string
  category: ProductCategory
  unit: string
  basePrice: number
  volatility: number
  color: string
  description: string
}

export interface PriceRecord {
  productId: string
  date: string        // 'YYYY-MM-DD' 形式
  dateLabel: string   // 表示用ラベル
  price: number
  averagePrice?: number  // 集約時の期間平均価格
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

export type PeriodMode = 'year' | 'month' | 'day' | 'fiscal_year'

export type SortKey = 'name' | 'price' | 'change' | 'changePercent'
export type SortDirection = 'asc' | 'desc'

export interface TableSort {
  key: SortKey
  direction: SortDirection
}

// データソース情報
export interface DataSource {
  name: string
  url: string
  description: string
}
