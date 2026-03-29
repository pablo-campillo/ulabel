import type { ProjectStats } from '../types/api'

export function deriveLabelerStats(
  stats: ProjectStats,
  labelerId: string,
): { count: number; ranking: number; totalLabelers: number } {
  const totals = stats.labeler_class_counts.map((lc) => ({
    labeler_id: lc.labeler_id,
    total: Object.values(lc.counts).reduce((a, b) => a + b, 0),
  }))

  totals.sort((a, b) => b.total - a.total)

  const myEntry = totals.find((t) => t.labeler_id === labelerId)
  const myTotal = myEntry?.total ?? 0
  const rankingIndex = totals.findIndex((t) => t.labeler_id === labelerId)

  return {
    count: myTotal,
    ranking: rankingIndex >= 0 ? rankingIndex + 1 : 0,
    totalLabelers: totals.length,
  }
}
