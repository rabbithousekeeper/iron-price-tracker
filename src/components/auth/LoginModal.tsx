import { useState } from 'react'
import { CREDENTIALS, AUTH_STORAGE_KEY } from '../../config/auth'

interface LoginModalProps {
  onAuthenticated: () => void
}

export function LoginModal({ onAuthenticated }: LoginModalProps) {
  const [userId, setUserId] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (userId === CREDENTIALS.id && password === CREDENTIALS.password) {
      localStorage.setItem(AUTH_STORAGE_KEY, 'true')
      onAuthenticated()
    } else {
      setError('IDまたはパスワードが正しくありません')
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-sm mx-4 p-8">
        {/* ロゴ */}
        <div className="flex flex-col items-center mb-6">
          <div className="flex items-center justify-center w-14 h-14 bg-brand-900 rounded-xl mb-3">
            <svg
              className="w-8 h-8 text-white"
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
          <h2 className="text-xl font-bold text-gray-900">価格トラッカー</h2>
          <p className="text-sm text-gray-500">Price Tracker</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label htmlFor="login-id" className="block text-sm font-medium text-gray-700 mb-1">
              ID
            </label>
            <input
              id="login-id"
              type="text"
              value={userId}
              onChange={(e) => { setUserId(e.target.value); setError('') }}
              className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-brand-500"
              autoFocus
            />
          </div>
          <div>
            <label htmlFor="login-password" className="block text-sm font-medium text-gray-700 mb-1">
              パスワード
            </label>
            <input
              id="login-password"
              type="password"
              value={password}
              onChange={(e) => { setPassword(e.target.value); setError('') }}
              className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-brand-500"
            />
          </div>

          {error && (
            <p className="text-sm text-red-600 font-medium">{error}</p>
          )}

          <button
            type="submit"
            className="w-full bg-brand-700 hover:bg-brand-900 text-white font-medium rounded-lg px-4 py-2.5 text-sm transition-colors"
          >
            ログイン
          </button>
        </form>
      </div>
    </div>
  )
}
