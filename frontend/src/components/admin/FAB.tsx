import { motion } from 'framer-motion'

interface Props {
  onClick: () => void
}

export function FAB({ onClick }: Props) {
  return (
    <motion.button
      onClick={onClick}
      className="fixed bottom-6 right-6 w-14 h-14 bg-primary-600 text-white rounded-full shadow-lg flex items-center justify-center cursor-pointer hover:bg-primary-700 transition-colors z-50"
      whileHover={{ scale: 1.1 }}
      whileTap={{ scale: 0.95 }}
    >
      <svg
        className="w-7 h-7"
        fill="none"
        viewBox="0 0 24 24"
        stroke="currentColor"
        strokeWidth={2.5}
      >
        <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
      </svg>
    </motion.button>
  )
}
