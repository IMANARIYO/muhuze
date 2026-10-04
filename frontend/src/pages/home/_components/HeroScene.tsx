import { Eye, Gift, ShieldCheck } from 'lucide-react'
import type { PointerEvent } from 'react'
import type { Product } from '@/types/product'

const card = 'absolute overflow-hidden rounded-3xl border-4 border-background bg-card shadow-2xl shadow-primary/30'
const chip = 'absolute flex items-center gap-2 rounded-2xl bg-background/90 px-4 py-2.5 text-sm font-semibold shadow-xl backdrop-blur'

// The stage tilts toward the pointer; each layer sits at its own depth, giving real parallax.
function tilt(event: PointerEvent<HTMLDivElement>) {
  const box = event.currentTarget.getBoundingClientRect()
  const stage = event.currentTarget.style
  stage.setProperty('--tilt-x', `${((event.clientY - box.top) / box.height - 0.5) * -18}deg`)
  stage.setProperty('--tilt-y', `${((event.clientX - box.left) / box.width - 0.5) * 22}deg`)
}

function reset(event: PointerEvent<HTMLDivElement>) {
  event.currentTarget.style.removeProperty('--tilt-x')
  event.currentTarget.style.removeProperty('--tilt-y')
}

export function HeroScene({ products }: { products: Product[] }) {
  const [main, second, third] = products

  return (
    <div className="relative mx-auto aspect-square w-full max-w-lg perspective-[1100px]" onPointerMove={tilt} onPointerLeave={reset}>
      <div className="absolute inset-[12%] animate-blob rounded-full bg-linear-to-br from-primary to-highlight opacity-50 blur-3xl" />
      <div className="absolute inset-[6%] animate-spin-slow rounded-full border-2 border-dashed border-primary/30" />

      <div className="absolute inset-0 transition-transform duration-300 ease-out transform-3d [transform:rotateX(var(--tilt-x,6deg))_rotateY(var(--tilt-y,-14deg))]">
        {main && (
          <div className={`${card} inset-[20%] animate-float`}>
            <img src={main.image} alt={main.title} className="size-full object-cover" fetchPriority="high" />
          </div>
        )}
        {second && (
          <div className={`${card} top-[6%] right-0 w-[38%] translate-z-24 animate-float-slow`}>
            <img src={second.image} alt={second.title} className="aspect-4/3 w-full object-cover" />
          </div>
        )}
        {third && (
          <div className={`${card} bottom-[8%] left-0 w-[36%] translate-z-36 animate-float [animation-delay:-3s]`}>
            <img src={third.image} alt={third.title} className="aspect-square w-full object-cover" />
          </div>
        )}
        <p className={`${chip} top-[14%] left-[2%] translate-z-48 animate-float-slow`}>
          <Eye className="size-4 text-primary" /> 6.2k views today
        </p>
        <p className={`${chip} right-[2%] bottom-[14%] translate-z-56 animate-float [animation-delay:-2s]`}>
          <Gift className="size-4 text-highlight" /> Referral earned
        </p>
        <p className={`${chip} bottom-0 left-[34%] translate-z-40 animate-float-slow [animation-delay:-5s]`}>
          <ShieldCheck className="size-4 text-primary" /> Verified seller
        </p>
      </div>
    </div>
  )
}
