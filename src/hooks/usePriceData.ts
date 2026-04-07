import { useMemo, useState } from 'react'
import type { PriceSnapshot, TableSort } from '../types'
import { PRODUCTS } from '../data/products'
import { generatePriceHistory } from '../data/mockData'

export function usePriceData() {
  const [selectedProductId, setSelectedProductId] = useState<string>(PRODUCTS[0].id)
  const [sort, setSort] = useState<TableSort>({ key: 'price', direction: 'desc' })

  const allRecords = useMemo(() => generatePriceHistory(), [])

  const snapshots: PriceSnapshot[] = useMemo(() => {
    return PRODUCTS.map((product) => {
      const history = allRecords.filter((r) => r.productId === product.id)
      // history is already sorted chronologically (oldest first)
      const current = history[history.length - 1]
      const previous = history[history.length - 2]

      const currentPrice = current.price
      const previousPrice = previous.price
      const changeAmount = currentPrice - previousPrice
      const changePercent = (changeAmount / previousPrice) * 100

      const prices = history.map((r) => r.price)
      const ytdMin = Math.min(...prices)
      const ytdMax = Math.max(...prices)

      const trend =
        Math.abs(changePercent) < 0.1
          ? 'flat'
          : changePercent > 0
          ? 'up'
          : 'down'

      return {
        product,
        currentPrice,
        previousPrice,
        changeAmount,
        changePercent,
        trend,
        history,
        ytdMin,
        ytdMax,
      }
    })
  }, [allRecords])

  const selectedSnapshot = useMemo(
    () => snapshots.find((s) => s.product.id === selectedProductId) ?? snapshots[0],
    [snapshots, selectedProductId],
  )

  const sortedSnapshots = useMemo(() => {
    const sorted = [...snapshots]
    sorted.sort((a, b) => {
      let aVal: number | string
      let bVal: number | string

      switch (sort.key) {
        case 'name':
          aVal = a.product.nameJa
          bVal = b.product.nameJa
          break
        case 'price':
          aVal = a.currentPrice
          bVal = b.currentPrice
          break
        case 'change':
          aVal = a.changeAmount
          bVal = b.changeAmount
          break
        case 'changePercent':
          aVal = a.changePercent
          bVal = b.changePercent
          break
      }

      if (typeof aVal === 'string' && typeof bVal === 'string') {
        return sort.direction === 'asc'
          ? aVal.localeCompare(bVal, 'ja')
          : bVal.localeCompare(aVal, 'ja')
      }
      const diff = (aVal as number) - (bVal as number)
      return sort.direction === 'asc' ? diff : -diff
    })
    return sorted
  }, [snapshots, sort])

  const lastUpdated = useMemo(() => new Date(2026, 3, 7), []) // April 7, 2026

  return {
    snapshots,
    selectedProductId,
    setSelectedProductId,
    selectedSnapshot,
    sort,
    setSort,
    sortedSnapshots,
    lastUpdated,
  }
}
