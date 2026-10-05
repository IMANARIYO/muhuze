import { Gift } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { shareReferralLink } from '@/lib/referral'

export function Highlights({ referralCode }: { referralCode?: string }) {
  return (
    <section className="mx-auto max-w-7xl px-4 py-10">
      <div className="reveal relative overflow-hidden rounded-3xl bg-primary px-6 py-12 text-center text-primary-foreground md:px-12">
        <div className="absolute -top-20 -left-20 size-72 animate-blob rounded-full bg-highlight/40 blur-3xl" />
        <div className="absolute -right-16 -bottom-24 size-72 animate-blob rounded-full bg-white/20 blur-3xl [animation-delay:-7s]" />
        <div className="relative">
          <h2 className="font-heading text-3xl font-extrabold md:text-4xl">Share your link. Earn on every deal.</h2>
          <p className="mx-auto mt-3 max-w-xl text-primary-foreground/80">
            Invite people to buy or sell on Muhuze and receive a commission each time they complete a transaction.
          </p>
          {referralCode && (
            <Button
              size="lg"
              className="mt-6 h-12 rounded-full bg-highlight px-8 text-base text-highlight-foreground hover:bg-highlight/90"
              onClick={() => shareReferralLink(referralCode)}
            >
              <Gift /> Share my referral link
            </Button>
          )}
        </div>
      </div>
    </section>
  )
}
