import { Link } from "react-router-dom";
import {
  FaSearch,
  FaShieldAlt,
  FaStore,
  FaArrowRight,
} from "react-icons/fa";

import { useAuth } from "../../../context/AuthContext";

export default function HeroContent() {
  const { currentUser } = useAuth();

  /*
   * ==========================================
   * SELLER DESTINATION
   * ==========================================
   *
   * Logged-in users can go directly to the
   * upload-product page.
   *
   * Users who are not logged in are sent
   * to registration first.
   */
  const sellerDestination = currentUser
    ? "/upload-product"
    : "/register";

  return (
    <div className="space-y-8">

      {/* =========================
          BADGE
      ========================= */}

      <div
        className="
          inline-flex
          items-center
          gap-2
          rounded-full
          bg-blue-50
          px-4
          py-2
          text-sm
          font-bold
          tracking-wide
          text-blue-700
        "
      >
        <span className="h-2.5 w-2.5 rounded-full bg-orange-500" />

        WELCOME TO MUHUZE GLOBAL LINK
      </div>

      {/* =========================
          MAIN HEADING
      ========================= */}

      <div>

        <h1
          className="
            text-5xl
            font-extrabold
            leading-[1.05]
            tracking-tight
            text-slate-950
            sm:text-6xl
            lg:text-7xl
          "
        >
          Connect.

          <span className="block text-blue-600">
            Discover.
          </span>

          <span className="block">
            <span className="text-orange-500">
              Trade.
            </span>{" "}
            Grow.
          </span>
        </h1>

        <p
          className="
            mt-7
            max-w-xl
            text-lg
            leading-8
            text-slate-600
            lg:text-xl
          "
        >
          MUHUZE Global Link connects people, businesses,
          products and opportunities in one trusted marketplace
          built for Africa and the world.
        </p>

      </div>

      {/* =========================
          MAIN ACTIONS
      ========================= */}

      <div className="flex flex-wrap gap-4">

        {/* =========================
            START SHOPPING
        ========================= */}

        <Link
          to="/marketplace"
          className="
            inline-flex
            items-center
            justify-center
            gap-3
            rounded-xl
            bg-blue-600
            px-7
            py-4
            font-bold
            text-white
            shadow-lg
            shadow-blue-600/20
            transition
            hover:bg-blue-700
            hover:-translate-y-0.5
          "
        >
          <FaSearch />

          Start Shopping

          <FaArrowRight className="text-sm" />
        </Link>

        {/* =========================
            SELL ON MUHUZE
        ========================= */}

        <Link
          to={sellerDestination}
          className="
            inline-flex
            items-center
            justify-center
            gap-3
            rounded-xl
            border-2
            border-orange-500
            bg-white
            px-7
            py-4
            font-bold
            text-orange-500
            transition
            hover:bg-orange-500
            hover:text-white
          "
        >
          <FaStore />

          Sell on MUHUZE
        </Link>

      </div>

      {/* =========================
          TRUST INDICATORS
      ========================= */}

      <div
        className="
          flex
          flex-wrap
          gap-x-8
          gap-y-3
          pt-2
          text-sm
          font-medium
          text-slate-600
        "
      >

        <div className="flex items-center gap-2">
          <FaShieldAlt className="text-blue-600" />
          Trusted & Secure
        </div>

        <div className="flex items-center gap-2">
          <FaStore className="text-blue-600" />
          Local & Global Marketplace
        </div>

        <div className="flex items-center gap-2">
          <FaShieldAlt className="text-orange-500" />
          Safe Deals
        </div>

      </div>

    </div>
  );
}