import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from 'recharts'
import { ChartContainer } from './ChartContainer'
import { getLabelColorMap } from '../../../lib/chartColors'
import type { LabelerClassCount } from '../../../types/api'

interface Props {
  labelerCounts: LabelerClassCount[]
  labels: string[]
}

export function LabelerLeaderboardChart({ labelerCounts, labels }: Props) {
  const colorMap = getLabelColorMap(labels)
  const sortedLabels = [...labels].sort()

  const data = labelerCounts
    .map((lc) => {
      const total = Object.values(lc.counts).reduce((a, b) => a + b, 0)
      return {
        username: lc.username,
        total,
        ...lc.counts,
      }
    })
    .sort((a, b) => b.total - a.total)

  if (data.length === 0) {
    return (
      <ChartContainer title="Labeler Leaderboard">
        <div className="h-full flex items-center justify-center text-gray-400 text-sm">
          No labeling activity yet
        </div>
      </ChartContainer>
    )
  }

  return (
    <ChartContainer title="Labeler Leaderboard">
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
            dataKey="username"
            tick={{ fontSize: 11 }}
            width={80}
          />
          <Tooltip
            contentStyle={{ fontSize: 12, borderRadius: 8, border: '1px solid #e5e7eb' }}
          />
          <Legend wrapperStyle={{ fontSize: 12 }} />

          {sortedLabels.map((label) => (
            <Bar
              key={label}
              dataKey={label}
              stackId="labels"
              fill={colorMap[label]}
              name={label}
              radius={[0, 4, 4, 0]}
            />
          ))}
        </BarChart>
      </ResponsiveContainer>
    </ChartContainer>
  )
}
