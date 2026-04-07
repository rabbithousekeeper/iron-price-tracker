import { DATA_SOURCES } from '../../data/products'

export function DataSourcePanel() {
  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-5">
      <h2 className="text-lg font-bold text-gray-800 mb-3">
        データ取得ソース
        <span className="text-sm font-normal text-gray-500 ml-2">（参考情報元）</span>
      </h2>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
        {DATA_SOURCES.map((source) => (
          <a
            key={source.name}
            href={source.url}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-start gap-3 p-3 rounded-lg border border-gray-100 hover:border-brand-200 hover:bg-blue-50 transition-colors group"
          >
            <div className="flex items-center justify-center w-8 h-8 bg-brand-50 rounded-lg flex-shrink-0 group-hover:bg-brand-100 transition-colors">
              <svg className="w-4 h-4 text-brand-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
              </svg>
            </div>
            <div className="min-w-0">
              <p className="text-sm font-semibold text-gray-800 group-hover:text-brand-700 transition-colors">
                {source.name}
                <svg className="inline-block w-3 h-3 ml-1 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                </svg>
              </p>
              <p className="text-xs text-gray-500 mt-0.5">{source.description}</p>
            </div>
          </a>
        ))}
      </div>
    </div>
  )
}
