import type { PriceSnapshot, SortKey, TableSort } from '../../types'
import { CATEGORY_LABELS } from '../../data/products'
import { formatPriceJPY, formatChange, formatChangePercent } from '../../utils/formatters'
import { TableSortHeader } from './TableSortHeader'

interface PriceTableProps {
  sortedSnapshots: PriceSnapshot[]
  sort: TableSort
  onSort: (sort: TableSort) => void
}

export function PriceTable({ sortedSnapshots, sort, onSort }: PriceTableProps) {
  const handleSort = (key: SortKey) => {
    onSort({
      key,
      direction: sort.key === key && sort.direction === 'desc' ? 'asc' : 'desc',
    })
  }

  return (
    <div>
      <h2 className="text-lg font-bold text-gray-800 mb-4">
        価格データ一覧
        <span className="text-sm font-normal text-gray-500 ml-2">（クリックで並び替え）</span>
      </h2>
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b border-gray-100">
              <tr>
                <TableSortHeader
                  label="品目"
                  sortKey="name"
                  sort={sort}
                  onSort={handleSort}
                  className="min-w-[160px]"
                />
                <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wide whitespace-nowrap">
                  カテゴリ
                </th>
                <TableSortHeader
                  label="現在価格"
                  sortKey="price"
                  sort={sort}
                  onSort={handleSort}
                  className="text-right"
                />
                <TableSortHeader
                  label="前月比"
                  sortKey="change"
                  sort={sort}
                  onSort={handleSort}
                  className="text-right"
                />
                <TableSortHeader
                  label="前月比(%)"
                  sortKey="changePercent"
                  sort={sort}
                  onSort={handleSort}
                  className="text-right"
                />
                <th className="px-4 py-3 text-right text-xs font-semibold text-gray-500 uppercase tracking-wide whitespace-nowrap hidden md:table-cell">
                  年初来安値
                </th>
                <th className="px-4 py-3 text-right text-xs font-semibold text-gray-500 uppercase tracking-wide whitespace-nowrap hidden md:table-cell">
                  年初来高値
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-50">
              {sortedSnapshots.map((snapshot, index) => {
                const { product, currentPrice, changeAmount, changePercent, trend, ytdMin, ytdMax } =
                  snapshot
                const isUp = trend === 'up'
                const isDown = trend === 'down'

                return (
                  <tr
                    key={product.id}
                    className={`transition-colors duration-150 hover:bg-blue-50 ${
                      index % 2 === 1 ? 'bg-gray-50/50' : 'bg-white'
                    }`}
                  >
                    {/* Product name */}
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2">
                        <span
                          className="w-2.5 h-2.5 rounded-full flex-shrink-0"
                          style={{ backgroundColor: product.color }}
                        />
                        <span className="font-medium text-gray-900">{product.nameJa}</span>
                      </div>
                    </td>

                    {/* Category */}
                    <td className="px-4 py-3">
                      <span
                        className="inline-block text-xs font-medium px-2 py-0.5 rounded-full"
                        style={{
                          backgroundColor: product.color + '1a',
                          color: product.color,
                        }}
                      >
                        {CATEGORY_LABELS[product.category]}
                      </span>
                    </td>

                    {/* Current price */}
                    <td className="px-4 py-3 text-right font-bold tabular-nums text-gray-900">
                      {formatPriceJPY(currentPrice)}
                      <span className="text-xs font-normal text-gray-400 ml-0.5">/t</span>
                    </td>

                    {/* Change amount */}
                    <td
                      className={`px-4 py-3 text-right font-medium tabular-nums ${
                        isUp ? 'text-price-up' : isDown ? 'text-price-down' : 'text-gray-500'
                      }`}
                    >
                      {formatChange(changeAmount)}
                    </td>

                    {/* Change percent */}
                    <td
                      className={`px-4 py-3 text-right font-medium tabular-nums ${
                        isUp ? 'text-price-up' : isDown ? 'text-price-down' : 'text-gray-500'
                      }`}
                    >
                      <span
                        className={`inline-flex items-center justify-end gap-0.5`}
                      >
                        {isUp ? '▲' : isDown ? '▼' : '─'}
                        {formatChangePercent(changePercent)}
                      </span>
                    </td>

                    {/* YTD min */}
                    <td className="px-4 py-3 text-right tabular-nums text-price-down hidden md:table-cell">
                      {formatPriceJPY(ytdMin)}
                    </td>

                    {/* YTD max */}
                    <td className="px-4 py-3 text-right tabular-nums text-price-up hidden md:table-cell">
                      {formatPriceJPY(ytdMax)}
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
        <div className="px-4 py-2 bg-gray-50 border-t border-gray-100 text-xs text-gray-400 text-right">
          {sortedSnapshots.length}品目 表示中
        </div>
      </div>
    </div>
  )
}
