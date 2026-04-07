import { usePriceData } from '../../hooks/usePriceData'
import { Header } from '../layout/Header'
import { Footer } from '../layout/Footer'
import { DataSourcePanel } from '../layout/DataSourcePanel'
import { PriceCardGrid } from '../cards/PriceCardGrid'
import { PriceChartPanel } from '../chart/PriceChartPanel'
import { PriceTable } from '../table/PriceTable'

export function DashboardPage() {
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
    startDate,
    setStartDate,
    endDate,
    setEndDate,
    chartRecords,
    downloadCsv,
  } = usePriceData()

  return (
    <div className="min-h-screen flex flex-col">
      <Header lastUpdated={lastUpdated} />

      <main className="flex-1 max-w-7xl mx-auto w-full px-4 sm:px-6 lg:px-8 py-8 space-y-8">
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

        {/* データソース */}
        <section aria-label="データ取得ソース">
          <DataSourcePanel />
        </section>
      </main>

      <Footer />
    </div>
  )
}
