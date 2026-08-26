import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import {
  FaBell,
  FaChevronDown,
  FaHeart,
  FaShoppingCart,
  FaUserCircle,
  FaWallet,
  FaBoxOpen,
  FaStore,
  FaSignOutAlt,
} from "react-icons/fa";

import { useCart } from "../../../context/CartContext";
import { useWishlist } from "../../../context/WishlistContext";
import { useNotifications } from "../../../context/NotificationContext";
import { useAuth } from "../../../context/AuthContext";

export default function UserMenu() {
  const navigate = useNavigate();
  const {
  currentUser,
  logout,
} = useAuth();

  const { cart } = useCart();
  const { wishlist } = useWishlist();
  const { notifications } = useNotifications();

  const [open, setOpen] = useState(false);

  const unreadNotifications = notifications.filter(
    (notification) => !notification.read
  ).length;


  const handleLogout = () => {
  logout();

  setOpen(false);

  navigate("/login");
};

  const Badge = ({ count }: { count: number }) =>
    count > 0 ? (
      <span
        className="
          absolute
          -top-2
          -right-2
          bg-red-600
          text-white
          text-xs
          w-5
          h-5
          rounded-full
          flex
          items-center
          justify-center
        "
      >
        {count}
      </span>
    ) : null;

  return (
    <div className="hidden lg:flex items-center gap-6">

      {/* Wishlist */}

      <Link
        to="/wishlist"
        className="relative hover:text-blue-600 transition"
      >
        <FaHeart className="text-xl" />
        <Badge count={wishlist.length} />
      </Link>

      {/* Wallet */}

      <Link
        to="/wallet"
        className="hover:text-blue-600 transition"
      >
        <FaWallet className="text-xl" />
      </Link>

      {/* Notifications */}

      <Link
        to="/notifications"
        className="relative hover:text-blue-600 transition"
      >
        <FaBell className="text-xl" />
        <Badge count={unreadNotifications} />
      </Link>

      {/* Cart */}

      <Link
        to="/cart"
        className="relative hover:text-blue-600 transition"
      >
        <FaShoppingCart className="text-xl" />
        <Badge count={cart.length} />
      </Link>

      {/* Login Button */}

      {!currentUser && (
  <div className="flex items-center gap-3">
    <Link
      to="/login"
      className="
        border
        border-blue-600
        text-blue-600
        px-4
        py-2
        rounded-xl
        hover:bg-blue-50
        transition
      "
    >
      Login
    </Link>

    <Link
      to="/register"
      className="
        bg-blue-600
        text-white
        px-4
        py-2
        rounded-xl
        hover:bg-blue-700
        transition
      "
    >
      Register
    </Link>
  </div>
)}

      {/* User Dropdown */}

      {currentUser && (
        <div className="relative">

          <button
            onClick={() => setOpen(!open)}
            className="
              flex
              items-center
              gap-2
              hover:text-blue-600
              transition
            "
          >
            <FaUserCircle className="text-2xl" />

            <span className="font-medium">
              {currentUser.fullName}
            </span>

            <FaChevronDown
              className={`transition ${
                open ? "rotate-180" : ""
              }`}
            />
          </button>

          {open && (
            <div
              className="
                absolute
                right-0
                mt-4
                w-72
                bg-white
                rounded-2xl
                shadow-2xl
                border
                overflow-hidden
                z-50
              "
            >
              {/* Header */}

              <div className="px-6 py-5 border-b">

                <p className="font-bold">
                  {currentUser.fullName}
                </p>

                <p className="text-sm text-gray-500">
                  {currentUser.email}
                </p>

              </div>

              {/* Menu */}

              <Link
                to="/profile"
                onClick={() => setOpen(false)}
                className="flex items-center gap-3 px-6 py-4 hover:bg-gray-100"
              >
                <FaUserCircle />
                My Profile
              </Link>

              {currentUser.role === "seller" && (
  <Link
   to="/seller-dashboard"
    onClick={() => setOpen(false)}
    className="flex items-center gap-3 px-6 py-4 hover:bg-gray-100"
  >
    <FaStore />
    Seller Dashboard
  </Link>
)}

              <Link
                to="/orders"
                onClick={() => setOpen(false)}
                className="flex items-center gap-3 px-6 py-4 hover:bg-gray-100"
              >
                <FaBoxOpen />
                My Orders
              </Link>

              <Link
                to="/wallet"
                onClick={() => setOpen(false)}
                className="flex items-center gap-3 px-6 py-4 hover:bg-gray-100"
              >
                <FaWallet />
                Wallet
              </Link>

<Link
  to="/referral"
  onClick={() => setOpen(false)}
  className="block px-5 py-3 hover:bg-gray-100"
>
  Referral Program
</Link>
              <button
                onClick={handleLogout}
                className="
                  flex
                  items-center
                  gap-3
                  w-full
                  px-6
                  py-4
                  text-red-600
                  hover:bg-red-50
                "
              >
                <FaSignOutAlt />
                Logout
              </button>

            </div>
          )}

        </div>
      )}

    </div>
  );
}