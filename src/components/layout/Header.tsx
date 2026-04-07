import { formatDate } from '../../utils/formatters'

interface HeaderProps {
  lastUpdated: Date
}

export function Header({ lastUpdated }: HeaderProps) {
  return (
    <header className="bg-brand-900 text-white shadow-lg">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
          <div className="flex items-center gap-3">
            <div className="flex items-center justify-center w-10 h-10 bg-white/10 rounded-lg">
              <svg
                className="w-6 h-6 text-white"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                strokeWidth={2}
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6"
                />
              </svg>
            </div>
            <div>
              <h1 className="text-xl font-bold leading-tight">
                鉄・鋼材価格トラッカー
              </h1>
              <p className="text-blue-200 text-sm">
                Japan Iron &amp; Steel Price Tracker
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2 text-sm">
            <span className="inline-flex items-center gap-1.5 bg-white/10 rounded-full px-3 py-1">
              <span className="w-2 h-2 bg-green-400 rounded-full animate-pulse" />
              <span className="text-blue-100">
                {formatDate(lastUpdated)} 現在
              </span>
            </span>
          </div>
        </div>
      </div>
    </header>
  )
}
