interface LabelButtonProps {
  label: string
  shortcutKey: number
  disabled: boolean
  onClick: () => void
}

export function LabelButton({
  label,
  shortcutKey,
  disabled,
  onClick,
}: LabelButtonProps) {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className={`
        w-full flex items-center gap-3 px-4 py-3 rounded-lg border text-left transition-all cursor-pointer
        ${
          disabled
            ? 'bg-gray-50 border-gray-200 text-gray-400 cursor-not-allowed'
            : 'bg-white border-gray-200 text-gray-800 hover:border-primary-400 hover:bg-primary-50 hover:shadow-sm active:scale-[0.98]'
        }
      `}
    >
      <span
        className={`
          inline-flex items-center justify-center w-8 h-8 rounded-md text-sm font-bold shrink-0
          ${
            disabled
              ? 'bg-gray-100 text-gray-400'
              : 'bg-primary-100 text-primary-700'
          }
        `}
      >
        {shortcutKey}
      </span>
      <span className="font-medium truncate">{label}</span>
    </button>
  )
}
