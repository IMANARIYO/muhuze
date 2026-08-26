import { Link } from "react-router-dom";

import {
  FaBoxOpen,
  FaBell,
  FaPlusCircle,
  FaShoppingBag,
  FaWallet,
} from "react-icons/fa";

const actions = [
  {
    title: "Upload Product",
    icon: <FaPlusCircle />,
    path: "/upload-product",
    color: "bg-blue-600",
  },
  {
    title: "My Products",
    icon: <FaBoxOpen />,
    path: "/my-products",
    color: "bg-green-600",
  },
  {
    title: "Seller Orders",
    icon: <FaShoppingBag />,
    path: "/seller-orders",
    color: "bg-purple-600",
  },
  {
    title: "Wallet",
    icon: <FaWallet />,
    path: "/wallet",
    color: "bg-yellow-500",
  },
  {
    title: "Notifications",
    icon: <FaBell />,
    path: "/notifications",
    color: "bg-red-500",
  },
];

export default function DashboardQuickActions() {
  return (
    <section className="mt-10">
      <h2 className="text-2xl font-bold mb-6">
        Quick Actions
      </h2>

      <div className="grid grid-cols-2 lg:grid-cols-5 gap-6">
        {actions.map((action) => (
          <Link
            key={action.title}
            to={action.path}
            className={`
              ${action.color}
              rounded-3xl
              text-white
              p-6
              text-center
              shadow-lg
              hover:scale-105
              transition
            `}
          >
            <div className="text-4xl flex justify-center mb-4">
              {action.icon}
            </div>

            <h3 className="font-semibold">
              {action.title}
            </h3>
          </Link>
        ))}
      </div>
    </section>
  );
}