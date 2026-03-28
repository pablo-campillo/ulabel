import { useState } from 'react'

interface Props {
  tags: string[]
  onChange: (tags: string[]) => void
  disabled?: boolean
}

export function TagInput({ tags, onChange, disabled }: Props) {
  const [input, setInput] = useState('')

  const addTag = (value: string) => {
    const trimmed = value.trim().toLowerCase()
    if (trimmed && !tags.includes(trimmed)) {
      onChange([...tags, trimmed])
    }
    setInput('')
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' || e.key === ',') {
      e.preventDefault()
      addTag(input)
    } else if (e.key === 'Backspace' && !input && tags.length > 0) {
      onChange(tags.slice(0, -1))
    }
  }

  return (
    <div>
      <div className="flex flex-wrap gap-2 mb-2">
        {tags.map((tag) => (
          <span
            key={tag}
            className="inline-flex items-center gap-1 px-2.5 py-1 bg-primary-50 text-primary-700 text-sm font-medium rounded-lg"
          >
            {tag}
            {!disabled && (
              <button
                type="button"
                onClick={() => onChange(tags.filter((t) => t !== tag))}
                className="text-primary-400 hover:text-primary-600 cursor-pointer"
              >
                <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            )}
          </span>
        ))}
      </div>
      {!disabled && (
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          onBlur={() => input && addTag(input)}
          placeholder="Type a label and press Enter"
          className="w-full px-3 py-2 rounded-lg border border-gray-300 focus:border-primary-500 focus:ring-2 focus:ring-primary-200 outline-none transition-all text-sm"
        />
      )}
    </div>
  )
}
