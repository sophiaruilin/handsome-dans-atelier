import { createContext, useContext } from 'react'
import type { PageResults } from '../types'

export interface ChatResultsState {
  results: PageResults | null
  // Bumps on every new search, so the page can replay its entrance animation.
  version: number
  show: (results: PageResults) => void
  clear: () => void
}

export const ChatResultsContext = createContext<ChatResultsState | null>(null)

export function useChatResults(): ChatResultsState {
  const ctx = useContext(ChatResultsContext)
  if (!ctx) throw new Error('useChatResults must be used inside <ChatResultsProvider>')
  return ctx
}
