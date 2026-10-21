// Lets any page open the chat with a question ready to send (e.g. "Ask about this item").
const EVENT = 'cc:ask-chat'

export function askChat(question: string) {
  window.dispatchEvent(new CustomEvent<string>(EVENT, { detail: question }))
}

export function onAskChat(handler: (question: string) => void): () => void {
  const listener = (e: Event) => handler((e as CustomEvent<string>).detail)
  window.addEventListener(EVENT, listener)
  return () => window.removeEventListener(EVENT, listener)
}
