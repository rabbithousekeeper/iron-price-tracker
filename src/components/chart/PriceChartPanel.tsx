import type { PriceSnapshot, PriceRecord, PeriodMode } from '../../types'
import { formatPriceJPY } from '../../utils/formatters'
import { ProductSelector } from './ProductSelector'
import { PriceLineChart } from './PriceLineChart'
import { PeriodControls } from './PeriodControls'
import { CsvDownloadButton } from './CsvDownloadButton'
import { TrendBadge } from '../cards/TrendBadge'

interface PriceChartPanelProps {
  snapshots: PriceSnapshot[]
  selectedSnapshots: PriceSnapshot[]
  selectedProductIds: string[]
  onToggleProduct: (id: string) => void
  periodMode: PeriodMode
  onPeriodModeChange: (mode: PeriodMode) => void
  startDate: string
  endDate: string
  onStartDateChange: (date: string) => void
  onEndDateChange: (date: string) => void
  chartRecords: PriceRecord[]
  onDownloadCsv: () => void
}

export function PriceChartPanel({
  snapshots,
  selectedSnapshots,
  selectedProductIds,
  onToggleProduct,
  periodMode,
  onPeriodModeChange,
  startDate,
  endDate,
  onStartDateChange,
  onEndDateChange,
  chartRecords,
  onDownloadCsv,
}: PriceChartPanelProps) {
  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-5">
      {/* ヘッダー：タイトル + CSVボタン */}
      <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4 mb-4">
        <div>
          <h2 className="text-lg font-bold text-gray-800 mb-1">
            価格チャート
            <span className="text-sm font-normal text-gray-500 ml-2">
              （{selectedSnapshots.length}品目選択中）
            </span>
          </h2>
        </div>
        <CsvDownloadButton onDownload={onDownloadCsv} />
      </div>

      {/* 期間コントロール */}
      <div className="mb-4">
        <PeriodControls
          periodMode={periodMode}
          onPeriodModeChange={onPeriodModeChange}
          startDate={startDate}
          endDate={endDate}
          onStartDateChange={onStartDateChange}
          onEndDateChange={onEndDateChange}
        />
      </div>

      {/* 品目セレクター */}
      <div className="mb-4 pb-4 border-b border-gray-100">
        <ProductSelector
          snapshots={snapshots}
          selectedProductIds={selectedProductIds}
          onToggle={onToggleProduct}
        />
      </div>

      {/* 選択中の品目情報 */}
      <div className="flex flex-wrap gap-3 mb-4">
        {selectedSnapshots.map(({ product, currentPrice, changeAmount, changePercent, trend }) => (
          <div
            key={product.id}
            className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-gray-50 text-sm"
          >
            <span
              className="w-2.5 h-2.5 rounded-full flex-shrink-0"
              style={{ backgroundColor: product.color }}
            />
            <span className="font-medium text-gray-800">{product.nameJa}</span>
            <span className="font-bold tabular-nums" style={{ color: product.color }}>
              {formatPriceJPY(currentPrice)}
            </span>
            <TrendBadge
              changeAmount={changeAmount}
              changePercent={changePercent}
              trend={trend}
            />
          </div>
        ))}
      </div>

      <PriceLineChart
        selectedSnapshots={selectedSnapshots}
        chartRecords={chartRecords}
      />

      <p className="text-xs text-gray-400 mt-3 text-right">
        ※ 価格は参考値です。複数品目をクリックして比較できます
      </p>
    </div>
  )
}
