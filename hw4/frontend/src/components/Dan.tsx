import { useId } from 'react'
import { useSeason, type Season } from '../dan/season'

const INK = '#0b2a52'
const NAVY = '#00356b'
const CREAM = '#fffdf7'
const BRASS = '#b08d57'
const POWDER = '#dbe5f1'

interface Props {
  size?: number
  bone?: boolean // a dog biscuit in his mouth (checkout cartwheel)
  className?: string
  title?: string
  season?: Season // defaults to today's season (or the footer preview)
}

// Handsome Dan, the Campus Customs mascot: a Victorian cartoon bulldog in a top hat, monocle,
// polka-dot bow tie and Yale sweater. Original drawing, engraved-ink outlines like the wallpaper.
export default function Dan({
  size = 120,
  bone = false,
  className,
  title = 'Handsome Dan, the Campus Customs bulldog',
  season: seasonProp,
}: Props) {
  const id = useId().replace(/:/g, '')
  const today = useSeason().season
  const season = seasonProp ?? today
  const scarf = season === 'fall' || season === 'winter' || season === 'game'
  const boater = season === 'spring' || season === 'summer'
  return (
    <svg
      className={className}
      viewBox="0 0 220 240"
      width={size}
      height={(size * 240) / 220}
      role="img"
      aria-label={title}
    >
      <defs>
        <pattern id={`h${id}`} width="4" height="4" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
          <line x1="0" y1="0" x2="0" y2="4" stroke={INK} strokeWidth="0.8" strokeOpacity="0.35" />
        </pattern>
        <pattern id={`dots${id}`} width="6" height="6" patternUnits="userSpaceOnUse">
          <rect width="6" height="6" fill="#286dc0" />
          <circle cx="3" cy="3" r="1.1" fill={CREAM} />
        </pattern>
        <pattern id={`stripes${id}`} width="12" height="12" patternUnits="userSpaceOnUse" patternTransform="rotate(70)">
          <rect width="12" height="12" fill={NAVY} />
          <rect width="5" height="12" fill={CREAM} />
        </pattern>
        <clipPath id={`head${id}`}>
          <path d="M110 56C158 56 182 80 182 108C182 136 162 154 136 158H84C58 154 38 136 38 108C38 80 62 56 110 56Z" />
        </clipPath>
      </defs>

      <g stroke={INK} strokeWidth="2.2" strokeLinejoin="round" strokeLinecap="round">
        {/* hind feet poking out to the sides */}
        <ellipse cx="44" cy="222" rx="18" ry="10" fill={CREAM} />
        <ellipse cx="176" cy="222" rx="18" ry="10" fill={CREAM} />
        <g fill={POWDER} strokeWidth="1.2">
          <circle cx="38" cy="222" r="4" />
          <circle cx="182" cy="222" r="4" />
        </g>

        {/* Yale sweater */}
        <path d="M60 152C46 172 42 198 50 224H170C178 198 174 172 160 152Z" fill={NAVY} />
        <path d="M72 162C66 182 66 204 70 222M148 162C154 182 154 204 150 222" stroke="#2a5591" strokeWidth="1.4" fill="none" />
        <path d="M56 214H164" stroke={CREAM} strokeOpacity="0.5" strokeWidth="1.2" />
        <path d="M58 219H162" stroke={CREAM} strokeOpacity="0.5" strokeWidth="1.2" />
        <text x="110" y="208" textAnchor="middle" fontFamily="'Playfair Display', Georgia, serif" fontWeight="900" fontSize="46" fill={CREAM} stroke="none">
          Y
        </text>

        {/* front paws */}
        <ellipse cx="88" cy="226" rx="15" ry="9" fill={CREAM} />
        <ellipse cx="132" cy="226" rx="15" ry="9" fill={CREAM} />
        <path d="M83 222V230M93 222V230M127 222V230M137 222V230" strokeWidth="1.2" />

        {/* rose ears */}
        <path d="M62 72Q42 74 34 60Q46 48 70 62Z" fill={POWDER} />
        <path d="M158 72Q178 74 186 60Q174 48 150 62Z" fill={POWDER} />

        {/* head */}
        <path d="M110 56C158 56 182 80 182 108C182 136 162 154 136 158H84C58 154 38 136 38 108C38 80 62 56 110 56Z" fill={CREAM} />
        <path d="M60 126Q56 146 78 156M160 126Q164 146 142 156" strokeWidth="1.5" fill="none" />
        <path d="M104 86Q110 82 116 86" strokeWidth="1.3" fill="none" />
        <path d="M84 72Q110 64 136 72M90 79Q110 73 130 79" strokeWidth="1.4" fill="none" />

        {/* cheeks */}
        <circle cx="64" cy="118" r="10" fill="#f4b9c4" fillOpacity="0.6" stroke="none" />
        <circle cx="156" cy="118" r="10" fill="#f4b9c4" fillOpacity="0.6" stroke="none" />

        {/* brows and eyes */}
        <path d="M76 84Q88 77 99 84M121 84Q132 77 144 84" strokeWidth="1.8" fill="none" />
        <circle cx="88" cy="95" r="6.5" fill={INK} />
        <circle cx="132" cy="95" r="6.5" fill={INK} />
        <circle cx="90.5" cy="92.5" r="2" fill={CREAM} stroke="none" />
        <circle cx="134.5" cy="92.5" r="2" fill={CREAM} stroke="none" />

        {/* monocle on a brass chain */}
        {season !== 'summer' && (
          <>
            <circle cx="132" cy="95" r="13" fill={CREAM} fillOpacity="0.25" stroke={BRASS} strokeWidth="2.6" />
            <path d="M144 101Q160 124 150 152" stroke={BRASS} strokeWidth="1.2" strokeDasharray="2 2.5" fill="none" />
          </>
        )}

        {/* muzzle, nose and that famous underbite */}
        <path d="M80 116C80 102 95 100 110 102C125 100 140 102 140 116C140 134 126 142 110 142C94 142 80 134 80 116Z" fill={CREAM} />
        <path d="M95 104Q110 95 125 104Q125 114 110 116Q95 114 95 104Z" fill={INK} />
        <ellipse cx="105" cy="103" rx="2.5" ry="1.4" fill={CREAM} stroke="none" opacity="0.7" />
        <path d="M110 115V122M88 125Q99 133 110 123Q121 133 132 125" strokeWidth="1.8" fill="none" />
        {!bone && <path d="M103 131Q110 140 117 131Z" fill="#e88a9a" strokeWidth="1.4" />}
        <path d="M97 129L100 121L103 129Z M117 129L120 121L123 129Z" fill={CREAM} strokeWidth="1.3" />

        {/* polka-dot bow tie */}
        <path d="M110 157L86 146V168Z" fill={`url(#dots${id})`} />
        <path d="M110 157L134 146V168Z" fill={`url(#dots${id})`} />
        <rect x="104" y="151" width="12" height="12" rx="3" fill="#286dc0" />

        {/* dog biscuit */}
        {bone && (
          <g fill="#f3e2c3" strokeWidth="1.8">
            <rect x="72" y="121" width="76" height="11" rx="5.5" />
            <circle cx="72" cy="120" r="7" />
            <circle cx="72" cy="133" r="7" />
            <circle cx="148" cy="120" r="7" />
            <circle cx="148" cy="133" r="7" />
            <rect x="73" y="122" width="74" height="9" stroke="none" />
          </g>
        )}

        {/* Seasonal Dan: striped Yale scarf (fall, winter, The Game) */}
        {scarf && (
          <g>
            <path d="M64 146Q110 170 156 146L158 160Q110 186 62 160Z" fill={`url(#stripes${id})`} />
            <path d="M74 158L64 204L82 207L90 162Z" fill={`url(#stripes${id})`} />
            <path d="M66 205L64 213M71 206L70 214M76 206L76 214M81 207L82 215" strokeWidth="1.4" />
          </g>
        )}

        {/* Spring: a daisy boutonniere */}
        {season === 'spring' && (
          <g transform="translate(80 178)" strokeWidth="1.2">
            {[0, 60, 120, 180, 240, 300].map((a) => (
              <ellipse key={a} cx="0" cy="-7" rx="3.6" ry="6.5" fill={CREAM} transform={`rotate(${a})`} />
            ))}
            <circle r="3.6" fill={BRASS} />
          </g>
        )}

        {/* Summer: round navy sunglasses */}
        {season === 'summer' && (
          <g strokeWidth="2">
            <circle cx="88" cy="95" r="11" fill={NAVY} />
            <circle cx="132" cy="95" r="11" fill={NAVY} />
            <path d="M99 94Q110 89 121 94M77 92L58 86M143 92L162 86" fill="none" />
            <path d="M82 90Q86 87 90 88M126 90Q130 87 134 88" stroke={CREAM} strokeWidth="1.6" fill="none" />
          </g>
        )}

        {/* The Game: a BEAT HARVARD pennant */}
        {season === 'game' && (
          <g>
            <path d="M184 228L200 112" strokeWidth="3" />
            <path d="M199 114L146 128L196 144Z" fill={NAVY} />
            <text x="183" y="132" textAnchor="middle" transform="rotate(10 183 132)" fontFamily="'Playfair Display', Georgia, serif" fontWeight="900" fontSize="9" fill={CREAM} stroke="none">
              BEAT
            </text>
            <text x="181" y="141" textAnchor="middle" transform="rotate(10 181 141)" fontFamily="'Playfair Display', Georgia, serif" fontWeight="900" fontSize="7" fill={CREAM} stroke="none">
              HARVARD
            </text>
            <ellipse cx="184" cy="226" rx="10" ry="8" fill={CREAM} />
          </g>
        )}

        {/* Hat: a Victorian top hat at a jaunty angle, or a straw boater in spring and summer */}
        {boater ? (
          <g transform="rotate(-8 110 54)">
            <ellipse cx="110" cy="54" rx="54" ry="10" fill="#ecd9a8" />
            <path d="M80 54V32Q110 26 140 32V54Z" fill="#ecd9a8" />
            <ellipse cx="110" cy="32" rx="30" ry="5" fill="#f3e6c2" />
            <path d="M80 42Q110 37 140 42V51Q110 46 80 51Z" fill={NAVY} />
            <path d="M64 57Q110 66 156 57M70 51Q110 59 150 51" stroke={BRASS} strokeWidth="1" fill="none" />
          </g>
        ) : (
          <g transform="rotate(-10 110 54)">
            <path d="M80 54L84 12Q110 5 136 12L140 54Z" fill={NAVY} />
            <path d="M81 45H139L140 54H80Z" fill={BRASS} />
            <path d="M91 16L88 42" stroke="#4a77b8" strokeWidth="2" fill="none" />
            <ellipse cx="110" cy="56" rx="45" ry="8" fill={NAVY} />
            {season === 'winter' && <path d="M83 14Q96 2 110 8Q124 2 137 13Q132 21 110 17Q90 22 83 14Z" fill={CREAM} />}
          </g>
        )}

        {/* Fall: a brass elm leaf drifting past */}
        {season === 'fall' && (
          <g strokeWidth="1.3">
            <path d="M188 30Q204 34 200 50Q186 48 188 30Z" fill={BRASS} />
            <path d="M188 30L199 49" fill="none" />
            <path d="M22 118Q30 104 42 112Q34 126 22 118Z" fill={BRASS} />
          </g>
        )}

        {/* Winter: snowflakes */}
        {season === 'winter' && (
          <g strokeWidth="1.4">
            {[
              [24, 44],
              [196, 96],
              [20, 168],
              [200, 40],
            ].map(([x, y]) => (
              <path key={`${x}-${y}`} d={`M${x} ${y - 6}V${y + 6}M${x - 6} ${y}H${x + 6}M${x - 4} ${y - 4}L${x + 4} ${y + 4}M${x - 4} ${y + 4}L${x + 4} ${y - 4}`} />
            ))}
          </g>
        )}
      </g>
    </svg>
  )
}
