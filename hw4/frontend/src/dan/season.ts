import { useEffect, useState } from 'react'

// Seasonal Handsome Dan: his outfit follows the calendar. "game" is the week of The Game
// (Yale vs Harvard), traditionally played the Saturday before Thanksgiving.
export type Season = 'fall' | 'winter' | 'spring' | 'summer' | 'game'

export const SEASONS: { key: Season; label: string; caption: string }[] = [
  { key: 'fall', label: 'Fall', caption: 'Scarf season on Old Campus.' },
  { key: 'winter', label: 'Winter', caption: 'Bundled up for the walk to Sterling.' },
  { key: 'spring', label: 'Spring', caption: 'Boater weather on Cross Campus.' },
  { key: 'summer', label: 'Summer', caption: 'Summer session, still handsome.' },
  { key: 'game', label: 'Game week', caption: "It's The Game week. Beat Harvard!" },
]

/** The Saturday before Thanksgiving (the fourth Thursday of November). */
export function theGameDate(year: number): Date {
  const nov1 = new Date(year, 10, 1)
  const firstThursday = 1 + ((4 - nov1.getDay() + 7) % 7)
  return new Date(year, 10, firstThursday + 21 - 5)
}

export function seasonFor(date: Date): Season {
  const game = theGameDate(date.getFullYear())
  const weekBefore = new Date(game)
  weekBefore.setDate(game.getDate() - 6)
  const day = new Date(date.getFullYear(), date.getMonth(), date.getDate())
  if (day >= weekBefore && day <= game) return 'game'
  const m = date.getMonth() // 0 = January
  if (m >= 8 && m <= 10) return 'fall'
  if (m === 11 || m <= 1) return 'winter'
  if (m <= 4) return 'spring'
  return 'summer'
}

const KEY = 'campus-customs-season'
const EVENT = 'cc:season'

function current(): { season: Season; override: Season | null } {
  const saved = sessionStorage.getItem(KEY) as Season | null
  const override = SEASONS.some((s) => s.key === saved) ? saved : null
  return { season: override ?? seasonFor(new Date()), override }
}

/** Preview another season (null = back to today's). Lasts for this browser tab. */
export function setSeasonOverride(season: Season | null) {
  if (season) sessionStorage.setItem(KEY, season)
  else sessionStorage.removeItem(KEY)
  window.dispatchEvent(new Event(EVENT))
}

export function useSeason() {
  const [state, setState] = useState(current)
  useEffect(() => {
    const update = () => setState(current())
    window.addEventListener(EVENT, update)
    return () => window.removeEventListener(EVENT, update)
  }, [])
  return state
}
