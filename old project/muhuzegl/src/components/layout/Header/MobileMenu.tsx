import { useState } from "react";
import { Link, NavLink, useNavigate } from "react-router-dom";

import {
  FaBars,
  FaTimes,
  FaHeart,
  FaShoppingCart,
  FaBell,
  FaWallet,
  FaUserCircle,
  FaBoxOpen,
  FaStore,
  FaSignOutAlt,
} from "react-icons/fa";

import { navItems } from "./headerData";
import { useCart } from "../../../context/CartContext";
import { useWishlist } from "../../../context/WishlistContext";
import { useNotifications } from "../../../context/NotificationContext";

export default function MobileMenu() {
  const [open, setOpen] = useState(false);

  const navigate = useNavigate();

  const { cart } = useCart();
  const { wishlist } = useWishlist();
  const { notifications } = useNotifications();

  const unreadNotifications = notifications.filter(
    (notification) => !notification.read
  ).length;

  const currentUser = JSON.parse(
    localStorage.getItem("currentUser") || "null"
  );

  const handleLogout = () => {
    localStorage.removeItem("currentUser");
    setOpen(false);
    navigate("/login");
  };

  const Badge = ({ count }: { count: number }) =>
    count > 0 ? (
      <span className="ml-auto bg-red-600 text-white text-xs px-2 py-0.5 rounded-full">
        {count}
      </span>
    ) : null;

  return (
    <>
      {/* Hamburger */}

      <button
        onClick={() => setOpen(true)}
        className="lg:hidden text-2xl"
      >
        <FaBars />
      </button>

      {/* Overlay */}

      {open && (
        <div
          className="fixed inset-0 bg-black/50 z-40"
          onClick={() => setOpen(false)}
        />
      )}

      {/* Drawer */}

      <aside
        className={`
          fixed
          top-0
          left-0
          h-full
         w-[320px]
         max-w-[85vw]
          bg-white
          shadow-2xl
          z-50
          transition-transform
          duration-300
          ${
            open
              ? "translate-x-0"
              : "-translate-x-full"
          }
        `}
      >
        {/* Header */}

        <div className="flex items-center justify-between px-6 py-5 border-b">

          <div>

            <h2 className="text-2xl font-bold text-blue-600">
              MUHUZE
            </h2>

            {currentUser && (
              <p className="text-sm text-gray-500">
                {currentUser.fullName}
              </p>
            )}

          </div>

          <button
            onClick={() => setOpen(false)}
            className="text-2xl"
          >
            <FaTimes />
          </button>

        </div>

        {/* Navigation */}

        <div className="py-4">

          {navItems.map((item) => {
            const Icon = item.icon;

            return (
              <NavLink
                key={item.id}
                to={item.path}
                onClick={() => setOpen(false)}
                className={({ isActive }) =>
                  `
                    flex
                    items-center
                    gap-4
                    px-6
                    py-4
                    transition
                    ${
                      isActive
                        ? "bg-blue-50 text-blue-600 font-semibold"
                        : "hover:bg-gray-100"
                    }
                  `
                }
              >
                <Icon />

                {item.label}
              </NavLink>
            );
          })}

        </div>

        <hr />

        {/* User Section */}

        <div className="py-4">

          <Link
            to="/wishlist"
            onClick={() => setOpen(false)}
            className="flex items-center px-6 py-4 hover:bg-gray-100"
          >
            <FaHeart />

            <span className="ml-4">
              Wishlist
            </span>

            <Badge count={wishlist.length} />
          </Link>

          <Link
            to="/cart"
            onClick={() => setOpen(false)}
            className="flex items-center px-6 py-4 hover:bg-gray-100"
          >
            <FaShoppingCart />

            <span className="ml-4">
              Cart
            </span>

            <Badge count={cart.length} />
          </Link>

          <Link
            to="/notifications"
            onClick={() => setOpen(false)}
            className="flex items-center px-6 py-4 hover:bg-gray-100"
          >
            <FaBell />

            <span className="ml-4">
              Notifications
            </span>

            <Badge count={unreadNotifications} />
          </Link>

          <Link
            to="/wallet"
            onClick={() => setOpen(false)}
            className="flex items-center px-6 py-4 hover:bg-gray-100"
          >
            <FaWallet />

            <span className="ml-4">
              Wallet
            </span>
          </Link>

          {currentUser && (
            <>
              <Link
                to="/profile"
                onClick={() => setOpen(false)}
                className="flex items-center px-6 py-4 hover:bg-gray-100"
              >
                <FaUserCircle />

                <span className="ml-4">
                  Profile
                </span>
              </Link>

              <Link
              to="/seller-dashboard"                onClick={() => setOpen(false)}
                className="flex items-center px-6 py-4 hover:bg-gray-100"
              >
                <FaStore />

                <span className="ml-4">
                  Seller Dashboard
                </span>
              </Link>

              <Link
                to="/orders"
                onClick={() => setOpen(false)}
                className="flex items-center px-6 py-4 hover:bg-gray-100"
              >
                <FaBoxOpen />

                <span className="ml-4">
                  Orders
                </span>
              </Link>

              <button
                onClick={handleLogout}
                className="
                  w-full
                  flex
                  items-center
                  px-6
                  py-4
                  text-red-600
                  hover:bg-red-50
                "
              >
                <FaSignOutAlt />

                <span className="ml-4">
                  Logout
                </span>
              </button>
            </>
          )}

          {!currentUser && (
            <Link
              to="/login"
              onClick={() => setOpen(false)}
              className="
                block
                mx-6
                mt-4
                text-center
                bg-blue-600
                text-white
                py-3
                rounded-xl
                hover:bg-blue-700
              "
            >
              Login
            </Link>
          )}

        </div>

      </aside>
    </>
  );
}