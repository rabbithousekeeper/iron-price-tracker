import { usePriceData } from '../../hooks/usePriceData'
import { Header } from '../layout/Header'
import { Footer } from '../layout/Footer'
import { PriceCardGrid } from '../cards/PriceCardGrid'
import { PriceChartPanel } from '../chart/PriceChartPanel'
import { PriceTable } from '../table/PriceTable'

export function DashboardPage() {
  const {
    snapshots,
    selectedProductId,
    setSelectedProductId,
    selectedSnapshot,
    sort,
    setSort,
    sortedSnapshots,
    lastUpdated,
  } = usePriceData()

  return (
    <div className="min-h-screen flex flex-col">
      <Header lastUpdated={lastUpdated} />

      <main className="flex-1 max-w-7xl mx-auto w-full px-4 sm:px-6 lg:px-8 py-8 space-y-8">
        {/* Price Cards */}
        <section aria-label="現在の価格">
          <PriceCardGrid
            snapshots={snapshots}
            selectedProductId={selectedProductId}
            onSelect={setSelectedProductId}
          />
        </section>

        {/* Chart Panel */}
        <section aria-label="価格チャート">
          <PriceChartPanel
            snapshots={snapshots}
            selectedSnapshot={selectedSnapshot}
            selectedProductId={selectedProductId}
            onSelectProduct={setSelectedProductId}
          />
        </section>

        {/* Data Table */}
        <section aria-label="価格データ一覧">
          <PriceTable
            sortedSnapshots={sortedSnapshots}
            sort={sort}
            onSort={setSort}
          />
        </section>
      </main>

      <Footer />
    </div>
  )
}
