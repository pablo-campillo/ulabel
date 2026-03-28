import { useRef, useCallback } from 'react'
import { toPng } from 'html-to-image'

interface Props {
  title: string
  children: React.ReactNode
}

export function ChartContainer({ title, children }: Props) {
  const ref = useRef<HTMLDivElement>(null)

  const handleDownload = useCallback(async () => {
    if (!ref.current) return
    try {
      const dataUrl = await toPng(ref.current, { backgroundColor: '#ffffff' })
      const link = document.createElement('a')
      link.download = `${title.toLowerCase().replace(/\s+/g, '-')}.png`
      link.href = dataUrl
      link.click()
    } catch {
      // silently fail
    }
  }, [title])

  return (
    <div ref={ref} className="bg-white rounded-xl border border-gray-200 p-5">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-semibold text-gray-700">{title}</h3>
        <button
          onClick={handleDownload}
          className="p-1.5 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors cursor-pointer"
          title="Download as image"
        >
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5M16.5 12L12 16.5m0 0L7.5 12m4.5 4.5V3" />
          </svg>
        </button>
      </div>
      <div className="h-80">{children}</div>
    </div>
  )
}
