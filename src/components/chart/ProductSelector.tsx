import type { PriceSnapshot, ProductCategory } from '../../types'
import { CATEGORY_LABELS, CATEGORY_ORDER } from '../../data/products'

interface ProductSelectorProps {
  snapshots: PriceSnapshot[]
  selectedProductIds: string[]
  onToggle: (id: string) => void
}

export function ProductSelector({ snapshots, selectedProductIds, onToggle }: ProductSelectorProps) {
  // カテゴリごとにグループ化
  const grouped = new Map<ProductCategory, PriceSnapshot[]>()
  for (const snapshot of snapshots) {
    const cat = snapshot.product.category
    if (!grouped.has(cat)) grouped.set(cat, [])
    grouped.get(cat)!.push(snapshot)
  }

  return (
    <div className="space-y-3">
      {CATEGORY_ORDER.filter((cat) => grouped.has(cat)).map((cat) => (
        <div key={cat}>
          <p className="text-xs font-semibold text-gray-500 mb-1">
            {CATEGORY_LABELS[cat]}
          </p>
          <div className="flex flex-wrap gap-1.5">
            {grouped.get(cat)!.map(({ product }) => {
              const isSelected = selectedProductIds.includes(product.id)
              return (
                <button
                  key={product.id}
                  onClick={() => onToggle(product.id)}
                  className={`flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium transition-all duration-150 ${
                    isSelected
                      ? 'text-white shadow-sm'
                      : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                  }`}
                  style={
                    isSelected
                      ? { backgroundColor: product.color }
                      : undefined
                  }
                >
                  <span
                    className="w-2 h-2 rounded-full flex-shrink-0"
                    style={{ backgroundColor: isSelected ? 'white' : product.color }}
                  />
                  {product.nameJa}
                </button>
              )
            })}
          </div>
        </div>
      ))}
    </div>
  )
}
