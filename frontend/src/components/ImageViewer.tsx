import { useState } from 'react'

interface ImageViewerProps {
  url: string
}

export function ImageViewer({ url }: ImageViewerProps) {
  const [loading, setLoading] = useState(true)

  return (
    <div className="flex-1 flex items-center justify-center bg-gray-50 rounded-xl border border-gray-200 overflow-hidden min-h-[400px] relative">
      {loading && (
        <div className="absolute inset-0 flex items-center justify-center">
          <div className="w-10 h-10 border-4 border-primary-200 border-t-primary-600 rounded-full animate-spin" />
        </div>
      )}
      <img
        src={url}
        alt="Image to label"
        className={`max-w-full max-h-[70vh] object-contain transition-opacity ${loading ? 'opacity-0' : 'opacity-100'}`}
        onLoad={() => setLoading(false)}
      />
    </div>
  )
}
