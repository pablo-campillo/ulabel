import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from 'recharts'
import { ChartContainer } from './ChartContainer'
import { getLabelColorMap } from '../../../lib/chartColors'

interface Props {
  distribution: Record<string, number>
}

export function LabelDistributionChart({ distribution }: Props) {
  const labels = Object.keys(distribution).sort()
  const colorMap = getLabelColorMap(labels)
  const total = Object.values(distribution).reduce((a, b) => a + b, 0)

  const data = labels.map((label) => ({
    label,
    count: distribution[label],
    percentage: total > 0 ? ((distribution[label] / total) * 100).toFixed(1) : '0',
  }))

  if (data.length === 0) {
    return (
      <ChartContainer title="Label Distribution">
        <div className="h-full flex items-center justify-center text-gray-400 text-sm">
          No labels submitted yet
        </div>
      </ChartContainer>
    )
  }

  return (
    <ChartContainer title="Label Distribution">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart
          data={data}
          layout="vertical"
          margin={{ top: 5, right: 30, bottom: 5, left: 0 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" horizontal={false} />
          <XAxis type="number" tick={{ fontSize: 11 }} />
          <YAxis
            type="category"
            dataKey="label"
            tick={{ fontSize: 11 }}
            width={80}
          />
          <Tooltip
            contentStyle={{ fontSize: 12, borderRadius: 8, border: '1px solid #e5e7eb' }}
            formatter={(value, _name, props) => {
              const pct = (props.payload as { percentage: string }).percentage
              return [`${value} (${pct}%)`, 'Count']
            }}
          />
          <Bar dataKey="count" radius={[0, 4, 4, 0]}>
            {data.map((entry) => (
              <Cell key={entry.label} fill={colorMap[entry.label]} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </ChartContainer>
  )
}
