import type { SortKey, TableSort } from '../../types'

interface TableSortHeaderProps {
  label: string
  sortKey: SortKey
  sort: TableSort
  onSort: (key: SortKey) => void
  className?: string
}

export function TableSortHeader({
  label,
  sortKey,
  sort,
  onSort,
  className = '',
}: TableSortHeaderProps) {
  const isActive = sort.key === sortKey

  return (
    <th
      className={`px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide cursor-pointer select-none whitespace-nowrap ${
        isActive ? 'text-brand-500' : 'text-gray-500 hover:text-gray-700'
      } ${className}`}
      onClick={() => onSort(sortKey)}
    >
      <span className="flex items-center gap-1">
        {label}
        <span className={isActive ? 'text-brand-500' : 'text-gray-300'}>
          {isActive && sort.direction === 'asc' ? '▲' : '▼'}
        </span>
      </span>
    </th>
  )
}
