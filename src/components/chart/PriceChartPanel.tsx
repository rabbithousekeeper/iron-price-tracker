import { useState, useMemo } from 'react'
import type { PriceSnapshot, PriceRecord, PeriodMode } from '../../types'
import { formatPriceJPY } from '../../utils/formatters'
import { ProductSelector } from './ProductSelector'
import { PriceLineChart } from './PriceLineChart'
import { IndexLineChart } from './IndexLineChart'
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
  fiscalMonth: number
  onFiscalMonthChange: (month: number) => void
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
  fiscalMonth,
  onFiscalMonthChange,
  startDate,
  endDate,
  onStartDateChange,
  onEndDateChange,
  chartRecords,
  onDownloadCsv,
}: PriceChartPanelProps) {
  const baseLabelOptions = useMemo(() => {
    if (selectedSnapshots.length === 0) return []
    const firstId = selectedSnapshots[0].product.id
    return chartRecords
      .filter((r) => r.productId === firstId)
      .map((r) => r.dateLabel)
  }, [chartRecords, selectedSnapshots])

  const [baseLabel, setBaseLabel] = useState<string>('')
  const effectiveBaseLabel = baseLabelOptions.includes(baseLabel)
    ? baseLabel
    : baseLabelOptions[0] ?? ''

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
          fiscalMonth={fiscalMonth}
          onFiscalMonthChange={onFiscalMonthChange}
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
              {formatPriceJPY(currentPrice, product.unit)}
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

      {/* 指数比較チャート */}
      {baseLabelOptions.length > 0 && (
        <div className="mt-6 pt-6 border-t border-gray-100">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-4">
            <h3 className="text-base font-bold text-gray-800">
              📊 指数比較（基準=100）
            </h3>
            <div className="flex items-center gap-2 text-sm">
              <span className="text-gray-500">基準時点:</span>
              <select
                value={effectiveBaseLabel}
                onChange={(e) => setBaseLabel(e.target.value)}
                className="border border-gray-200 rounded-lg px-2.5 py-1.5 text-xs text-gray-700 bg-white focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-transparent"
              >
                {baseLabelOptions.map((label) => (
                  <option key={label} value={label}>{label}</option>
                ))}
              </select>
            </div>
          </div>
          <IndexLineChart
            selectedSnapshots={selectedSnapshots}
            chartRecords={chartRecords}
            baseLabel={effectiveBaseLabel}
          />
          <p className="text-xs text-gray-400 mt-2 text-right">
            ※ 基準時点の価格を100として各品目の変動率を比較
          </p>
        </div>
      )}
    </div>
  )
}
