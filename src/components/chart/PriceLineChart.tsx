import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ReferenceLine,
  ResponsiveContainer,
} from 'recharts'
import type { PriceSnapshot } from '../../types'
import { formatYAxisTick } from '../../utils/formatters'
import { ChartTooltip } from './ChartTooltip'

interface PriceLineChartProps {
  snapshot: PriceSnapshot
}

export function PriceLineChart({ snapshot }: PriceLineChartProps) {
  const { product, history, currentPrice } = snapshot

  // Add prevPrice to each data point for tooltip display
  const data = history.map((record, index) => ({
    ...record,
    prevPrice: index > 0 ? history[index - 1].price : undefined,
  }))

  const prices = history.map((r) => r.price)
  const minPrice = Math.min(...prices)
  const maxPrice = Math.max(...prices)
  const padding = (maxPrice - minPrice) * 0.1
  const yDomain = [
    Math.floor((minPrice - padding) / 1000) * 1000,
    Math.ceil((maxPrice + padding) / 1000) * 1000,
  ]

  return (
    <div className="w-full h-72">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data} margin={{ top: 5, right: 20, left: 10, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
          <XAxis
            dataKey="monthLabel"
            tick={{ fontSize: 11, fill: '#6b7280' }}
            tickLine={false}
            axisLine={{ stroke: '#e5e7eb' }}
            interval={2}
          />
          <YAxis
            domain={yDomain}
            tickFormatter={formatYAxisTick}
            tick={{ fontSize: 11, fill: '#6b7280' }}
            tickLine={false}
            axisLine={false}
            width={55}
          />
          <Tooltip content={<ChartTooltip />} />
          <ReferenceLine
            y={currentPrice}
            stroke={product.color}
            strokeDasharray="4 4"
            strokeOpacity={0.5}
            label={{
              value: '現在',
              position: 'right',
              fontSize: 11,
              fill: product.color,
            }}
          />
          <Line
            type="monotone"
            dataKey="price"
            stroke={product.color}
            strokeWidth={2.5}
            dot={{ r: 3, fill: product.color, strokeWidth: 0 }}
            activeDot={{ r: 5, fill: product.color, stroke: 'white', strokeWidth: 2 }}
            isAnimationActive={true}
            animationDuration={600}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}
