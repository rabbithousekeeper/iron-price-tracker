import { formatChange, formatChangePercent } from '../../utils/formatters'

interface TrendBadgeProps {
  changeAmount: number
  changePercent: number
  trend: 'up' | 'down' | 'flat'
}

export function TrendBadge({ changeAmount, changePercent, trend }: TrendBadgeProps) {
  if (trend === 'flat') {
    return (
      <span className="inline-flex items-center gap-1 text-gray-500 text-sm font-medium">
        <span>─</span>
        <span>変化なし</span>
      </span>
    )
  }

  const isUp = trend === 'up'

  return (
    <span
      className={`inline-flex items-center gap-1 text-sm font-medium ${
        isUp ? 'text-price-up' : 'text-price-down'
      }`}
    >
      <svg
        className="w-4 h-4"
        fill="currentColor"
        viewBox="0 0 20 20"
      >
        {isUp ? (
          <path
            fillRule="evenodd"
            d="M5.293 9.707a1 1 0 010-1.414l4-4a1 1 0 011.414 0l4 4a1 1 0 01-1.414 1.414L11 7.414V15a1 1 0 11-2 0V7.414L6.707 9.707a1 1 0 01-1.414 0z"
            clipRule="evenodd"
          />
        ) : (
          <path
            fillRule="evenodd"
            d="M14.707 10.293a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 111.414-1.414L9 12.586V5a1 1 0 012 0v7.586l2.293-2.293a1 1 0 011.414 0z"
            clipRule="evenodd"
          />
        )}
      </svg>
      <span>
        {formatChange(changeAmount)}円 ({formatChangePercent(changePercent)})
      </span>
    </span>
  )
}
