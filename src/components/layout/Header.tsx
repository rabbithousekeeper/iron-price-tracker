import { formatDate } from '../../utils/formatters'

// ページ種別
type Page = 'dashboard' | 'legal'

interface HeaderProps {
  lastUpdated: Date
  onNavigate?: (page: Page) => void
}

export function Header({ lastUpdated, onNavigate }: HeaderProps) {
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
                価格トラッカー
              </h1>
              <p className="text-blue-200 text-sm">
                Price Tracker
              </p>
            </div>
          </div>
          <div className="flex items-center gap-3 text-sm">
            {onNavigate && (
              <button
                onClick={() => onNavigate('legal')}
                className="inline-flex items-center gap-1.5 bg-white/10 hover:bg-white/20 rounded-full px-3 py-1 text-blue-100 transition-colors"
              >
                <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                法的情報
              </button>
            )}
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
