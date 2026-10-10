import { toast } from 'sonner'

export const referralLink = (code: string) => `${location.origin}/r/${code}`

/** Opens the device share sheet when there is one, otherwise copies the link. */
export async function shareReferralLink(code: string) {
  const url = referralLink(code)
  if (typeof navigator.share === 'function') {
    // Rejects when the person closes the share sheet; nothing to report then.
    await navigator.share({ title: 'Join me on Muhuze', url }).catch(() => undefined)
    return
  }
  await navigator.clipboard.writeText(url)
  toast.success('Referral link copied')
}
