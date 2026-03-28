import { useState, useEffect, useRef } from 'react'
import { useDebounce } from '../../hooks/useDebounce'
import { searchLabelers } from '../../api/admin'
import type { LabelerAutocompleteItem } from '../../types/api'

interface Props {
  selectedLabelers: LabelerAutocompleteItem[]
  onChange: (labelers: LabelerAutocompleteItem[]) => void
}

export function LabelerAutocomplete({ selectedLabelers, onChange }: Props) {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState<LabelerAutocompleteItem[]>([])
  const [showDropdown, setShowDropdown] = useState(false)
  const [loading, setLoading] = useState(false)
  const debouncedQuery = useDebounce(query, 300)
  const containerRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!debouncedQuery.trim()) {
      setResults([])
      return
    }

    let cancelled = false
    setLoading(true)
    searchLabelers(debouncedQuery.trim())
      .then((data) => {
        if (!cancelled) {
          setResults(data.filter((d) => !selectedLabelers.some((s) => s.id === d.id)))
          setShowDropdown(true)
        }
      })
      .catch(() => {
        if (!cancelled) setResults([])
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })

    return () => { cancelled = true }
  }, [debouncedQuery, selectedLabelers])

  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setShowDropdown(false)
      }
    }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [])

  const selectLabeler = (labeler: LabelerAutocompleteItem) => {
    onChange([...selectedLabelers, labeler])
    setQuery('')
    setShowDropdown(false)
  }

  const removeLabeler = (id: string) => {
    onChange(selectedLabelers.filter((l) => l.id !== id))
  }

  return (
    <div ref={containerRef} className="relative">
      <div className="flex flex-wrap gap-2 mb-2">
        {selectedLabelers.map((l) => (
          <span
            key={l.id}
            className="inline-flex items-center gap-1 px-2.5 py-1 bg-gray-100 text-gray-700 text-sm font-medium rounded-lg"
          >
            {l.username}
            <button
              type="button"
              onClick={() => removeLabeler(l.id)}
              className="text-gray-400 hover:text-gray-600 cursor-pointer"
            >
              <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </span>
        ))}
      </div>

      <div className="relative">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onFocus={() => results.length > 0 && setShowDropdown(true)}
          placeholder="Search labelers by username..."
          className="w-full px-3 py-2 rounded-lg border border-gray-300 focus:border-primary-500 focus:ring-2 focus:ring-primary-200 outline-none transition-all text-sm"
        />
        {loading && (
          <div className="absolute right-3 top-1/2 -translate-y-1/2">
            <div className="w-4 h-4 border-2 border-gray-300 border-t-primary-600 rounded-full animate-spin" />
          </div>
        )}
      </div>

      {showDropdown && results.length > 0 && (
        <div className="absolute z-10 mt-1 w-full bg-white border border-gray-200 rounded-lg shadow-lg max-h-48 overflow-y-auto">
          {results.map((r) => (
            <button
              key={r.id}
              type="button"
              onClick={() => selectLabeler(r)}
              className="w-full text-left px-3 py-2 text-sm hover:bg-primary-50 hover:text-primary-700 transition-colors cursor-pointer"
            >
              {r.username}
            </button>
          ))}
        </div>
      )}

      {showDropdown && !loading && debouncedQuery.trim() && results.length === 0 && (
        <div className="absolute z-10 mt-1 w-full bg-white border border-gray-200 rounded-lg shadow-lg p-3 text-sm text-gray-500">
          No labelers found
        </div>
      )}
    </div>
  )
}
