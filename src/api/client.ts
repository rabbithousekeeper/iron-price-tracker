/**
 * バックエンドAPI クライアント
 *
 * 環境変数 VITE_API_BASE_URL が設定されている場合は実APIにアクセスし、
 * 未設定の場合はモックデータを使用する
 */

import type { PriceRecord } from '../types'

// 環境変数でAPI URLを制御
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL as string | undefined

/**
 * 実データAPIが有効かどうかを判定
 */
export function isApiEnabled(): boolean {
  return !!API_BASE_URL
}

/**
 * APIから価格データを取得
 */
export async function fetchPrices(params: {
  productId?: string
  startDate?: string
  endDate?: string
  source?: string
  limit?: number
}): Promise<PriceRecord[]> {
  if (!API_BASE_URL) {
    throw new Error('API_BASE_URL is not configured')
  }

  const url = new URL(`${API_BASE_URL}/api/prices/`)
  if (params.productId) url.searchParams.set('product_id', params.productId)
  if (params.startDate) url.searchParams.set('start_date', params.startDate)
  if (params.endDate) url.searchParams.set('end_date', params.endDate)
  if (params.source) url.searchParams.set('source', params.source)
  if (params.limit) url.searchParams.set('limit', String(params.limit))

  const resp = await fetch(url.toString())
  if (!resp.ok) {
    throw new Error(`API error: ${resp.status} ${resp.statusText}`)
  }

  const data = await resp.json()
  return data.records as PriceRecord[]
}

/**
 * 各商品の最新価格を取得
 */
export async function fetchLatestPrices(): Promise<PriceRecord[]> {
  if (!API_BASE_URL) {
    throw new Error('API_BASE_URL is not configured')
  }

  const resp = await fetch(`${API_BASE_URL}/api/prices/latest`)
  if (!resp.ok) {
    throw new Error(`API error: ${resp.status} ${resp.statusText}`)
  }

  const data = await resp.json()
  return data.records as PriceRecord[]
}

/**
 * データソースの状態を取得
 */
export async function fetchSourceStatus(): Promise<
  Array<{
    source: string
    status: string
    lastFetched: string | null
    recordsCount: number
  }>
> {
  if (!API_BASE_URL) {
    throw new Error('API_BASE_URL is not configured')
  }

  const resp = await fetch(`${API_BASE_URL}/api/prices/sources`)
  if (!resp.ok) {
    throw new Error(`API error: ${resp.status} ${resp.statusText}`)
  }

  const data = await resp.json()
  return data.sources
}
