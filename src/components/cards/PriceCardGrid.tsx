import { useState } from 'react'
import type { PriceSnapshot, ProductCategory } from '../../types'
import { CATEGORY_LABELS, CATEGORY_ORDER } from '../../data/products'
import { PriceCard } from './PriceCard'

interface PriceCardGridProps {
  snapshots: PriceSnapshot[]
  selectedProductIds: string[]
  onToggle: (id: string) => void
}

export function PriceCardGrid({ snapshots, selectedProductIds, onToggle }: PriceCardGridProps) {
  const [isOpen, setIsOpen] = useState(false)

  // カテゴリごとにグループ化
  const grouped = new Map<ProductCategory, PriceSnapshot[]>()
  for (const snapshot of snapshots) {
    const cat = snapshot.product.category
    if (!grouped.has(cat)) grouped.set(cat, [])
    grouped.get(cat)!.push(snapshot)
  }

  return (
    <div>
      {/* アコーディオンヘッダー */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full flex items-center justify-between text-left group mb-4"
      >
        <h2 className="text-lg font-bold text-gray-800">
          現在の価格
          <span className="text-sm font-normal text-gray-500 ml-2">（前月比）</span>
        </h2>
        <span
          className={`text-gray-400 group-hover:text-gray-600 transition-transform duration-200 ${
            isOpen ? 'rotate-0' : '-rotate-90'
          }`}
        >
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
          </svg>
        </span>
      </button>

      {/* アコーディオンコンテンツ */}
      {isOpen && (
        <>
          {CATEGORY_ORDER.filter((cat) => grouped.has(cat)).map((cat) => (
            <div key={cat} className="mb-6">
              <h3 className="text-sm font-semibold text-gray-500 mb-2 flex items-center gap-2">
                <span className="inline-block w-1 h-4 bg-brand-500 rounded-full" />
                {CATEGORY_LABELS[cat]}
              </h3>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-3">
                {grouped.get(cat)!.map((snapshot) => (
                  <PriceCard
                    key={snapshot.product.id}
                    snapshot={snapshot}
                    isSelected={selectedProductIds.includes(snapshot.product.id)}
                    onClick={() => onToggle(snapshot.product.id)}
                  />
                ))}
              </div>
            </div>
          ))}
          <p className="text-xs text-gray-400 mt-3">
            ※ カードをクリックしてチャートに表示する品目を選択できます（複数選択可）
          </p>
        </>
      )}
    </div>
  )
}
