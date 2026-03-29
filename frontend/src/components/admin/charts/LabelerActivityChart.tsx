import { useState } from 'react'
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
  Brush,
} from 'recharts'
import { ChartContainer } from './ChartContainer'
import { getLabelColorMap } from '../../../lib/chartColors'
import type { LabelerDailyActivity } from '../../../types/api'

interface Props {
  labelerActivity: LabelerDailyActivity[]
  labels: string[]
}

export function LabelerActivityChart({ labelerActivity, labels }: Props) {
  const [selectedLabeler, setSelectedLabeler] = useState<string>(
    labelerActivity[0]?.labeler_id ?? '',
  )

  const colorMap = getLabelColorMap(labels)
  const sortedLabels = [...labels].sort()

  const labeler = labelerActivity.find((l) => l.labeler_id === selectedLabeler)
  const data = (labeler?.daily ?? [])
    .map((d) => ({
      date: d.date,
      ...d.counts,
    }))
    .sort((a, b) => a.date.localeCompare(b.date))

  if (labelerActivity.length === 0) {
    return (
      <ChartContainer title="Labeler Daily Activity">
        <div className="h-full flex items-center justify-center text-gray-400 text-sm">
          No labeler activity yet
        </div>
      </ChartContainer>
    )
  }

  return (
    <ChartContainer title="Labeler Daily Activity">
      <div className="mb-3">
        <select
          value={selectedLabeler}
          onChange={(e) => setSelectedLabeler(e.target.value)}
          className="px-3 py-1.5 text-sm border border-gray-300 rounded-lg focus:border-primary-500 focus:ring-2 focus:ring-primary-200 outline-none cursor-pointer"
        >
          {labelerActivity.map((l) => (
            <option key={l.labeler_id} value={l.labeler_id}>
              {l.username}
            </option>
          ))}
        </select>
      </div>
      <div className="h-[calc(100%-2.5rem)]">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} margin={{ top: 5, right: 20, bottom: 5, left: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
            <XAxis
              dataKey="date"
              tick={{ fontSize: 11 }}
              tickFormatter={(d: string) => {
                const date = new Date(d)
                return `${date.getMonth() + 1}/${date.getDate()}`
              }}
            />
            <YAxis tick={{ fontSize: 11 }} allowDecimals={false} />
            <Tooltip
              contentStyle={{ fontSize: 12, borderRadius: 8, border: '1px solid #e5e7eb' }}
              labelFormatter={(label) => new Date(String(label)).toLocaleDateString()}
            />
            <Legend wrapperStyle={{ fontSize: 12 }} />

            {sortedLabels.map((label) => (
              <Bar
                key={label}
                dataKey={label}
                stackId="labels"
                fill={colorMap[label]}
                name={label}
              />
            ))}

            {data.length > 10 && (
              <Brush
                dataKey="date"
                height={25}
                stroke="#4c6ef5"
                tickFormatter={(d: string) => {
                  const date = new Date(d)
                  return `${date.getMonth() + 1}/${date.getDate()}`
                }}
              />
            )}
          </BarChart>
        </ResponsiveContainer>
      </div>
    </ChartContainer>
  )
}
