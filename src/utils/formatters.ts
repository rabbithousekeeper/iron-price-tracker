export function formatPrice(price: number): string {
  return price.toLocaleString('ja-JP')
}

export function formatPriceJPY(price: number): string {
  return `¥${price.toLocaleString('ja-JP')}`
}

export function formatChange(amount: number): string {
  const sign = amount > 0 ? '+' : ''
  return `${sign}${amount.toLocaleString('ja-JP')}`
}

export function formatChangePercent(percent: number): string {
  const sign = percent > 0 ? '+' : ''
  return `${sign}${percent.toFixed(1)}%`
}

export function formatDate(date: Date): string {
  return date.toLocaleDateString('ja-JP', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  })
}

export function formatYAxisTick(value: number): string {
  if (value >= 10_000) {
    return `${(value / 10_000).toFixed(0)}万`
  }
  return `${(value / 1_000).toFixed(0)}千`
}
