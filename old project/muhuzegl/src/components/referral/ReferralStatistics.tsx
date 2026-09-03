import {
  FaGift,
  FaUsers,
  FaMoneyBillWave,
} from "react-icons/fa";

import { useReferral } from "../../context/ReferralContext";

export default function ReferralStatistics() {
  const {
    referrals,
    totalReferrals,
    totalRewards,
  } = useReferral();

  /**
   * ==========================================
   * COMPLETED REFERRALS
   * ==========================================
   */

  const completedReferrals =
    referrals.filter(
      (referral) =>
        referral.status ===
        "Completed"
    ).length;

  /**
   * ==========================================
   * PENDING REFERRALS
   * ==========================================
   */

  const pendingReferrals =
    referrals.filter(
      (referral) =>
        referral.status ===
        "Pending"
    ).length;

  /**
   * ==========================================
   * STATISTICS CARDS
   * ==========================================
   */

  const cards = [
    {
      title: "Total Referrals",

      value: totalReferrals,

      suffix: "",

      icon: <FaUsers />,

      color: "text-blue-600",

      bg: "bg-blue-100",
    },

    {
      title: "Referral Rewards",

      value: totalRewards,

      suffix: "RWF",

      icon: <FaMoneyBillWave />,

      color: "text-green-600",

      bg: "bg-green-100",
    },

    {
      title: "Completed Referrals",

      value: completedReferrals,

      suffix: "",

      icon: <FaGift />,

      color: "text-purple-600",

      bg: "bg-purple-100",
    },
  ];

  return (
    <section className="mt-10">
      {/* ===================================== */}
      {/* TITLE */}
      {/* ===================================== */}

      <h2 className="text-2xl font-bold mb-6">
        Referral Statistics
      </h2>

      {/* ===================================== */}
      {/* STATISTICS */}
      {/* ===================================== */}

      <div className="grid md:grid-cols-3 gap-6">
        {cards.map(
          (card) => (
            <div
              key={card.title}
              className="bg-white rounded-3xl shadow-lg p-6"
            >
              {/* Icon */}

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

              {/* Title */}

              <p className="mt-5 text-gray-500">
                {card.title}
              </p>

              {/* Value */}

              <h3
                className={`
                  text-3xl
                  font-bold
                  mt-2
                  ${card.color}
                `}
              >
                {card.value.toLocaleString()}{" "}
                {card.suffix}
              </h3>
            </div>
          )
        )}
      </div>

      {/* ===================================== */}
      {/* PENDING REFERRALS */}
      {/* ===================================== */}

      <div className="mt-6">
        <div className="bg-white rounded-3xl shadow-lg p-6">
          <p className="text-gray-500">
            Pending Referrals 
          </p>

          <h3 className="text-2xl font-bold mt-2 text-yellow-600">
            {pendingReferrals.toLocaleString()}
          </h3>
        </div>
      </div>
    </section>
  );
}