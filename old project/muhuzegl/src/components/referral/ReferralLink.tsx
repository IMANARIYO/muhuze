import { FaLink, FaCopy } from "react-icons/fa";

import { useReferral } from "../../context/ReferralContext";
import { useToast } from "../ui/Toast";

export default function ReferralLink() {
  const { referralLink } = useReferral();

  const { showToast } = useToast();

  async function handleCopy() {
    if (!referralLink) {
      showToast(
        "Referral link is not available.",
        "warning"
      );

      return;
    }

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
    <div className="bg-white rounded-3xl shadow-lg p-8 mt-8">
      {/* Header */}
      <div className="flex items-center gap-4">
        <div className="w-16 h-16 rounded-2xl bg-green-100 flex items-center justify-center">
          <FaLink className="text-green-600 text-2xl" />
        </div>

        <div>
          <h2 className="text-2xl font-bold text-gray-900">
            Referral Link
          </h2>

          <p className="text-gray-500">
            Share this link with your friends.
          </p>
        </div>
      </div>

      {/* Referral Link */}
      <div className="mt-6 flex flex-col md:flex-row gap-4">
        <input
          type="text"
          readOnly
          value={referralLink}
          placeholder="Your referral link"
          className="
            flex-1
            border
            border-gray-300
            rounded-xl
            px-5
            py-4
            bg-slate-100
            text-gray-700
            outline-none
            focus:ring-2
            focus:ring-green-500
          "
        />

        <button
          type="button"
          onClick={handleCopy}
          disabled={!referralLink}
          className="
            bg-green-600
            hover:bg-green-700
            disabled:bg-gray-400
            disabled:cursor-not-allowed
            text-white
            rounded-xl
            px-8
            py-4
            flex
            items-center
            justify-center
            gap-2
            transition
          "
        >
          <FaCopy />

          Copy
        </button>
      </div>
    </div>
  );
}