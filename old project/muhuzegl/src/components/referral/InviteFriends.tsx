import Button from "../ui/Button";

import { useReferral } from "../../context/ReferralContext";
import { useToast } from "../ui/Toast";

export default function InviteFriends() {
  const { referralLink } =
    useReferral();

  const { showToast } =
    useToast();

  async function handleShare() {
    if (!referralLink) {
      showToast(
        "Referral link is not available.",
        "warning"
      );

      return;
    }

    /**
     * ==========================================
     * NATIVE SHARE
     * ==========================================
     */

    if (
      typeof navigator.share ===
      "function"
    ) {
      try {
        await navigator.share({
          title:
            "Join MUHUZE Marketplace",

          text:
            "Use my referral link to join MUHUZE Marketplace!",

          url: referralLink,
        });

        showToast(
          "Thank you for sharing!",
          "success"
        );
      } catch {
        // User cancelled sharing.
        // No error toast needed.
      }

      return;
    }

    /**
     * ==========================================
     * FALLBACK: COPY LINK
     * ==========================================
     */

    try {
      await navigator.clipboard.writeText(
        referralLink
      );

      showToast(
        "Referral link copied!",
        "success"
      );
    } catch {
      showToast(
        "Unable to copy referral link.",
        "error"
      );
    }
  }

  return (
    <div className="mt-10 text-center">
      <Button
        size="lg"
        onClick={handleShare}
      >
        Invite Friends
      </Button>
    </div>
  );
}