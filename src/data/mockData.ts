import type { PriceRecord } from '../types'
import { PRODUCTS } from './products'

// 決定論的な乱数生成器 (Linear Congruential Generator)
function createLCG(seed: number) {
  let s = seed
  return () => {
    s = (1664525 * s + 1013904223) & 0xffffffff
    return ((s >>> 0) / 0xffffffff) * 2 - 1
  }
}

// 文字列からシード値を生成
function stringToSeed(str: string): number {
  let hash = 0
  for (let i = 0; i < str.length; i++) {
    hash = (hash * 31 + str.charCodeAt(i)) & 0xffffffff
  }
  return hash >>> 0
}

function formatDateLabel(year: number, month: number, day: number): string {
  return `${year}年${month}月${day}日`
}

function formatDateKey(year: number, month: number, day: number): string {
  return `${year}-${String(month).padStart(2, '0')}-${String(day).padStart(2, '0')}`
}

// 日別価格データを生成（過去2年分）
export function generatePriceHistory(): PriceRecord[] {
  const records: PriceRecord[] = []

  // 2024年4月1日 ～ 2026年4月7日 の日別データ
  const startDate = new Date(2024, 3, 1) // 2024-04-01
  const endDate = new Date(2026, 3, 7)   // 2026-04-07

  // 日付リストを生成
  const dates: Array<{ year: number; month: number; day: number }> = []
  const current = new Date(startDate)
  while (current <= endDate) {
    dates.push({
      year: current.getFullYear(),
      month: current.getMonth() + 1,
      day: current.getDate(),
    })
    current.setDate(current.getDate() + 1)
  }

  for (const product of PRODUCTS) {
    const lcg = createLCG(stringToSeed(product.id))
    let price = product.basePrice

    for (const { year, month, day } of dates) {
      // 日別のランダムウォーク（月次よりボラティリティを小さくする）
      const noise = lcg()
      const noise2 = lcg()
      const noise3 = lcg()
      const normalApprox = (noise + noise2 + noise3) / 3

      // 日次ボラティリティ = 月次ボラティリティ / sqrt(22営業日)
      const dailyVolatility = product.volatility / Math.sqrt(22)
      price = price * (1 + dailyVolatility * normalApprox)

      // ±30%にクランプ
      const minPrice = product.basePrice * 0.7
      const maxPrice = product.basePrice * 1.3
      price = Math.max(minPrice, Math.min(maxPrice, price))

      // 価格の丸め（単位に応じて）
      let roundedPrice: number
      if (product.basePrice >= 10_000) {
        roundedPrice = Math.round(price / 100) * 100
      } else if (product.basePrice >= 1_000) {
        roundedPrice = Math.round(price / 10) * 10
      } else {
        roundedPrice = Math.round(price)
      }

      records.push({
        productId: product.id,
        date: formatDateKey(year, month, day),
        dateLabel: formatDateLabel(year, month, day),
        price: roundedPrice,
      })
    }
  }

  return records
}
