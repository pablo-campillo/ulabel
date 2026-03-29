import { LabelButton } from './LabelButton'

interface LabelSidebarProps {
  labels: string[]
  disabled: boolean
  onSelect: (label: string) => void
}

export function LabelSidebar({ labels, disabled, onSelect }: LabelSidebarProps) {
  const sortedLabels = [...labels].sort()

  return (
    <div className="w-64 shrink-0 flex flex-col gap-2">
      <h3 className="text-xs uppercase tracking-wide font-semibold text-gray-500 mb-1 px-1">
        Labels
      </h3>
      {sortedLabels.map((label, index) => (
        <LabelButton
          key={label}
          label={label}
          shortcutKey={index + 1}
          disabled={disabled}
          onClick={() => onSelect(label)}
        />
      ))}
    </div>
  )
}
