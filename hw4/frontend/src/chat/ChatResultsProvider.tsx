import { useState, type ReactNode } from 'react'
import type { PageResults } from '../types'
import { ChatResultsContext } from './context'

// Holds the latest search the chat sent to the page. It lives above the routes, so the results
// are still there after a shopper opens a product and comes back.
export default function ChatResultsProvider({ children }: { children: ReactNode }) {
  const [results, setResults] = useState<PageResults | null>(null)
  const [version, setVersion] = useState(0)

  const value = {
    results,
    version,
    show: (r: PageResults) => {
      setResults(r)
      setVersion((v) => v + 1)
    },
    clear: () => setResults(null),
  }
  return <ChatResultsContext.Provider value={value}>{children}</ChatResultsContext.Provider>
}
