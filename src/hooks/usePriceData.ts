import { useMemo, useState, useCallback, useEffect } from 'react'
import type { PriceSnapshot, PriceRecord, TableSort, PeriodMode } from '../types'
import { PRODUCTS } from '../data/products'
import { generatePriceHistory } from '../data/mockData'
import { isApiEnabled, fetchPrices } from '../api/client'

// 年度キーを計算（決算月に基づく）
function getFiscalYearKey(dateStr: string, fiscalMonth: number): string {
  const year = parseInt(dateStr.slice(0, 4))
  const month = parseInt(dateStr.slice(5, 7))
  // 決算月の翌月が年度の開始月
  // 例：決算月3月 → 4月始まり、決算月12月 → 1月始まり
  const fiscalStartMonth = (fiscalMonth % 12) + 1
  const fiscalYear = month >= fiscalStartMonth ? year : year - 1
  return `${fiscalYear}年度`
}

// 期間モードに応じてレコードを集約
function aggregateRecords(
  records: PriceRecord[],
  periodMode: PeriodMode,
  fiscalMonth: number = 3,
): PriceRecord[] {
  if (periodMode === 'day') return records

  // 品目ごとにグループ化してから期間で集約（複数品目が混在しても正しく処理）
  const byProduct = new Map<string, PriceRecord[]>()
  for (const record of records) {
    if (!byProduct.has(record.productId)) byProduct.set(record.productId, [])
    byProduct.get(record.productId)!.push(record)
  }

  const aggregated: PriceRecord[] = []
  for (const [, productRecords] of byProduct) {
    const groups = new Map<string, PriceRecord[]>()
    for (const record of productRecords) {
      let key: string
      if (periodMode === 'month') {
        key = record.date.slice(0, 7) // 'YYYY-MM'
      } else if (periodMode === 'fiscal_year') {
        key = getFiscalYearKey(record.date, fiscalMonth)
      } else {
        key = record.date.slice(0, 4) // 'YYYY'
      }
      if (!groups.has(key)) groups.set(key, [])
      groups.get(key)!.push(record)
    }

    for (const [key, recs] of groups) {
      const last = recs[recs.length - 1]
      // 平均価格を計算
      const avgPrice = Math.round(recs.reduce((sum, r) => sum + r.price, 0) / recs.length)
      let dateLabel: string
      if (periodMode === 'month') {
        const [y, m] = key.split('-')
        dateLabel = `${y}年${parseInt(m)}月`
      } else if (periodMode === 'fiscal_year') {
        dateLabel = key
      } else {
        dateLabel = `${key}年`
      }
      aggregated.push({
        ...last,
        dateLabel,
        price: last.price,
        averagePrice: avgPrice,
      })
    }
  }
  return aggregated
}

export function usePriceData() {
  const [selectedProductIds, setSelectedProductIds] = useState<string[]>([PRODUCTS[0].id])
  const [sort, setSort] = useState<TableSort>({ key: 'price', direction: 'desc' })
  const [periodMode, setPeriodMode] = useState<PeriodMode>('month')
  const [fiscalMonth, setFiscalMonth] = useState<number>(3) // 決算月（デフォルト: 3月）
  const [startDate, setStartDate] = useState<string>('2025-04-01')
  const [endDate, setEndDate] = useState<string>('2026-04-07')

  // API利用時のデータ格納用state
  const [apiRecords, setApiRecords] = useState<PriceRecord[] | null>(null)
  const [apiLoading, setApiLoading] = useState(false)
  const [apiError, setApiError] = useState<string | null>(null)

  const useApi = isApiEnabled()

  // モックデータ（API未使用時のフォールバック）
  const mockRecords = useMemo(() => (useApi ? [] : generatePriceHistory()), [useApi])

  // API有効時: バックエンドからデータ取得
  useEffect(() => {
    if (!useApi) return

    let cancelled = false
    setApiLoading(true)
    setApiError(null)

    fetchPrices({
      startDate,
      endDate,
      limit: 10000,
    })
      .then((records) => {
        if (!cancelled) {
          setApiRecords(records)
          setApiLoading(false)
        }
      })
      .catch((err) => {
        if (!cancelled) {
          console.error('API取得エラー:', err)
          setApiError(err.message)
          setApiLoading(false)
        }
      })

    return () => {
      cancelled = true
    }
  }, [useApi, startDate, endDate])

  // データソース: APIデータまたはモックデータ
  const allRecords = useApi ? (apiRecords ?? []) : mockRecords

  // 日付範囲でフィルタリング
  const filteredRecords = useMemo(() => {
    return allRecords.filter((r) => r.date >= startDate && r.date <= endDate)
  }, [allRecords, startDate, endDate])

  // スナップショット（全品目のサマリ）
  const snapshots: PriceSnapshot[] = useMemo(() => {
    return PRODUCTS.map((product) => {
      const history = filteredRecords.filter((r) => r.productId === product.id)
      if (history.length < 2) {
        // データ不足の場合のフォールバック
        const price = history.length > 0 ? history[0].price : product.basePrice
        return {
          product,
          currentPrice: price,
          previousPrice: price,
          changeAmount: 0,
          changePercent: 0,
          trend: 'flat' as const,
          history,
          ytdMin: price,
          ytdMax: price,
        }
      }

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
  }, [filteredRecords])

  // チャート表示用：期間モードに応じて集約したデータ
  const chartRecords = useMemo(() => {
    const selected = filteredRecords.filter((r) =>
      selectedProductIds.includes(r.productId)
    )
    return aggregateRecords(selected, periodMode, fiscalMonth)
  }, [filteredRecords, selectedProductIds, periodMode, fiscalMonth])

  // 選択中のスナップショット
  const selectedSnapshots = useMemo(
    () => snapshots.filter((s) => selectedProductIds.includes(s.product.id)),
    [snapshots, selectedProductIds],
  )

  // 品目の選択トグル（複数選択対応）
  const toggleProductId = useCallback((id: string) => {
    setSelectedProductIds((prev) => {
      if (prev.includes(id)) {
        // 最低1つは選択状態にする
        if (prev.length <= 1) return prev
        return prev.filter((pid) => pid !== id)
      }
      return [...prev, id]
    })
  }, [])

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

  const lastUpdated = useMemo(() => new Date(2026, 3, 7), []) // 2026年4月7日

  // CSVダウンロード
  const downloadCsv = useCallback(() => {
    const today = new Date(2026, 3, 7)
    const dateStr = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}-${String(today.getDate()).padStart(2, '0')}`
    const modeLabel = periodMode === 'day' ? '日別' : periodMode === 'month' ? '月別' : periodMode === 'fiscal_year' ? '年度別' : '年別'
    const filename = `prices-${modeLabel}-${dateStr}.csv`

    // ヘッダー行（日別以外は平均価格列を追加）
    const isAggregated = periodMode !== 'day'
    const headers = isAggregated
      ? ['品目', '品目（英語）', 'カテゴリ', '期間', '価格（期末）', '平均価格', '単位']
      : ['品目', '品目（英語）', 'カテゴリ', '日付', '価格', '単位']
    const rows: string[][] = [headers]

    // 選択中の品目のデータを出力
    const productIds = selectedProductIds.length > 0 ? selectedProductIds : PRODUCTS.map((p) => p.id)
    for (const pid of productIds) {
      const product = PRODUCTS.find((p) => p.id === pid)
      if (!product) continue

      const records = filteredRecords.filter((r) => r.productId === pid)
      const aggregated = aggregateRecords(records, periodMode, fiscalMonth)

      for (const record of aggregated) {
        if (isAggregated) {
          rows.push([
            product.nameJa,
            product.nameEn,
            product.category,
            record.dateLabel,
            String(record.price),
            String(record.averagePrice ?? record.price),
            product.unit,
          ])
        } else {
          rows.push([
            product.nameJa,
            product.nameEn,
            product.category,
            record.date,
            String(record.price),
            product.unit,
          ])
        }
      }
    }

    const csvContent = rows.map((row) =>
      row.map((cell) => `"${cell.replace(/"/g, '""')}"`).join(',')
    ).join('\n')

    // BOM付きUTF-8でダウンロード
    const bom = '\uFEFF'
    const blob = new Blob([bom + csvContent], { type: 'text/csv;charset=utf-8;' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = filename
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(url)
  }, [selectedProductIds, filteredRecords, periodMode, fiscalMonth])

  return {
    snapshots,
    selectedProductIds,
    toggleProductId,
    selectedSnapshots,
    sort,
    setSort,
    sortedSnapshots,
    lastUpdated,
    periodMode,
    setPeriodMode,
    fiscalMonth,
    setFiscalMonth,
    startDate,
    setStartDate,
    endDate,
    setEndDate,
    chartRecords,
    downloadCsv,
    // API関連の状態
    isUsingApi: useApi,
    apiLoading,
    apiError,
  }
}
