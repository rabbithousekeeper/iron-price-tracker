// ページ種別
type Page = 'dashboard' | 'legal'

interface FooterProps {
  onNavigate?: (page: Page) => void
}

export function Footer({ onNavigate }: FooterProps) {
  return (
    <footer className="bg-gray-800 text-gray-300 mt-16">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div>
            <h3 className="text-white font-semibold mb-2">価格トラッカー</h3>
            <p className="text-sm leading-relaxed">
              鉄鋼・非鉄金属・石油化学製品の市況価格を品目別に追跡・可視化するサービスです。
              スクラップ、薄板、形鋼・棒鋼、鋼管、ステンレス、石油化学、非鉄金属、特殊鋼など幅広い品目に対応しています。
            </p>
          </div>
          <div>
            <h3 className="text-white font-semibold mb-2">免責事項</h3>
            <p className="text-sm leading-relaxed text-gray-400">
              ※ 本データは参考値です。実際の取引価格は市況・地域・数量により異なります。
              投資・取引の判断は自己責任でお願いします。
            </p>
          </div>
          <div>
            <h3 className="text-white font-semibold mb-2">法的情報</h3>
            <p className="text-sm leading-relaxed text-gray-400 mb-2">
              データソースの出典表示、スクレイピングの法的根拠、免責事項の詳細をご確認いただけます。
            </p>
            {onNavigate && (
              <button
                onClick={() => onNavigate('legal')}
                className="inline-flex items-center gap-1 text-sm text-blue-300 hover:text-white transition-colors"
              >
                法的情報・データポリシー
                <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
                </svg>
              </button>
            )}
          </div>
        </div>
        <div className="border-t border-gray-700 mt-6 pt-4 text-xs text-gray-500 text-center">
          &copy; 2026 価格トラッカー / Price Tracker. データは参考値であり、実際の市場価格とは異なる場合があります。
        </div>
      </div>
    </footer>
  )
}
