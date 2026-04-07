import type { PriceRecord } from '../types'
import { PRODUCTS } from './products'

// Linear Congruential Generator for deterministic "random" numbers
function createLCG(seed: number) {
  let s = seed
  return () => {
    s = (1664525 * s + 1013904223) & 0xffffffff
    // Convert to unsigned and scale to [-1, 1]
    return ((s >>> 0) / 0xffffffff) * 2 - 1
  }
}

// Create a numeric seed from a string
function stringToSeed(str: string): number {
  let hash = 0
  for (let i = 0; i < str.length; i++) {
    hash = (hash * 31 + str.charCodeAt(i)) & 0xffffffff
  }
  return hash >>> 0
}

function formatMonthLabel(year: number, month: number): string {
  return `${year}年${month}月`
}

function formatMonthKey(year: number, month: number): string {
  return `${year}-${String(month).padStart(2, '0')}`
}

export function generatePriceHistory(): PriceRecord[] {
  const records: PriceRecord[] = []

  // Generate 13 months: 12 months ago → current month (April 2026)
  const currentYear = 2026
  const currentMonth = 4 // April

  const months: Array<{ year: number; month: number }> = []
  for (let i = 12; i >= 0; i--) {
    let month = currentMonth - i
    let year = currentYear
    while (month <= 0) {
      month += 12
      year -= 1
    }
    months.push({ year, month })
  }

  for (const product of PRODUCTS) {
    const lcg = createLCG(stringToSeed(product.id))
    let price = product.basePrice

    for (const { year, month } of months) {
      // Random walk: multiply by (1 + volatility * noise)
      const noise = lcg()
      // Scale noise to ~normal distribution approximation using 3 samples
      const noise2 = lcg()
      const noise3 = lcg()
      const normalApprox = (noise + noise2 + noise3) / 3

      price = price * (1 + product.volatility * normalApprox)

      // Clamp to ±30% of basePrice
      const minPrice = product.basePrice * 0.7
      const maxPrice = product.basePrice * 1.3
      price = Math.max(minPrice, Math.min(maxPrice, price))

      // Round to nearest 100 JPY
      price = Math.round(price / 100) * 100

      records.push({
        productId: product.id,
        month: formatMonthKey(year, month),
        monthLabel: formatMonthLabel(year, month),
        price,
      })
    }
  }

  return records
}
