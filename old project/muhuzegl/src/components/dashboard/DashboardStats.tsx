import {
  FaBoxOpen,
  FaMoneyBillWave,
  FaShoppingBag,
  FaWallet,
} from "react-icons/fa";

import { useMarketplace } from "../../context/MarketplaceContext";
import { useOrders } from "../../context/OrderContext";
import { useWallet } from "../../context/WalletContext";

export default function DashboardStats() {
const { items } = useMarketplace();
  const { orders } = useOrders();

  const { balance } = useWallet();

  const cards = [
    {
  title: "Listings",
  value: items.length,
  icon: <FaBoxOpen />,
  color: "bg-blue-100 text-blue-700",
},
    {
      title: "Orders",
      value: orders.length,
      icon: <FaShoppingBag />,
      color: "bg-green-100 text-green-700",
    },
    {
      title: "Wallet",
      value: `${balance.toLocaleString()} RWF`,
      icon: <FaWallet />,
      color: "bg-yellow-100 text-yellow-700",
    },
    {
      title: "Revenue",
      value: `${orders
        .reduce(
          (sum, order) =>
            sum + order.total,
          0
        )
        .toLocaleString()} RWF`,
      icon: <FaMoneyBillWave />,
      color: "bg-purple-100 text-purple-700",
    },
  ];

  return (
    <div className="grid md:grid-cols-2 xl:grid-cols-4 gap-6 mt-10">
      {cards.map((card) => (
        <div
          key={card.title}
          className="bg-white rounded-3xl shadow-lg p-6"
        >
          <div
            className={`w-14 h-14 rounded-2xl flex items-center justify-center text-2xl ${card.color}`}
          >
            {card.icon}
          </div>

          <p className="mt-5 text-gray-500">
            {card.title}
          </p>

          <h2 className="text-3xl font-bold mt-2">
            {card.value}
          </h2>
        </div>
      ))}
    </div>
  );
}