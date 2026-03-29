import { useEffect, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'

let audioCtx: AudioContext | null = null

function ensureAudioContext() {
  if (!audioCtx) {
    audioCtx = new AudioContext()
  }
  if (audioCtx.state === 'suspended') {
    audioCtx.resume()
  }
}

// Resume AudioContext on first user interaction so it's ready for useEffect playback
if (typeof window !== 'undefined') {
  const unlock = () => {
    ensureAudioContext()
    window.removeEventListener('click', unlock)
    window.removeEventListener('keydown', unlock)
  }
  window.addEventListener('click', unlock)
  window.addEventListener('keydown', unlock)
}

function playRankUpSound() {
  if (!audioCtx || audioCtx.state === 'suspended') return
  const osc = audioCtx.createOscillator()
  const gain = audioCtx.createGain()
  osc.connect(gain)
  gain.connect(audioCtx.destination)
  osc.type = 'sine'
  osc.frequency.setValueAtTime(440, audioCtx.currentTime)
  osc.frequency.linearRampToValueAtTime(880, audioCtx.currentTime + 0.15)
  gain.gain.setValueAtTime(0.3, audioCtx.currentTime)
  gain.gain.linearRampToValueAtTime(0, audioCtx.currentTime + 0.3)
  osc.start()
  osc.stop(audioCtx.currentTime + 0.3)
}

function playRankDownSound() {
  if (!audioCtx || audioCtx.state === 'suspended') return
  const osc = audioCtx.createOscillator()
  const gain = audioCtx.createGain()
  osc.connect(gain)
  gain.connect(audioCtx.destination)
  osc.type = 'sine'
  osc.frequency.setValueAtTime(440, audioCtx.currentTime)
  osc.frequency.linearRampToValueAtTime(220, audioCtx.currentTime + 0.2)
  gain.gain.setValueAtTime(0.3, audioCtx.currentTime)
  gain.gain.linearRampToValueAtTime(0, audioCtx.currentTime + 0.35)
  osc.start()
  osc.stop(audioCtx.currentTime + 0.35)
}

interface RankingBadgeProps {
  ranking: number
  totalLabelers: number
  previousRanking: number | null
  labelCount: number
}

export function RankingBadge({
  ranking,
  totalLabelers,
  previousRanking,
  labelCount,
}: RankingBadgeProps) {
  const improved =
    previousRanking !== null && previousRanking > 0 && ranking < previousRanking
  const dropped =
    previousRanking !== null && previousRanking > 0 && ranking > previousRanking

  const hasPlayedSound = useRef(false)

  useEffect(() => {
    if (hasPlayedSound.current) return
    if (improved) {
      playRankUpSound()
      hasPlayedSound.current = true
    } else if (dropped) {
      playRankDownSound()
      hasPlayedSound.current = true
    }
  }, [improved, dropped])

  useEffect(() => {
    hasPlayedSound.current = false
  }, [ranking])

  if (ranking === 0) {
    return (
      <div className="flex items-center gap-4">
        <div className="bg-gray-100 rounded-xl px-4 py-2 text-center">
          <div className="text-xs text-gray-500 uppercase tracking-wide font-medium">
            Labels
          </div>
          <div className="text-2xl font-bold text-gray-800">{labelCount}</div>
        </div>
        <div className="bg-gray-100 rounded-xl px-4 py-2 text-center">
          <div className="text-xs text-gray-500 uppercase tracking-wide font-medium">
            Rank
          </div>
          <div className="text-lg font-semibold text-gray-400">---</div>
        </div>
      </div>
    )
  }

  return (
    <div className="flex items-center gap-4">
      <div className="bg-primary-50 rounded-xl px-4 py-2 text-center">
        <div className="text-xs text-primary-600 uppercase tracking-wide font-medium">
          Labels
        </div>
        <AnimatePresence mode="wait">
          <motion.div
            key={labelCount}
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 10 }}
            transition={{ duration: 0.2 }}
            className="text-2xl font-bold text-primary-700"
          >
            {labelCount}
          </motion.div>
        </AnimatePresence>
      </div>

      <AnimatePresence mode="wait">
        <motion.div
          key={`${ranking}-${previousRanking}`}
          initial={
            improved
              ? { scale: 1.3, backgroundColor: '#d3f9d8' }
              : dropped
                ? { x: -5, backgroundColor: '#fff3bf' }
                : {}
          }
          animate={
            improved
              ? { scale: 1, backgroundColor: '#f0f4ff' }
              : dropped
                ? {
                    x: [0, -3, 3, -3, 3, 0],
                    backgroundColor: '#f0f4ff',
                  }
                : {}
          }
          transition={{ duration: 0.5 }}
          className="bg-primary-50 rounded-xl px-4 py-2 text-center relative"
        >
          <div className="text-xs text-primary-600 uppercase tracking-wide font-medium">
            Rank
          </div>
          <div className="flex items-center justify-center gap-1">
            <span className="text-2xl font-bold text-primary-700">
              #{ranking}
            </span>
            <span className="text-sm text-primary-400">/ {totalLabelers}</span>
          </div>

          {improved && (
            <motion.div
              initial={{ opacity: 1, y: 0 }}
              animate={{ opacity: 0, y: -20 }}
              transition={{ duration: 1, delay: 0.2 }}
              className="absolute -top-2 -right-2 text-green-500"
            >
              <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                <path
                  fillRule="evenodd"
                  d="M10 17a.75.75 0 01-.75-.75V5.612L5.29 9.77a.75.75 0 01-1.08-1.04l5.25-5.5a.75.75 0 011.08 0l5.25 5.5a.75.75 0 11-1.08 1.04l-3.96-4.158V16.25A.75.75 0 0110 17z"
                  clipRule="evenodd"
                />
              </svg>
            </motion.div>
          )}

          {dropped && (
            <motion.div
              initial={{ opacity: 1, y: 0 }}
              animate={{ opacity: 0, y: 20 }}
              transition={{ duration: 1, delay: 0.2 }}
              className="absolute -top-2 -right-2 text-amber-500"
            >
              <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                <path
                  fillRule="evenodd"
                  d="M10 3a.75.75 0 01.75.75v10.638l3.96-4.158a.75.75 0 111.08 1.04l-5.25 5.5a.75.75 0 01-1.08 0l-5.25-5.5a.75.75 0 111.08-1.04l3.96 4.158V3.75A.75.75 0 0110 3z"
                  clipRule="evenodd"
                />
              </svg>
            </motion.div>
          )}
        </motion.div>
      </AnimatePresence>
    </div>
  )
}
