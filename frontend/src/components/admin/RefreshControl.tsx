import { useState, useEffect, useRef, useCallback } from 'react'

const INTERVAL_OPTIONS = [
  { label: 'Off', value: 0 },
  { label: '5s', value: 5_000 },
  { label: '10s', value: 10_000 },
  { label: '30s', value: 30_000 },
  { label: '1m', value: 60_000 },
  { label: '5m', value: 300_000 },
]

interface RefreshControlProps {
  onRefresh: () => void
  refreshing?: boolean
}

export function RefreshControl({ onRefresh, refreshing }: RefreshControlProps) {
  const [interval, setInterval_] = useState(0)
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date())
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null)

  const doRefresh = useCallback(() => {
    onRefresh()
    setLastUpdate(new Date())
  }, [onRefresh])

  useEffect(() => {
    if (timerRef.current) {
      clearInterval(timerRef.current)
      timerRef.current = null
    }
    if (interval > 0) {
      timerRef.current = setInterval(doRefresh, interval)
    }
    return () => {
      if (timerRef.current) {
        clearInterval(timerRef.current)
      }
    }
  }, [interval, doRefresh])

  const handleManualRefresh = () => {
    doRefresh()
  }

  const formatTime = (date: Date) =>
    date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })

  const activeOption = INTERVAL_OPTIONS.find((o) => o.value === interval)

  return (
    <div className="flex items-center gap-3">
      <span className="text-xs text-gray-400">
        Last update: {formatTime(lastUpdate)}
      </span>

      <button
        onClick={handleManualRefresh}
        disabled={refreshing}
        className="p-1.5 text-gray-500 hover:text-primary-600 hover:bg-primary-50 rounded-lg transition-colors cursor-pointer disabled:opacity-50"
        title="Refresh now"
      >
        <svg
          className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`}
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          strokeWidth={2}
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.992 0l3.181 3.183a8.25 8.25 0 0013.803-3.7M4.031 9.865a8.25 8.25 0 0113.803-3.7l3.181 3.182M20.016 4.356v4.992"
          />
        </svg>
      </button>

      <div className="relative">
        <select
          value={interval}
          onChange={(e) => setInterval_(Number(e.target.value))}
          className="appearance-none pl-2.5 pr-7 py-1 text-xs font-medium text-gray-600 bg-white border border-gray-200 rounded-lg hover:border-gray-300 focus:outline-none focus:ring-1 focus:ring-primary-500 focus:border-primary-500 cursor-pointer"
        >
          {INTERVAL_OPTIONS.map((opt) => (
            <option key={opt.value} value={opt.value}>
              {opt.value === 0 ? 'Off' : opt.label}
            </option>
          ))}
        </select>
        <svg
          className="absolute right-1.5 top-1/2 -translate-y-1/2 w-3 h-3 text-gray-400 pointer-events-none"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          strokeWidth={2}
        >
          <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 8.25l-7.5 7.5-7.5-7.5" />
        </svg>
      </div>

      {activeOption && activeOption.value > 0 && (
        <span className="text-xs text-primary-600 font-medium">
          Auto: {activeOption.label}
        </span>
      )}
    </div>
  )
}
