export interface RegressionResult {
  slope: number
  intercept: number
  r2: number
}

export function linearRegression(
  points: { x: number; y: number }[],
): RegressionResult {
  const n = points.length
  if (n < 2) return { slope: 0, intercept: 0, r2: 0 }

  let sumX = 0, sumY = 0, sumXY = 0, sumX2 = 0, sumY2 = 0
  for (const p of points) {
    sumX += p.x
    sumY += p.y
    sumXY += p.x * p.y
    sumX2 += p.x * p.x
    sumY2 += p.y * p.y
  }

  const denom = n * sumX2 - sumX * sumX
  if (denom === 0) return { slope: 0, intercept: sumY / n, r2: 0 }

  const slope = (n * sumXY - sumX * sumY) / denom
  const intercept = (sumY - slope * sumX) / n

  const ssTot = sumY2 - (sumY * sumY) / n
  const ssRes = points.reduce((acc, p) => {
    const predicted = slope * p.x + intercept
    return acc + (p.y - predicted) ** 2
  }, 0)
  const r2 = ssTot === 0 ? 1 : 1 - ssRes / ssTot

  return { slope, intercept, r2 }
}

export function estimateCompletionDate(
  slope: number,
  intercept: number,
  totalImages: number,
  startDate: Date,
): Date | null {
  if (slope <= 0) return null
  const daysNeeded = (totalImages - intercept) / slope
  const result = new Date(startDate)
  result.setDate(result.getDate() + Math.ceil(daysNeeded))
  return result
}

export interface CumulativeDataPoint {
  date: string
  cumulative: number
  regressionY: number | null
  [label: string]: string | number | null
}

export function buildDailyChartData(
  _dailyTotals: { date: string; labelers: { count: number }[] }[],
  dailyActivity: {
    labeler_id: string
    username: string
    daily: { date: string; counts: Record<string, number> }[]
  }[],
  labels: string[],
  totalImages: number,
): CumulativeDataPoint[] {
  // Aggregate daily counts per label across all labelers
  const dateMap = new Map<string, Record<string, number>>()

  for (const labeler of dailyActivity) {
    for (const day of labeler.daily) {
      const existing = dateMap.get(day.date) || {}
      for (const [label, count] of Object.entries(day.counts)) {
        existing[label] = (existing[label] || 0) + count
      }
      dateMap.set(day.date, existing)
    }
  }

  const sortedDates = [...dateMap.keys()].sort()
  if (sortedDates.length === 0) return []

  // Build cumulative data
  let cumulative = 0
  const points: { x: number; y: number }[] = []
  const data: CumulativeDataPoint[] = []

  sortedDates.forEach((date, index) => {
    const counts = dateMap.get(date)!
    const dayTotal = Object.values(counts).reduce((a, b) => a + b, 0)
    cumulative += dayTotal

    points.push({ x: index, y: cumulative })

    const point: CumulativeDataPoint = {
      date,
      cumulative,
      regressionY: null,
    }

    for (const label of labels) {
      point[label] = counts[label] || 0
    }

    data.push(point)
  })

  // Compute regression
  const reg = linearRegression(points)
  for (let i = 0; i < data.length; i++) {
    data[i].regressionY = Math.max(0, reg.slope * i + reg.intercept)
  }

  // Project into the future if slope > 0
  if (reg.slope > 0 && cumulative < totalImages) {
    const startDate = new Date(sortedDates[0])
    const completionDate = estimateCompletionDate(
      reg.slope,
      reg.intercept,
      totalImages,
      startDate,
    )
    if (completionDate) {
      const lastDate = new Date(sortedDates[sortedDates.length - 1])
      const daysToAdd = Math.min(
        Math.ceil((completionDate.getTime() - lastDate.getTime()) / 86400000),
        90,
      )
      for (let d = 1; d <= daysToAdd; d++) {
        const futureDate = new Date(lastDate)
        futureDate.setDate(futureDate.getDate() + d)
        const dateStr = futureDate.toISOString().split('T')[0]
        const idx = points.length - 1 + d
        const point: CumulativeDataPoint = {
          date: dateStr,
          cumulative: 0,
          regressionY: Math.min(totalImages, reg.slope * idx + reg.intercept),
        }
        for (const label of labels) {
          point[label] = 0
        }
        data.push(point)
      }
    }
  }

  return data
}
