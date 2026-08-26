import {
  FaMoneyBillWave,
  FaClock,
  FaWallet,
  FaUndo,
  FaTimesCircle,
} from "react-icons/fa";

import { useReferralCommission } from "../../context/ReferralCommissionContext";

export default function ReferralCommissionStatistics() {
  const {
    summary,
    loading,
    error,
  } = useReferralCommission();

  const cards = [
    {
      title: "Total Commission",
      value: summary.totalCommission,
      icon: <FaMoneyBillWave />,
      color: "text-blue-600",
      bg: "bg-blue-100",
    },
    {
      title: "Pending Commission",
      value: summary.pendingCommission,
      icon: <FaClock />,
      color: "text-yellow-600",
      bg: "bg-yellow-100",
    },
    {
      title: "Available Commission",
      value: summary.availableCommission,
      icon: <FaWallet />,
      color: "text-green-600",
      bg: "bg-green-100",
    },
    {
      title: "Reversed Commission",
      value: summary.reversedCommission,
      icon: <FaUndo />,
      color: "text-orange-600",
      bg: "bg-orange-100",
    },
    {
      title: "Cancelled Commission",
      value: summary.cancelledCommission,
      icon: <FaTimesCircle />,
      color: "text-red-600",
      bg: "bg-red-100",
    },
  ];

  /**
   * ==========================================
   * LOADING
   * ==========================================
   */

  if (loading) {
    return (
      <section className="mt-10">
        <h2 className="text-2xl font-bold mb-6">
          Referral Commissions
        </h2>

        <div className="bg-white rounded-3xl shadow-lg p-8 text-center text-gray-500">
          Loading commission data...
        </div>
      </section>
    );
  }

  /**
   * ==========================================
   * ERROR
   * ==========================================
   */

  if (error) {
    return (
      <section className="mt-10">
        <h2 className="text-2xl font-bold mb-6">
          Referral Commissions
        </h2>

        <div className="bg-red-50 border border-red-200 rounded-3xl p-6 text-red-700">
          Unable to load referral commissions.
        </div>
      </section>
    );
  }

  /**
   * ==========================================
   * DISPLAY
   * ==========================================
   */

  return (
    <section className="mt-10">
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-900">
          Referral Commissions
        </h2>

        <p className="text-gray-500 mt-1">
          Track your earnings from your referral network.
        </p>
      </div>

      <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-6">
        {cards.map((card) => (
          <div
            key={card.title}
            className="bg-white rounded-3xl shadow-lg p-6"
          >
            <div
              className={`
                w-14
                h-14
                rounded-2xl
                ${card.bg}
                flex
                items-center
                justify-center
                text-2xl
                ${card.color}
              `}
            >
              {card.icon}
            </div>

            <p className="mt-5 text-gray-500">
              {card.title}
            </p>

            <h3
              className={`
                text-3xl
                font-bold
                mt-2
                ${card.color}
              `}
            >
              {card.value.toLocaleString()} USD
            </h3>
          </div>
        ))}
      </div>

      {/* Commission Rates */}

      <div className="mt-8 bg-white rounded-3xl shadow-lg p-8">
        <h3 className="text-xl font-bold text-gray-900">
          Commission Levels
        </h3>

        <p className="text-gray-500 mt-1">
          Your referral commission structure.
        </p>

        <div className="grid md:grid-cols-3 gap-4 mt-6">
          <div className="rounded-2xl bg-blue-50 p-5">
            <p className="text-gray-500">
              Level 1
            </p>

            <p className="text-3xl font-bold text-blue-600 mt-2">
              12%
            </p>
          </div>

          <div className="rounded-2xl bg-green-50 p-5">
            <p className="text-gray-500">
              Level 2
            </p>

            <p className="text-3xl font-bold text-green-600 mt-2">
              5%
            </p>
          </div>

          <div className="rounded-2xl bg-purple-50 p-5">
            <p className="text-gray-500">
              Level 3
            </p>

            <p className="text-3xl font-bold text-purple-600 mt-2">
              3%
            </p>
          </div>
        </div>
      </div>
    </section>
  );
}