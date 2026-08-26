import {
  FaArrowDown,
  FaArrowUp,
  FaMoneyBillWave,
} from "react-icons/fa";

import { useWallet } from "../../context/WalletContext";

export default function WalletStatistics() {
  const {
    balance,
    pendingBalance,
    totalEarned,
    totalWithdrawn,
  } = useWallet();

  const cards = [
    {
      title: "Available Balance",
      value: balance,
      icon: <FaMoneyBillWave />,
      color: "text-blue-600",
      bg: "bg-blue-100",
    },
    {
      title: "Pending Balance",
      value: pendingBalance,
      icon: <FaArrowUp />,
      color: "text-yellow-600",
      bg: "bg-yellow-100",
    },
    {
      title: "Total Earned",
      value: totalEarned,
      icon: <FaArrowDown />,
      color: "text-green-600",
      bg: "bg-green-100",
    },
    {
      title: "Total Withdrawn",
      value: totalWithdrawn,
      icon: <FaArrowDown />,
      color: "text-purple-600",
      bg: "bg-purple-100",
    },
  ];

  return (
    <section className="mt-8">
      <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
        {cards.map((card) => (
          <div
            key={card.title}
            className="bg-white rounded-3xl shadow-lg p-6"
          >
            <div
              className={`w-14 h-14 rounded-2xl ${card.bg} ${card.color} flex items-center justify-center text-2xl`}
            >
              {card.icon}
            </div>

            <p className="mt-5 text-gray-500">
              {card.title}
            </p>

            <h3
              className={`text-2xl font-bold mt-2 ${card.color}`}
            >
              {card.value.toLocaleString()} USD
            </h3>
          </div>
        ))}
      </div>
    </section>
  );
}