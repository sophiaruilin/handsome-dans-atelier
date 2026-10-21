const EVENT = 'cc:toast'

export function toast(text: string) {
  window.dispatchEvent(new CustomEvent<string>(EVENT, { detail: text }))
}

export function onToast(handler: (text: string) => void): () => void {
  const listener = (e: Event) => handler((e as CustomEvent<string>).detail)
  window.addEventListener(EVENT, listener)
  return () => window.removeEventListener(EVENT, listener)
}
