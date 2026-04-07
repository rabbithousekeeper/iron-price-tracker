import type { PriceSnapshot } from '../../types'
import { formatPriceJPY } from '../../utils/formatters'
import { ProductSelector } from './ProductSelector'
import { PriceLineChart } from './PriceLineChart'
import { TrendBadge } from '../cards/TrendBadge'

interface PriceChartPanelProps {
  snapshots: PriceSnapshot[]
  selectedSnapshot: PriceSnapshot
  selectedProductId: string
  onSelectProduct: (id: string) => void
}

export function PriceChartPanel({
  snapshots,
  selectedSnapshot,
  selectedProductId,
  onSelectProduct,
}: PriceChartPanelProps) {
  const { product, currentPrice, changeAmount, changePercent, trend, ytdMin, ytdMax } =
    selectedSnapshot

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-5">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-5">
        <div>
          <h2 className="text-lg font-bold text-gray-800 mb-1">
            価格チャート
            <span className="text-sm font-normal text-gray-500 ml-2">（過去13ヶ月）</span>
          </h2>
          <ProductSelector
            snapshots={snapshots}
            selectedProductId={selectedProductId}
            onSelect={onSelectProduct}
          />
        </div>
      </div>

      {/* Selected product info */}
      <div className="flex flex-wrap items-baseline gap-x-4 gap-y-1 mb-4 pb-4 border-b border-gray-100">
        <h3 className="text-lg font-bold text-gray-900">{product.nameJa}</h3>
        <span className="text-2xl font-bold tabular-nums" style={{ color: product.color }}>
          {formatPriceJPY(currentPrice)}
          <span className="text-sm font-normal text-gray-500">/トン</span>
        </span>
        <TrendBadge
          changeAmount={changeAmount}
          changePercent={changePercent}
          trend={trend}
        />
        <div className="text-xs text-gray-500 ml-auto">
          <span>年初来: </span>
          <span className="text-price-down font-medium">{formatPriceJPY(ytdMin)}</span>
          <span className="mx-1">─</span>
          <span className="text-price-up font-medium">{formatPriceJPY(ytdMax)}</span>
        </div>
      </div>

      <p className="text-xs text-gray-500 mb-2">{product.description}</p>

      <PriceLineChart snapshot={selectedSnapshot} />

      <p className="text-xs text-gray-400 mt-3 text-right">
        ※ 価格は参考値です
      </p>
    </div>
  )
}
