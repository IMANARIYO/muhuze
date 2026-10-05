import { useEffect, useRef } from 'react'
import { formatCount } from '@/lib/format'

const DURATION = 3000

/** Counts from zero to `to` in three seconds, starting when it scrolls into view. */
export function CountUp({ to, suffix }: { to: number; suffix: string }) {
  const ref = useRef<HTMLSpanElement>(null)

  useEffect(() => {
    const node = ref.current
    if (!node) return
    // Written straight to the DOM: one text update per frame without re-rendering the hero.
    const show = (value: number) => {
      node.textContent = formatCount(Math.round(value)) + suffix
    }
    if (matchMedia('(prefers-reduced-motion: reduce)').matches) {
      show(to)
      return
    }

    let frame = 0
    const observer = new IntersectionObserver(([entry]) => {
      if (!entry.isIntersecting) return
      observer.disconnect()
      const start = performance.now()
      const tick = (now: number) => {
        const progress = Math.min((now - start) / DURATION, 1)
        // Fast at first, slowing down as it reaches the final number.
        show(to * (1 - (1 - progress) ** 3))
        if (progress < 1) frame = requestAnimationFrame(tick)
      }
      frame = requestAnimationFrame(tick)
    })
    observer.observe(node)
    return () => {
      observer.disconnect()
      cancelAnimationFrame(frame)
    }
  }, [to, suffix])

  return <span ref={ref} className="tabular-nums">{`0${suffix}`}</span>
}
