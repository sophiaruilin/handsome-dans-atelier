import { SEASONS, setSeasonOverride, useSeason } from '../dan/season'

// Footer control to preview Seasonal Dan's outfits (Auto = today's season).
export default function SeasonSwitcher() {
  const { season, override } = useSeason()
  return (
    <div className="wardrobe" role="group" aria-label="Dan's wardrobe">
      <span>Dan's wardrobe:</span>
      <button className={!override ? 'active' : ''} onClick={() => setSeasonOverride(null)}>
        Today
      </button>
      {SEASONS.map((s) => (
        <button key={s.key} className={override === s.key ? 'active' : ''} onClick={() => setSeasonOverride(s.key)} aria-pressed={season === s.key}>
          {s.label}
        </button>
      ))}
    </div>
  )
}
