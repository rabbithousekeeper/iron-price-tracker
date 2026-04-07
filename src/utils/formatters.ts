export function formatPrice(price: number): string {
  return price.toLocaleString('ja-JP')
}

export function formatPriceJPY(price: number, unit?: string): string {
  if (unit && unit.includes('指数')) {
    return price.toLocaleString('ja-JP', { minimumFractionDigits: 1, maximumFractionDigits: 1 })
  }
  return `\u00a5${price.toLocaleString('ja-JP')}`
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
    const man = value / 10_000
    return man === Math.floor(man) ? `${man}万` : `${man.toFixed(1)}万`
  }
  if (value >= 1_000) {
    const sen = value / 1_000
    return sen === Math.floor(sen) ? `${sen}千` : `${sen.toFixed(1)}千`
  }
  return `${value}`
}
