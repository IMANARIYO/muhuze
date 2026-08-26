import type { PremiumPlan } from "../../types/premium";

interface PremiumReceiptProps {
  open: boolean;
  plan: PremiumPlan | null;
  receiptNumber: string;
  paymentDate: string;
  customerName: string;
  customerEmail: string;
  onClose: () => void;
}

export default function PremiumReceipt({
  open,
  plan,
  receiptNumber,
  paymentDate,
  customerName,
  customerEmail,
  onClose,
}: PremiumReceiptProps) {
  if (!open || !plan) {
    return null;
  }

  function handlePrint() {
    window.print();
  }

  const benefits = plan.benefits;

  return (
    <div className="fixed inset-0 bg-black/60 flex justify-center items-center z-50 p-5 overflow-y-auto">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-3xl overflow-hidden my-8">

        {/* ==========================================
            HEADER
        ========================================== */}

        <div className="bg-blue-700 text-white p-8">
          <h1 className="text-4xl font-bold">
            MUHUZE
          </h1>

          <p className="mt-2">
            Premium Membership Receipt
          </p>
        </div>

        {/* ==========================================
            BODY
        ========================================== */}

        <div className="p-8">

          {/* ========================================
              CUSTOMER + RECEIPT INFORMATION
          ======================================== */}

          <div className="grid md:grid-cols-2 gap-8">

            <div>
              <h2 className="text-xl font-bold mb-4">
                Customer Information
              </h2>

              <div className="space-y-2">
                <p>
                  <strong>Name:</strong>{" "}
                  {customerName}
                </p>

                <p>
                  <strong>Email:</strong>{" "}
                  {customerEmail}
                </p>
              </div>
            </div>

            <div>
              <h2 className="text-xl font-bold mb-4">
                Receipt Details
              </h2>

              <div className="space-y-2">
                <p>
                  <strong>Receipt No:</strong>{" "}
                  {receiptNumber}
                </p>

                <p>
                  <strong>Date:</strong>{" "}
                  {paymentDate}
                </p>

                <p>
                  <strong>Status:</strong>{" "}
                  <span className="text-green-600 font-bold">
                    PAID
                  </span>
                </p>
              </div>
            </div>

          </div>

          {/* ==========================================
              MEMBERSHIP DETAILS
          ========================================== */}

          <div className="mt-10">

            <h2 className="text-xl font-bold mb-4">
              Membership Details
            </h2>

            <div className="overflow-x-auto">
              <table className="w-full border">

                <thead className="bg-slate-100">
                  <tr>
                    <th className="text-left p-4">
                      Description
                    </th>

                    <th className="text-center p-4">
                      Duration
                    </th>

                    <th className="text-right p-4">
                      Amount
                    </th>
                  </tr>
                </thead>

                <tbody>
                  <tr>
                    <td className="p-4">
                      {plan.name} Premium Membership
                    </td>

                    <td className="text-center p-4">
                      {plan.duration} Days
                    </td>

                    <td className="text-right pr-4 font-bold">
                      ${plan.price.toLocaleString()}
                    </td>
                  </tr>
                </tbody>

              </table>
            </div>

          </div>

          {/* ==========================================
              TOTAL
          ========================================== */}

          <div className="mt-8 flex justify-end">

            <div className="bg-blue-50 rounded-xl p-6 w-80">

              <div className="flex justify-between">
                <span>
                  Total Paid
                </span>

                <strong>
                  ${plan.price.toLocaleString()}
                </strong>
              </div>

            </div>

          </div>

          {/* ==========================================
              PREMIUM BENEFITS
          ========================================== */}

          <div className="mt-10">

            <h2 className="text-xl font-bold mb-4">
              Premium Benefits Included
            </h2>

            <ul className="space-y-3">

              {benefits.premiumBadge && (
                <li>
                  ✅ Premium Member Badge
                </li>
              )}

              {benefits.priorityNotifications && (
                <li>
                  ✅ Priority Notifications
                </li>
              )}

              {benefits.earlyPromotionAccess && (
                <li>
                  ✅ Early Access to Selected Promotions
                </li>
              )}

              {benefits.premiumOnlyPromotions && (
                <li>
                  ✅ Access to Premium-Only Promotions
                </li>
              )}

              {benefits.premiumDiscounts && (
                <li>
                  ✅ Special Premium Member Discounts
                </li>
              )}

              {benefits.enhancedFavorites && (
                <li>
                  ✅ Enhanced Favorites / Watchlist
                </li>
              )}

              {benefits.prioritySupport && (
                <li>
                  ✅ Priority Customer Support
                </li>
              )}

              {benefits.priorityServiceHandling && (
                <li>
                  ✅ Priority Handling for Eligible
                  MUHUZE Services
                </li>
              )}

              {benefits.enhancedVisibility && (
                <li>
                  ✅ Increased Product Visibility
                </li>
              )}

              {benefits.promotionalAdvantages && (
                <li>
                  ✅ Seller Promotional Advantages
                </li>
              )}

              {benefits.advancedAnalytics && (
                <li>
                  ✅ Advanced Seller Analytics
                </li>
              )}

              {benefits.unlimitedListings && (
                <li>
                  ✅ Unlimited Product Listings
                </li>
              )}

              {benefits.sellerVerificationEligible && (
                <li>
                  ✅ Premium Seller Verification Eligibility
                </li>
              )}

              {/* ======================================
                  SELLER COMMISSION
              ====================================== */}

              <li>
                💰 Premium Seller Commission:{" "}
                <strong>
                  {benefits.sellerCommissionRate}%
                </strong>
              </li>

              {/* ======================================
                  REFERRAL PARTICIPATION
              ====================================== */}

              {benefits.referralCommissionEligible && (
                <li>
                  🤝 Eligible for Referral Commission
                  Participation
                </li>
              )}

            </ul>

          </div>

          {/* ==========================================
              REFERRAL DISCLAIMER
          ========================================== */}

          {benefits.referralCommissionEligible && (
            <div className="mt-8 bg-blue-50 border border-blue-100 rounded-xl p-5">

              <h3 className="font-bold text-blue-800">
                Referral Commission Information
              </h3>

              <p className="text-gray-600 mt-2 text-sm leading-relaxed">
                Premium membership makes you eligible
                to participate in the MUHUZE referral
                commission program. Membership itself
                does not guarantee income.
              </p>

              <p className="text-gray-600 mt-2 text-sm leading-relaxed">
                Referral commissions are generated only
                when qualifying referred users perform
                real economic activity that generates
                eligible MUHUZE revenue.
              </p>

            </div>
          )}

          {/* ==========================================
              MEMBERSHIP NOTICE
          ========================================== */}

          <div className="mt-8 border-t pt-6">

            <p className="text-gray-500 text-sm leading-relaxed">
              Premium benefits remain available while
              the membership is active. When the
              membership expires, Premium benefits are
              removed and the standard seller commission
              rate applies.
            </p>

          </div>

        </div>

        {/* ==========================================
            FOOTER
        ========================================== */}

        <div className="border-t p-6 flex justify-end gap-4">

          <button
            onClick={handlePrint}
            className="bg-green-600 hover:bg-green-700 text-white px-6 py-3 rounded-xl"
          >
            Print Receipt
          </button>

          <button
            onClick={onClose}
            className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-xl"
          >
            Close
          </button>

        </div>

      </div>
    </div>
  );
}