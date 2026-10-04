import { BadgeCheck, Gift, Headset, Wallet, type LucideIcon } from 'lucide-react'
import { Link } from 'react-router'
import { buttonVariants } from '@/components/ui/button'
import { cn } from '@/lib/utils'

const features: { icon: LucideIcon; title: string; text: string }[] = [
  { icon: BadgeCheck, title: 'Verified sellers', text: 'Subscribed and trusted' },
  { icon: Gift, title: 'Referral rewards', text: 'Earn on every deal' },
  { icon: Wallet, title: 'Clear earnings', text: 'Track it in your wallet' },
  { icon: Headset, title: 'Direct contact', text: 'Talk to the seller' },
]

export function Highlights() {
  return (
    <section className="mx-auto max-w-7xl space-y-10 px-4 py-10">
      <div className="reveal grid grid-cols-2 gap-4 rounded-3xl border bg-card p-6 shadow-sm lg:grid-cols-4">
        {features.map(({ icon: Icon, title, text }) => (
          <div key={title} className="group flex items-center gap-3">
            <span className="grid size-12 shrink-0 place-items-center rounded-2xl bg-accent text-primary transition group-hover:-rotate-12 group-hover:bg-primary group-hover:text-primary-foreground">
              <Icon />
            </span>
            <div>
              <p className="font-semibold">{title}</p>
              <p className="text-sm text-muted-foreground">{text}</p>
            </div>
          </div>
        ))}
      </div>

      <div className="reveal relative overflow-hidden rounded-3xl bg-primary px-6 py-12 text-center text-primary-foreground md:px-12">
        <div className="absolute -top-20 -left-20 size-72 animate-blob rounded-full bg-highlight/40 blur-3xl" />
        <div className="absolute -right-16 -bottom-24 size-72 animate-blob rounded-full bg-white/20 blur-3xl [animation-delay:-7s]" />
        <div className="relative">
          <h2 className="font-heading text-3xl font-extrabold md:text-4xl">Share your link. Earn on every deal.</h2>
          <p className="mx-auto mt-3 max-w-xl text-primary-foreground/80">
            Invite people to buy or sell on Muhuze and receive a commission each time they complete a transaction.
          </p>
          <Link to="/dashboard/referrals" className={cn(buttonVariants({ size: 'lg' }), 'mt-6 h-12 rounded-full bg-highlight px-8 text-base text-highlight-foreground hover:bg-highlight/90')}>
            <Gift /> Get my referral link
          </Link>
        </div>
      </div>
    </section>
  )
}
