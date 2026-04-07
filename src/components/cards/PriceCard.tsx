import type { PriceSnapshot } from '../../types'
import { CATEGORY_LABELS } from '../../data/products'
import { formatPriceJPY } from '../../utils/formatters'
import { TrendBadge } from './TrendBadge'

interface PriceCardProps {
  snapshot: PriceSnapshot
  onClick: () => void
  isSelected: boolean
}

export function PriceCard({ snapshot, onClick, isSelected }: PriceCardProps) {
  const { product, currentPrice, changePercent, trend, ytdMin, ytdMax } = snapshot

  // Calculate position of current price within YTD range (0–100%)
  const range = ytdMax - ytdMin
  const position = range > 0 ? ((currentPrice - ytdMin) / range) * 100 : 50

  return (
    <button
      onClick={onClick}
      className={`w-full text-left bg-white rounded-xl shadow-sm border-2 p-4 transition-all duration-150 hover:shadow-md ${
        isSelected
          ? 'border-brand-500 ring-2 ring-brand-100'
          : 'border-transparent hover:border-gray-200'
      }`}
    >
      {/* Header row */}
      <div className="flex items-start justify-between gap-2 mb-3">
        <div className="min-w-0">
          <p className="font-bold text-gray-900 truncate">{product.nameJa}</p>
          <span
            className="inline-block text-xs font-medium px-2 py-0.5 rounded-full mt-1"
            style={{
              backgroundColor: product.color + '1a',
              color: product.color,
            }}
          >
            {CATEGORY_LABELS[product.category]}
          </span>
        </div>
        <div
          className="w-3 h-3 rounded-full flex-shrink-0 mt-1"
          style={{ backgroundColor: product.color }}
        />
      </div>

      {/* Current price */}
      <div className="mb-2">
        <span className="text-2xl font-bold text-gray-900 tabular-nums">
          {formatPriceJPY(currentPrice)}
        </span>
        <span className="text-xs text-gray-500 ml-1">/トン</span>
      </div>

      {/* Change badge */}
      <div className="mb-3">
        <TrendBadge
          changeAmount={snapshot.changeAmount}
          changePercent={changePercent}
          trend={trend}
        />
        <p className="text-xs text-gray-400 mt-0.5">前月比</p>
      </div>

      {/* YTD range bar */}
      <div className="mt-3">
        <div className="flex justify-between text-xs text-gray-400 mb-1">
          <span>年初来安値 {formatPriceJPY(ytdMin)}</span>
          <span>{formatPriceJPY(ytdMax)} 高値</span>
        </div>
        <div className="relative h-1.5 bg-gray-100 rounded-full overflow-hidden">
          <div
            className="absolute inset-y-0 left-0 rounded-full"
            style={{
              width: `${position}%`,
              backgroundColor: product.color,
              opacity: 0.7,
            }}
          />
          <div
            className="absolute top-1/2 -translate-y-1/2 w-2.5 h-2.5 rounded-full border-2 border-white shadow"
            style={{
              left: `calc(${position}% - 5px)`,
              backgroundColor: product.color,
            }}
          />
        </div>
      </div>
    </button>
  )
}
