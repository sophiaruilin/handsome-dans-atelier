import { useEffect, useState } from 'react'
import { onDan } from './danBus'

// True for a moment whenever Dan should jump; use it to add the "jumping" class.
export function useDanJump(): boolean {
  const [jumping, setJumping] = useState(false)
  useEffect(() => {
    let timer: number | undefined
    const off = onDan((move) => {
      if (move !== 'jump') return
      // Off, then on again a moment later, so a second add restarts the animation.
      setJumping(false)
      window.clearTimeout(timer)
      timer = window.setTimeout(() => {
        setJumping(true)
        timer = window.setTimeout(() => setJumping(false), 1100)
      }, 30)
    })
    return () => {
      off()
      window.clearTimeout(timer)
    }
  }, [])
  return jumping
}
