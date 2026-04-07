import type { TooltipProps } from 'recharts'
import type { ValueType, NameType } from 'recharts/types/component/DefaultTooltipContent'
import { formatPriceJPY } from '../../utils/formatters'

export function ChartTooltip({ active, payload, label }: TooltipProps<ValueType, NameType>) {
  if (!active || !payload || payload.length === 0) return null

  const price = payload[0].value as number
  const prevPrice = payload[0].payload?.prevPrice as number | undefined

  const change = prevPrice !== undefined ? price - prevPrice : null
  const changePercent = prevPrice !== undefined ? ((price - prevPrice) / prevPrice) * 100 : null

  return (
    <div className="bg-white border border-gray-200 rounded-lg shadow-lg p-3 text-sm min-w-[160px]">
      <p className="font-semibold text-gray-700 mb-1">{label}</p>
      <p className="text-lg font-bold text-gray-900">{formatPriceJPY(price)}</p>
      <p className="text-xs text-gray-400">円/トン</p>
      {change !== null && changePercent !== null && (
        <div
          className={`mt-1.5 text-xs font-medium ${
            change > 0 ? 'text-price-up' : change < 0 ? 'text-price-down' : 'text-gray-500'
          }`}
        >
          前月比: {change > 0 ? '+' : ''}{change.toLocaleString('ja-JP')}円
          ({changePercent > 0 ? '+' : ''}{changePercent.toFixed(1)}%)
        </div>
      )}
    </div>
  )
}
