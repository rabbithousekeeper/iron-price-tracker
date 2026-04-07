import type { PriceSnapshot } from '../../types'
import { PriceCard } from './PriceCard'

interface PriceCardGridProps {
  snapshots: PriceSnapshot[]
  selectedProductId: string
  onSelect: (id: string) => void
}

export function PriceCardGrid({ snapshots, selectedProductId, onSelect }: PriceCardGridProps) {
  return (
    <div>
      <h2 className="text-lg font-bold text-gray-800 mb-4">
        現在の価格
        <span className="text-sm font-normal text-gray-500 ml-2">（前月比）</span>
      </h2>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
        {snapshots.map((snapshot) => (
          <PriceCard
            key={snapshot.product.id}
            snapshot={snapshot}
            isSelected={snapshot.product.id === selectedProductId}
            onClick={() => onSelect(snapshot.product.id)}
          />
        ))}
      </div>
      <p className="text-xs text-gray-400 mt-3">
        ※ カードをクリックするとチャートに詳細が表示されます
      </p>
    </div>
  )
}
