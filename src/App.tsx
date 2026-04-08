import { useState } from 'react'
import { DashboardPage } from './components/dashboard/DashboardPage'
import { LegalPage } from './components/legal/LegalPage'
import { LoginModal } from './components/auth/LoginModal'
import { AUTH_STORAGE_KEY } from './config/auth'

// ページ種別
type Page = 'dashboard' | 'legal'

export default function App() {
  const [page, setPage] = useState<Page>('dashboard')
  const [isAuthenticated, setIsAuthenticated] = useState(
    () => localStorage.getItem(AUTH_STORAGE_KEY) === 'true'
  )

  // 未認証時はログインモーダルを表示
  if (!isAuthenticated) {
    return <LoginModal onAuthenticated={() => setIsAuthenticated(true)} />
  }

  const handleLogout = () => {
    setIsAuthenticated(false)
  }

  if (page === 'legal') {
    return (
      <div className="min-h-screen flex flex-col">
        <HeaderNav onNavigate={setPage} onLogout={handleLogout} />
        <main className="flex-1">
          <LegalPage onBack={() => setPage('dashboard')} />
        </main>
        <FooterNav onNavigate={setPage} />
      </div>
    )
  }

  return <DashboardPage onNavigate={setPage} onLogout={handleLogout} />
}

/* ヘッダー（法的情報ページ用の簡易版） */
function HeaderNav({ onNavigate, onLogout }: { onNavigate: (p: Page) => void; onLogout: () => void }) {
  const handleLogout = () => {
    localStorage.removeItem(AUTH_STORAGE_KEY)
    onLogout()
  }

  return (
    <header className="bg-brand-900 text-white shadow-lg">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
        <div className="flex items-center justify-between">
          <button onClick={() => onNavigate('dashboard')} className="flex items-center gap-3 hover:opacity-80 transition-opacity">
            <div className="flex items-center justify-center w-10 h-10 bg-white/10 rounded-lg">
              <svg className="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
              </svg>
            </div>
            <div>
              <h1 className="text-xl font-bold leading-tight">価格トラッカー</h1>
              <p className="text-blue-200 text-sm">Price Tracker</p>
            </div>
          </button>
          <button
            onClick={handleLogout}
            className="inline-flex items-center gap-1.5 bg-white/10 hover:bg-white/20 rounded-full px-3 py-1 text-sm text-blue-100 transition-colors"
          >
            <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
            </svg>
            ログアウト
          </button>
        </div>
      </div>
    </header>
  )
}

/* フッター（法的情報ページ用の簡易版） */
function FooterNav({ onNavigate }: { onNavigate: (p: Page) => void }) {
  return (
    <footer className="bg-gray-800 text-gray-300 mt-16">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 text-center">
        <button
          onClick={() => onNavigate('dashboard')}
          className="text-sm text-blue-300 hover:text-white transition-colors"
        >
          ダッシュボードに戻る
        </button>
        <div className="border-t border-gray-700 mt-4 pt-4 text-xs text-gray-500">
          &copy; 2026 価格トラッカー / Price Tracker. データは参考値であり、実際の市場価格とは異なる場合があります。
        </div>
      </div>
    </footer>
  )
}
