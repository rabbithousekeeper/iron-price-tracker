import type { PeriodMode } from '../../types'

interface PeriodControlsProps {
  periodMode: PeriodMode
  onPeriodModeChange: (mode: PeriodMode) => void
  startDate: string
  endDate: string
  onStartDateChange: (date: string) => void
  onEndDateChange: (date: string) => void
}

const PERIOD_OPTIONS: { value: PeriodMode; label: string }[] = [
  { value: 'day', label: '日別' },
  { value: 'month', label: '月別' },
  { value: 'year', label: '年別' },
]

export function PeriodControls({
  periodMode,
  onPeriodModeChange,
  startDate,
  endDate,
  onStartDateChange,
  onEndDateChange,
}: PeriodControlsProps) {
  return (
    <div className="flex flex-col sm:flex-row items-start sm:items-center gap-3">
      {/* 期間モード切り替え */}
      <div className="flex rounded-lg border border-gray-200 overflow-hidden">
        {PERIOD_OPTIONS.map(({ value, label }) => (
          <button
            key={value}
            onClick={() => onPeriodModeChange(value)}
            className={`px-3 py-1.5 text-xs font-medium transition-colors ${
              periodMode === value
                ? 'bg-brand-500 text-white'
                : 'bg-white text-gray-600 hover:bg-gray-50'
            }`}
          >
            {label}
          </button>
        ))}
      </div>

      {/* 日付ピッカー */}
      <div className="flex items-center gap-2 text-sm">
        <input
          type="date"
          value={startDate}
          min="2024-04-01"
          max={endDate}
          onChange={(e) => onStartDateChange(e.target.value)}
          className="border border-gray-200 rounded-lg px-2.5 py-1.5 text-xs text-gray-700 focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-transparent"
        />
        <span className="text-gray-400 text-xs">〜</span>
        <input
          type="date"
          value={endDate}
          min={startDate}
          max="2026-04-07"
          onChange={(e) => onEndDateChange(e.target.value)}
          className="border border-gray-200 rounded-lg px-2.5 py-1.5 text-xs text-gray-700 focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-transparent"
        />
      </div>
    </div>
  )
}
