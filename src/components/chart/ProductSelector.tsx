import type { PriceSnapshot } from '../../types'

interface ProductSelectorProps {
  snapshots: PriceSnapshot[]
  selectedProductId: string
  onSelect: (id: string) => void
}

export function ProductSelector({ snapshots, selectedProductId, onSelect }: ProductSelectorProps) {
  return (
    <div className="flex flex-wrap gap-2">
      {snapshots.map(({ product }) => (
        <button
          key={product.id}
          onClick={() => onSelect(product.id)}
          className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full text-sm font-medium transition-all duration-150 ${
            product.id === selectedProductId
              ? 'text-white shadow-sm'
              : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
          }`}
          style={
            product.id === selectedProductId
              ? { backgroundColor: product.color }
              : undefined
          }
        >
          <span
            className="w-2 h-2 rounded-full flex-shrink-0"
            style={{ backgroundColor: product.id === selectedProductId ? 'white' : product.color }}
          />
          {product.nameJa}
        </button>
      ))}
    </div>
  )
}
