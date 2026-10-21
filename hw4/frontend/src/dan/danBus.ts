// Handsome Dan's moods. Any component can make him jump (item added to the bag) or cartwheel
// across the screen with a biscuit (reservation placed); the mascots listen and animate.
export type DanMove = 'jump' | 'cartwheel'
const EVENT = 'cc:dan'

export function danDo(move: DanMove) {
  window.dispatchEvent(new CustomEvent<DanMove>(EVENT, { detail: move }))
}

export function onDan(handler: (move: DanMove) => void): () => void {
  const listener = (e: Event) => handler((e as CustomEvent<DanMove>).detail)
  window.addEventListener(EVENT, listener)
  return () => window.removeEventListener(EVENT, listener)
}
