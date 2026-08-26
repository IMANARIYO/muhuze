import { FaCopy, FaGift } from "react-icons/fa";

import { useReferral } from "../../context/ReferralContext";
import { useToast } from "../ui/Toast";

export default function ReferralCode() {
  const { referralCode } =
    useReferral();

  const { showToast } =
    useToast();

  async function handleCopy() {
    if (!referralCode) {
      showToast(
        "Referral code is not available.",
        "warning"
      );

      return;
    }

    try {
      await navigator.clipboard.writeText(
        referralCode
      );

      showToast(
        "Referral code copied successfully!",
        "success"
      );
    } catch {
      showToast(
        "Unable to copy referral code.",
        "error"
      );
    }
  }

  return (
    <div className="bg-white rounded-3xl shadow-lg p-8">
      {/* Header */}

      <div className="flex items-center gap-4">
        <div className="w-16 h-16 rounded-2xl bg-blue-100 flex items-center justify-center">
          <FaGift className="text-blue-600 text-3xl" />
        </div>

        <div>
          <h2 className="text-2xl font-bold text-gray-900">
            Your Referral Code
          </h2>

          <p className="text-gray-500">
            Share this code with friends.
          </p>
        </div>
      </div>

      {/* Referral Code */}

      <div className="mt-8 flex flex-col md:flex-row gap-4">
        <input
          type="text"
          readOnly
          value={referralCode}
          placeholder="Your referral code"
          className="
            flex-1
            border
            border-gray-300
            rounded-xl
            px-5
            py-4
            bg-slate-100
            font-bold
            text-xl
            text-gray-700
            outline-none
          "
        />

        <button
          type="button"
          onClick={handleCopy}
          disabled={!referralCode}
          className="
            bg-blue-600
            hover:bg-blue-700
            disabled:bg-gray-400
            disabled:cursor-not-allowed
            text-white
            rounded-xl
            px-8
            py-4
            flex
            items-center
            justify-center
            gap-3
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