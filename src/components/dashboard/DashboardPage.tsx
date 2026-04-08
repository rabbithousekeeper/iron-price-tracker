import { usePriceData } from '../../hooks/usePriceData'
import { Header } from '../layout/Header'
import { Footer } from '../layout/Footer'
import { DataSourcePanel } from '../layout/DataSourcePanel'
import { PriceCardGrid } from '../cards/PriceCardGrid'
import { PriceChartPanel } from '../chart/PriceChartPanel'
import { PriceTable } from '../table/PriceTable'

// ページ種別
type Page = 'dashboard' | 'legal'

interface DashboardPageProps {
  onNavigate?: (page: Page) => void
  onLogout?: () => void
}

// 日時フォーマット（日本時間 JST 表示）
function formatDateTime(iso: string | null): string {
  if (!iso) return '未取得'
  // バックエンドがTZ情報なし（"2026-04-07T13:15:39.230069"）で返すためUTCとして扱う
  const utcStr = iso.endsWith('Z') || iso.includes('+') ? iso : iso + 'Z'
  return new Date(utcStr).toLocaleString('ja-JP', {
    timeZone: 'Asia/Tokyo',
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
}

export function DashboardPage({ onNavigate, onLogout }: DashboardPageProps) {
  const {
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
    hasData,
    isUsingApi,
    apiLoading,
    apiError,
    refreshData,
    runManualFetch,
    manualFetching,
    manualFetchResult,
    apiLastFetched,
    scrapeLastFetched,
    runApiFetch,
  } = usePriceData()

  return (
    <div className="min-h-screen flex flex-col">
      <Header lastUpdated={lastUpdated} onNavigate={onNavigate} onLogout={onLogout} />

      <main className="flex-1 max-w-7xl mx-auto w-full px-4 sm:px-6 lg:px-8 py-8 space-y-8">
        {/* API状態バー */}
        {isUsingApi && (
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 bg-white rounded-lg border border-gray-200 px-4 py-3 shadow-sm">
            <div className="flex flex-col gap-1 text-sm">
              {apiLoading ? (
                <div className="flex items-center gap-2">
                  <svg className="animate-spin h-4 w-4 text-blue-500" viewBox="0 0 24 24" fill="none">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                  </svg>
                  <span className="text-gray-600">データを読み込み中...</span>
                </div>
              ) : apiError ? (
                <div className="flex items-center gap-2">
                  <span className="w-2 h-2 bg-red-500 rounded-full" />
                  <span className="text-red-600">API接続エラー: {apiError}</span>
                </div>
              ) : (
                <>
                  <div className="flex items-center gap-2">
                    <span className="w-2 h-2 bg-green-500 rounded-full" />
                    <span className="text-gray-600">📡 API最終取得: {formatDateTime(apiLastFetched)}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="w-2 h-2 bg-transparent rounded-full" />
                    <span className="text-gray-600">🔍 スクレイピング最終実行: {formatDateTime(scrapeLastFetched)}</span>
                  </div>
                </>
              )}
            </div>
            <div className="flex items-center gap-2">
              {/* 再読み込みボタン */}
              <button
                onClick={refreshData}
                disabled={apiLoading}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                🔄 再読み込み
              </button>
              {/* API更新ボタン */}
              <button
                onClick={runApiFetch}
                disabled={apiLoading}
                title="EIA・Yahoo Financeから最新データを取得"
                className="inline-flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                📡 API更新
              </button>
              {/* スクレイピング実行ボタン */}
              <button
                onClick={runManualFetch}
                disabled={manualFetching || apiLoading}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium text-white bg-brand-700 rounded-md hover:bg-brand-800 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {manualFetching ? (
                  <>
                    <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24" fill="none">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                    </svg>
                    スクレイピング中...
                  </>
                ) : (
                  '🔍 スクレイピング実行'
                )}
              </button>
            </div>
          </div>
        )}

        {/* 手動スクレイピング結果メッセージ */}
        {manualFetchResult && (
          <div
            className={`rounded-lg px-4 py-3 text-sm ${
              manualFetchResult.success
                ? 'bg-green-50 text-green-800 border border-green-200'
                : 'bg-red-50 text-red-800 border border-red-200'
            }`}
          >
            {manualFetchResult.message}
          </div>
        )}

        {/* データなし時のメッセージ */}
        {!apiLoading && !hasData && (
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 px-6 py-12 text-center">
            <p className="text-gray-500 text-lg">
              データがありません。「データを更新」ボタンでデータを取得してください。
            </p>
          </div>
        )}

        {/* データあり時のみ表示 */}
        {hasData && (
          <>
            {/* 価格カード */}
            <section aria-label="現在の価格">
              <PriceCardGrid
                snapshots={snapshots}
                selectedProductIds={selectedProductIds}
                onToggle={toggleProductId}
              />
            </section>

            {/* チャートパネル */}
            <section aria-label="価格チャート">
              <PriceChartPanel
                snapshots={snapshots}
                selectedSnapshots={selectedSnapshots}
                selectedProductIds={selectedProductIds}
                onToggleProduct={toggleProductId}
                periodMode={periodMode}
                onPeriodModeChange={setPeriodMode}
                fiscalMonth={fiscalMonth}
                onFiscalMonthChange={setFiscalMonth}
                startDate={startDate}
                endDate={endDate}
                onStartDateChange={setStartDate}
                onEndDateChange={setEndDate}
                chartRecords={chartRecords}
                onDownloadCsv={downloadCsv}
              />
            </section>

            {/* データテーブル */}
            <section aria-label="価格データ一覧">
              <PriceTable
                sortedSnapshots={sortedSnapshots}
                sort={sort}
                onSort={setSort}
              />
            </section>
          </>
        )}

        {/* データソース */}
        <section aria-label="データ取得ソース">
          <DataSourcePanel />
        </section>
      </main>

      <Footer onNavigate={onNavigate} />
    </div>
  )
}
