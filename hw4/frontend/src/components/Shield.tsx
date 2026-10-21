// Small heraldic shields for the Affiliation filter. Simplified, original designs: colours and
// divisions inspired by each college/school's arms, not reproductions of the official marks.

type Division = 'chevron' | 'pale' | 'fess' | 'bend' | 'cross' | 'saltire' | 'chief' | 'plain'

const SHIELDS: Record<string, [string, string, Division]> = {
  // residential colleges
  'Benjamin Franklin': ['#1f4e8c', '#e8c547', 'chief'],
  Berkeley: ['#d62f2f', '#ffffff', 'chevron'],
  Branford: ['#1f4e8c', '#f2d43d', 'chief'],
  Davenport: ['#ffffff', '#1a1a1a', 'chevron'],
  'Grace Hopper': ['#ffffff', '#1a1a1a', 'saltire'],
  'Jonathan Edwards': ['#ffffff', '#2e9e6b', 'bend'],
  Morse: ['#ffffff', '#c8202f', 'pale'],
  Pierson: ['#1a1a1a', '#f2d43d', 'pale'],
  Saybrook: ['#1f4e8c', '#f2d43d', 'cross'],
  'Timothy Dwight': ['#ffffff', '#d62f2f', 'chief'],
  Trumbull: ['#ffffff', '#1a1a1a', 'fess'],
  // graduate and professional schools
  'School of Architecture': ['#8a8f99', '#1f4e8c', 'chevron'],
  'School of Art': ['#1f4e8c', '#f2b632', 'pale'],
  'Divinity School': ['#c8202f', '#ffffff', 'fess'],
  'School of Engineering & Applied Science': ['#1f4e8c', '#ffffff', 'chevron'],
  'School of the Environment (Forest School)': ['#2e7d4f', '#c8202f', 'saltire'],
  'Law School': ['#e8c547', '#1a1a1a', 'fess'],
  'School of Management': ['#2e7d4f', '#ffffff', 'chevron'],
  'School of Medicine': ['#2e7d4f', '#c8202f', 'saltire'],
  'School of Music': ['#c8202f', '#1f4e8c', 'chief'],
  'School of Nursing': ['#1a1a1a', '#ffffff', 'cross'],
  'School of Public Health': ['#c8202f', '#1f4e8c', 'bend'],
}

const OUTLINE = 'M2 2H30V16C30 25 23 30 16 33C9 30 2 25 2 16Z'

export default function Shield({ name, size = 18 }: { name: string; size?: number }) {
  const [field, charge, division] = SHIELDS[name] ?? ['#00356b', '#fffdf7', 'plain']
  const id = `sh-${name.replace(/\W/g, '')}`
  const marks: Record<Division, string> = {
    chevron: 'M2 24L16 12L30 24V30L16 18L2 30Z',
    pale: 'M12 2H20V34H12Z',
    fess: 'M2 13H30V21H2Z',
    bend: 'M2 6L6 2L30 26L26 30Z',
    cross: 'M13 2H19V34H13ZM2 13H30V19H2Z',
    saltire: 'M2 6L6 2L30 26L26 30ZM26 2L30 6L6 30L2 26Z',
    chief: 'M2 2H30V11H2Z',
    plain: '',
  }
  return (
    <svg viewBox="0 0 32 35" width={size} height={(size * 35) / 32} aria-hidden="true" className="shield">
      <clipPath id={id}>
        <path d={OUTLINE} />
      </clipPath>
      <g clipPath={`url(#${id})`}>
        <rect width="32" height="35" fill={field} />
        {marks[division] && <path d={marks[division]} fill={charge} />}
      </g>
      <path d={OUTLINE} fill="none" stroke="#0b2a52" strokeWidth="1.6" />
    </svg>
  )
}
