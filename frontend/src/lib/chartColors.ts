const BASE_COLORS = [
  '#4c6ef5', // primary
  '#40c057', // green
  '#fd7e14', // orange
  '#e64980', // pink
  '#7950f2', // violet
  '#15aabf', // cyan
  '#fab005', // yellow
  '#be4bdb', // grape
  '#12b886', // teal
  '#fa5252', // red
  '#228be6', // blue
  '#82c91e', // lime
]

export function getChartColors(count: number): string[] {
  if (count <= BASE_COLORS.length) {
    return BASE_COLORS.slice(0, count)
  }

  const colors = [...BASE_COLORS]
  for (let i = BASE_COLORS.length; i < count; i++) {
    const hue = (i * 137.5) % 360
    colors.push(`hsl(${hue}, 65%, 55%)`)
  }
  return colors
}

export function getLabelColorMap(labels: string[]): Record<string, string> {
  const sorted = [...labels].sort()
  const colors = getChartColors(sorted.length)
  const map: Record<string, string> = {}
  sorted.forEach((label, i) => {
    map[label] = colors[i]
  })
  return map
}
