import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts'
import type { PriceRecord, PriceSnapshot } from '../../types'
import { formatYAxisTick, formatPriceJPY } from '../../utils/formatters'
import { PRODUCTS } from '../../data/products'

interface PriceLineChartProps {
  selectedSnapshots: PriceSnapshot[]
  chartRecords: PriceRecord[]
}

export function PriceLineChart({ selectedSnapshots, chartRecords }: PriceLineChartProps) {
  if (selectedSnapshots.length === 0) return null

  // 日付ラベルの一覧を取得（最初の品目基準）
  const firstProductId = selectedSnapshots[0].product.id
  const dateLabels = chartRecords
    .filter((r) => r.productId === firstProductId)
    .map((r) => ({ date: r.date, dateLabel: r.dateLabel }))

  // グラフ用データを構築：各日付ラベルごとに全品目の価格を横並びに
  const data = dateLabels.map(({ date, dateLabel }) => {
    const point: Record<string, unknown> = { date, dateLabel }
    for (const snapshot of selectedSnapshots) {
      // dateLabelで一致する品目を検索（集約モードでも正しくマッチ）
      const record = chartRecords.find(
        (r) => r.productId === snapshot.product.id && r.dateLabel === dateLabel
      )
      if (record) {
        point[snapshot.product.id] = record.price
      }
    }
    return point
  })

  // Y軸の範囲を計算
  const allPrices = chartRecords.map((r) => r.price)
  const minPrice = Math.min(...allPrices)
  const maxPrice = Math.max(...allPrices)
  const padding = (maxPrice - minPrice) * 0.1 || maxPrice * 0.1

  // 適切な丸め単位を決定
  const range = maxPrice - minPrice + 2 * padding
  let roundUnit = 1000
  if (range < 100) roundUnit = 1
  else if (range < 1000) roundUnit = 10
  else if (range < 10000) roundUnit = 100

  const yDomain = [
    Math.floor((minPrice - padding) / roundUnit) * roundUnit,
    Math.ceil((maxPrice + padding) / roundUnit) * roundUnit,
  ]

  // X軸のintervalを算出（データ点が多い場合に間引き）
  const interval = data.length > 30 ? Math.floor(data.length / 12) : data.length > 13 ? 2 : 0

  return (
    <div className="w-full h-80">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data} margin={{ top: 5, right: 20, left: 10, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
          <XAxis
            dataKey="dateLabel"
            tick={{ fontSize: 10, fill: '#6b7280' }}
            tickLine={false}
            axisLine={{ stroke: '#e5e7eb' }}
            interval={interval}
            angle={data.length > 20 ? -30 : 0}
            textAnchor={data.length > 20 ? 'end' : 'middle'}
            height={data.length > 20 ? 60 : 30}
          />
          <YAxis
            domain={yDomain}
            tickFormatter={formatYAxisTick}
            tick={{ fontSize: 11, fill: '#6b7280' }}
            tickLine={false}
            axisLine={false}
            width={60}
          />
          <Tooltip
            content={({ active, payload, label }) => {
              if (!active || !payload || payload.length === 0) return null
              return (
                <div className="bg-white border border-gray-200 rounded-lg shadow-lg p-3 text-sm min-w-[180px]">
                  <p className="font-semibold text-gray-700 mb-2">{label}</p>
                  {payload.map((entry) => {
                    const product = PRODUCTS.find((p) => p.id === entry.dataKey)
                    if (!product) return null
                    return (
                      <div key={entry.dataKey} className="flex items-center gap-2 mb-1">
                        <span
                          className="w-2.5 h-2.5 rounded-full flex-shrink-0"
                          style={{ backgroundColor: entry.color }}
                        />
                        <span className="text-gray-600 text-xs">{product.nameJa}:</span>
                        <span className="font-bold text-gray-900 ml-auto">
                          {formatPriceJPY(entry.value as number)}
                        </span>
                      </div>
                    )
                  })}
                </div>
              )
            }}
          />
          {selectedSnapshots.length > 1 && (
            <Legend
              formatter={(value: string) => {
                const product = PRODUCTS.find((p) => p.id === value)
                return product ? product.nameJa : value
              }}
              wrapperStyle={{ fontSize: 12 }}
            />
          )}
          {selectedSnapshots.map((snapshot) => (
            <Line
              key={snapshot.product.id}
              type="monotone"
              dataKey={snapshot.product.id}
              name={snapshot.product.id}
              stroke={snapshot.product.color}
              strokeWidth={2}
              dot={data.length <= 30 ? { r: 2.5, fill: snapshot.product.color, strokeWidth: 0 } : false}
              activeDot={{ r: 4, fill: snapshot.product.color, stroke: 'white', strokeWidth: 2 }}
              isAnimationActive={true}
              animationDuration={600}
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}
