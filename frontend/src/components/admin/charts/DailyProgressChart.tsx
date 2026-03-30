import { useState, useMemo, useCallback } from 'react'
import {
  ComposedChart,
  Bar,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ReferenceLine,
  ReferenceArea,
  ResponsiveContainer,
  Brush,
  Legend,
} from 'recharts'
import { ChartContainer } from './ChartContainer'
import { buildDailyChartData } from '../../../lib/regression'
import { getLabelColorMap } from '../../../lib/chartColors'
import type { ProjectStats } from '../../../types/api'

interface Props {
  stats: ProjectStats
  labels: string[]
}

export function DailyProgressChart({ stats, labels }: Props) {
  const colorMap = getLabelColorMap(labels)
  const sortedLabels = [...labels].sort()

  const data = buildDailyChartData(
    stats.daily_totals,
    stats.labeler_daily_activity,
    labels,
    stats.total_images,
  )

  const [refAreaLeft, setRefAreaLeft] = useState<string | null>(null)
  const [refAreaRight, setRefAreaRight] = useState<string | null>(null)
  const [zoomLeft, setZoomLeft] = useState<string | null>(null)
  const [zoomRight, setZoomRight] = useState<string | null>(null)

  const zoomedData = useMemo(() => {
    if (!zoomLeft || !zoomRight) return data
    const leftIdx = data.findIndex((d) => d.date === zoomLeft)
    const rightIdx = data.findIndex((d) => d.date === zoomRight)
    if (leftIdx === -1 || rightIdx === -1) return data
    const start = Math.min(leftIdx, rightIdx)
    const end = Math.max(leftIdx, rightIdx)
    return data.slice(start, end + 1)
  }, [data, zoomLeft, zoomRight])

  const isZoomed = zoomLeft !== null && zoomRight !== null

  const handleMouseDown = useCallback(
    (e: { activeLabel?: string }) => {
      if (e?.activeLabel) setRefAreaLeft(e.activeLabel)
    },
    [],
  )

  const handleMouseMove = useCallback(
    (e: { activeLabel?: string }) => {
      if (refAreaLeft && e?.activeLabel) setRefAreaRight(e.activeLabel)
    },
    [refAreaLeft],
  )

  const handleMouseUp = useCallback(() => {
    if (!refAreaLeft || !refAreaRight) {
      setRefAreaLeft(null)
      setRefAreaRight(null)
      return
    }

    const leftIdx = data.findIndex((d) => d.date === refAreaLeft)
    const rightIdx = data.findIndex((d) => d.date === refAreaRight)

    if (leftIdx === rightIdx) {
      setRefAreaLeft(null)
      setRefAreaRight(null)
      return
    }

    const start = Math.min(leftIdx, rightIdx)
    const end = Math.max(leftIdx, rightIdx)

    setZoomLeft(data[start].date)
    setZoomRight(data[end].date)
    setRefAreaLeft(null)
    setRefAreaRight(null)
  }, [refAreaLeft, refAreaRight, data])

  const handleResetZoom = useCallback(() => {
    setZoomLeft(null)
    setZoomRight(null)
  }, [])

  if (data.length === 0) {
    return (
      <ChartContainer title="Daily Labeling Progress">
        <div className="h-full flex items-center justify-center text-gray-400 text-sm">
          No labeling activity yet
        </div>
      </ChartContainer>
    )
  }

  // Find the estimated completion date from regression data
  const completionPoint = data.find(
    (d) => d.regressionY !== null && d.regressionY >= stats.total_images,
  )

  return (
    <ChartContainer
      title="Daily Labeling Progress"
      isZoomed={isZoomed}
      onResetZoom={handleResetZoom}
    >
      <ResponsiveContainer width="100%" height="100%">
        <ComposedChart
          data={zoomedData}
          margin={{ top: 5, right: 20, bottom: 5, left: 0 }}
          onMouseDown={handleMouseDown}
          onMouseMove={handleMouseMove}
          onMouseUp={handleMouseUp}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
          <XAxis
            dataKey="date"
            tick={{ fontSize: 11 }}
            allowDataOverflow
            tickFormatter={(d: string) => {
              const date = new Date(d)
              return `${date.getMonth() + 1}/${date.getDate()}`
            }}
          />
          <YAxis tick={{ fontSize: 11 }} />
          <Tooltip
            contentStyle={{ fontSize: 12, borderRadius: 8, border: '1px solid #e5e7eb' }}
            labelFormatter={(label) => new Date(String(label)).toLocaleDateString()}
          />
          <Legend wrapperStyle={{ fontSize: 12 }} />

          <ReferenceLine
            y={stats.total_images}
            stroke="#e64980"
            strokeDasharray="6 3"
            strokeWidth={1.5}
            label={{
              value: `Target: ${stats.total_images}`,
              position: 'right',
              fontSize: 11,
              fill: '#e64980',
            }}
          />

          {sortedLabels.map((label) => (
            <Bar
              key={label}
              dataKey={label}
              stackId="labels"
              fill={colorMap[label]}
              name={label}
            />
          ))}

          <Line
            dataKey="regressionY"
            stroke="#868e96"
            strokeDasharray="4 2"
            strokeWidth={2}
            dot={false}
            name="Trend"
            connectNulls
          />

          {zoomedData.length > 10 && (
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

          {refAreaLeft && refAreaRight && (
            <ReferenceArea
              x1={refAreaLeft}
              x2={refAreaRight}
              strokeOpacity={0.3}
              fill="#4c6ef5"
              fillOpacity={0.15}
            />
          )}
        </ComposedChart>
      </ResponsiveContainer>
      {completionPoint && (
        <p className="text-xs text-gray-500 mt-2 text-center">
          Estimated completion:{' '}
          <span className="font-medium">
            {new Date(completionPoint.date).toLocaleDateString()}
          </span>
        </p>
      )}
    </ChartContainer>
  )
}
