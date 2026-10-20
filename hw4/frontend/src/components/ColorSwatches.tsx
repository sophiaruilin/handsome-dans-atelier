// Map catalogue color names ("heather gray", "navy blue", ...) to a CSS color for the swatch dot.
const KEYWORDS: [string, string][] = [
  ['navy', '#14284b'],
  ['royal', '#2b5dc4'],
  ['yale blue', '#00356b'],
  ['light blue', '#9cc3e6'],
  ['blue', '#2a5ca8'],
  ['charcoal', '#3d3f43'],
  ['dark heather', '#55585e'],
  ['heather', '#a7a9ad'],
  ['gray', '#9b9da1'],
  ['grey', '#9b9da1'],
  ['black', '#111'],
  ['white', '#fff'],
  ['cream', '#f3ead3'],
  ['oatmeal', '#e3d7bf'],
  ['red', '#c8102e'],
  ['maroon', '#6d1a2b'],
  ['green', '#2f6b3a'],
  ['gold', '#c9a227'],
  ['yellow', '#f2c94c'],
  ['pink', '#f2a7c3'],
  ['purple', '#5b3a8c'],
  ['orange', '#e57a2e'],
  ['brown', '#6b4a2f'],
  ['tan', '#c9a97f'],
]

function swatchColor(name: string): string {
  const lower = name.toLowerCase()
  return KEYWORDS.find(([k]) => lower.includes(k))?.[1] ?? '#ccc'
}

export default function ColorSwatches({ colors, showNames = false }: { colors: string[]; showNames?: boolean }) {
  return (
    <ul className="swatches" aria-label="Colors">
      {colors.map((c) => (
        <li key={c} title={c}>
          <span className="swatch" style={{ background: swatchColor(c) }} />
          {showNames && <span className="swatch-name">{c}</span>}
        </li>
      ))}
    </ul>
  )
}
