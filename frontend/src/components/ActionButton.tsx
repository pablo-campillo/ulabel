interface ActionButtonProps {
  label: string
  shortcutHint: string
  variant?: 'primary' | 'secondary'
  onClick: () => void
}

export function ActionButton({
  label,
  shortcutHint,
  variant = 'primary',
  onClick,
}: ActionButtonProps) {
  const base =
    'inline-flex items-center gap-2 px-6 py-3 rounded-xl font-semibold text-base transition-all cursor-pointer active:scale-[0.97]'
  const variants = {
    primary:
      'bg-primary-600 text-white hover:bg-primary-700 shadow-md hover:shadow-lg',
    secondary:
      'bg-gray-100 text-gray-700 hover:bg-gray-200 border border-gray-300',
  }

  return (
    <button onClick={onClick} className={`${base} ${variants[variant]}`}>
      {label}
      <kbd
        className={`text-xs px-2 py-0.5 rounded ${
          variant === 'primary'
            ? 'bg-primary-500 text-primary-100'
            : 'bg-gray-200 text-gray-500'
        }`}
      >
        {shortcutHint}
      </kbd>
    </button>
  )
}
