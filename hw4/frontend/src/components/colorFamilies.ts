// Colour families for the Products page filter, based on each product's main (first) colour.
// The rest of the colour list is lettering and graphics, so "navy" means a navy garment.

export const COLOR_FAMILIES = ['Navy', 'Heather gray', 'Charcoal', 'Cream & white', 'Coral'] as const

const SWATCHES: Record<string, string> = {
  Navy: '#14284b',
  'Heather gray': '#a7a9ad',
  Charcoal: '#3d3f43',
  'Cream & white': '#f3ead3',
  Coral: '#e98a74',
}

export const swatchFor = (family: string) => SWATCHES[family] ?? '#ccc'

export function colorFamily(colors: string[]): string | null {
  const c = colors[0]?.toLowerCase() ?? ''
  if (!c) return null
  if (c.includes('navy') || c.includes('blue')) return 'Navy'
  if (c.includes('charcoal') || c.includes('dark heather')) return 'Charcoal'
  if (c.includes('gray') || c.includes('grey')) return 'Heather gray'
  if (c.includes('cream') || c.includes('white') || c.includes('ivory') || c.includes('oatmeal')) return 'Cream & white'
  if (c.includes('coral') || c.includes('pink') || c.includes('red')) return 'Coral'
  return null
}
