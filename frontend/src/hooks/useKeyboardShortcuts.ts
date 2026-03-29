import { useEffect } from 'react'

export function useKeyboardShortcuts(
  shortcuts: Record<string, () => void>,
  enabled: boolean,
) {
  useEffect(() => {
    if (!enabled) return

    const handler = (e: KeyboardEvent) => {
      if (
        e.target instanceof HTMLInputElement ||
        e.target instanceof HTMLTextAreaElement
      )
        return

      const action = shortcuts[e.key]
      if (action) {
        e.preventDefault()
        action()
      }
    }

    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [shortcuts, enabled])
}
