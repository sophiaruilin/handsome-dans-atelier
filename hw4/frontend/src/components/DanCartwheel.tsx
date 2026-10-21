import { useEffect, useState } from 'react'
import { onDan } from '../dan/danBus'
import Dan from './Dan'

const CONFETTI = ['#00356b', '#fffdf7', '#286dc0', '#9fb6d3', '#00244a', '#dfe7f0']

// When a reservation is placed, Handsome Dan cartwheels across the screen with a biscuit.
export default function DanCartwheel() {
  const [run, setRun] = useState(0)

  useEffect(
    () =>
      onDan((move) => {
        if (move === 'cartwheel') setRun((r) => r + 1)
      }),
    [],
  )
  useEffect(() => {
    if (!run) return
    const t = window.setTimeout(() => setRun(0), 3600)
    return () => window.clearTimeout(t)
  }, [run])

  if (!run) return null
  return (
    <div className="cartwheel-stage" key={run} aria-live="polite">
      <p className="cartwheel-banner">Boola Boola! Your order is reserved!</p>
      <div className="cartwheel-track">
        <div className="cartwheel-dan">
          <Dan size={150} bone title="Handsome Dan cartwheeling with a biscuit" />
        </div>
      </div>
      {Array.from({ length: 36 }, (_, i) => (
        <span
          key={i}
          className="confetti"
          style={{
            left: `${(i * 97) % 100}%`,
            background: CONFETTI[i % CONFETTI.length],
            animationDelay: `${(i % 12) * 0.09}s`,
            transform: `rotate(${i * 37}deg)`,
          }}
        />
      ))}
    </div>
  )
}
