import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ReferenceLine,
  ResponsiveContainer,
} from 'recharts'
import type { PriceRecord, PriceSnapshot } from '../../types'
import { PRODUCTS } from '../../data/products'

interface IndexLineChartProps {
  selectedSnapshots: PriceSnapshot[]
  chartRecords: PriceRecord[]
  baseLabel: string
}

export function IndexLineChart({ selectedSnapshots, chartRecords, baseLabel }: IndexLineChartProps) {
  if (selectedSnapshots.length === 0) return null

  // 基準時点の各品目価格を取得
  const basePrices = new Map<string, number>()
  for (const snapshot of selectedSnapshots) {
    const baseRecord = chartRecords.find(
      (r) => r.productId === snapshot.product.id && r.dateLabel === baseLabel
    )
    if (baseRecord) {
      basePrices.set(snapshot.product.id, baseRecord.price)
    }
  }

  // 基準データがある品目のみ対象
  const validSnapshots = selectedSnapshots.filter((s) => basePrices.has(s.product.id))
  if (validSnapshots.length === 0) return null

  // 日付ラベル一覧（最初の品目基準）
  const firstProductId = validSnapshots[0].product.id
  const dateLabels = chartRecords
    .filter((r) => r.productId === firstProductId)
    .map((r) => ({ date: r.date, dateLabel: r.dateLabel }))

  // 指数化データを構築
  const data = dateLabels.map(({ date, dateLabel }) => {
    const point: Record<string, unknown> = { date, dateLabel }
    for (const snapshot of validSnapshots) {
      const record = chartRecords.find(
        (r) => r.productId === snapshot.product.id && r.dateLabel === dateLabel
      )
      if (record) {
        const basePrice = basePrices.get(snapshot.product.id)!
        point[snapshot.product.id] = (record.price / basePrice) * 100
      }
    }
    return point
  })

  // X軸の間引き
  const interval = data.length > 30 ? Math.floor(data.length / 12) : data.length > 13 ? 2 : 0

  return (
    <div className="w-full h-72">
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
            tick={{ fontSize: 11, fill: '#6b7280' }}
            tickLine={false}
            axisLine={false}
            width={45}
          />
          <ReferenceLine y={100} stroke="#9ca3af" strokeDasharray="4 4" strokeWidth={1.5} />
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
                          {(entry.value as number).toFixed(1)}
                        </span>
                      </div>
                    )
                  })}
                </div>
              )
            }}
          />
          {validSnapshots.length > 1 && (
            <Legend
              formatter={(value: string) => {
                const product = PRODUCTS.find((p) => p.id === value)
                return product ? product.nameJa : value
              }}
              wrapperStyle={{ fontSize: 12 }}
            />
          )}
          {validSnapshots.map((snapshot) => (
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
