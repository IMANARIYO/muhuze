import {
  FaBoxOpen,
  FaGlobeAfrica,
  FaStore,
  FaUsers,
} from "react-icons/fa";

import { useMarketplace } from "../../../context/MarketplaceContext";

export default function HeroStats() {
  const { items } = useMarketplace();

  /*
   * ==========================================
   * REAL MARKETPLACE PRODUCTS
   * ==========================================
   *
   * Count actual marketplace listings.
   */
  const marketplaceProducts = items.length;

  /*
   * ==========================================
   * REAL SELLER COMMUNITY
   * ==========================================
   *
   * A seller may have many listings.
   * Therefore we use a Set so each seller
   * is counted only once.
   */
  const sellerIds = new Set(
    items
      .map((item) => {
        if (typeof item.sellerId === "string") {
          return item.sellerId;
        }

        return item.sellerId?._id;
      })
      .filter(Boolean)
  );

  const sellerCommunity = sellerIds.size;

  /*
   * ==========================================
   * MARKETPLACE VISION
   * ==========================================
   *
   * This is currently a platform statement,
   * not a database count.
   */
  const marketplaceVision = "Global";

  /*
   * ==========================================
   * BUYER & SELLER NETWORK
   * ==========================================
   *
   * We do NOT invent a user count here.
   *
   * The MarketplaceItem type only gives us
   * seller information. It does not contain
   * buyer information or total registered users.
   *
   * Until we connect the Users API, we display
   * a truthful status instead of fake numbers.
   */
  const buyerSellerNetwork = "Connected";

  const heroStats = [
    {
      id: 1,
      value: marketplaceProducts.toString(),
      label: "Marketplace Products",
      icon: FaBoxOpen,
    },
    {
      id: 2,
      value: sellerCommunity.toString(),
      label: "Seller Community",
      icon: FaStore,
    },
    {
      id: 3,
      value: buyerSellerNetwork,
      label: "Buyer & Seller Network",
      icon: FaUsers,
    },
    {
      id: 4,
      value: marketplaceVision,
      label: "Marketplace Vision",
      icon: FaGlobeAfrica,
    },
  ];

  return (
    <div
      className="
        mt-20
        grid
        grid-cols-2
        gap-4
        lg:grid-cols-4
        lg:gap-6
      "
    >
      {heroStats.map((stat) => {
        const Icon = stat.icon;

        return (
          <div
            key={stat.id}
            className="
              group
              rounded-2xl
              border
              border-slate-100
              bg-white
              p-6
              shadow-sm
              transition
              duration-300
              hover:-translate-y-1
              hover:shadow-xl
            "
          >
            <div
              className="
                flex
                items-center
                gap-4
              "
            >
              <div
                className="
                  flex
                  h-12
                  w-12
                  shrink-0
                  items-center
                  justify-center
                  rounded-xl
                  bg-blue-50
                  text-blue-600
                  transition
                  group-hover:bg-blue-600
                  group-hover:text-white
                "
              >
                <Icon />
              </div>

              <div>
                <h3
                  className="
                    text-xl
                    font-extrabold
                    text-slate-900
                    sm:text-2xl
                  "
                >
                  {stat.value}
                </h3>

                <p
                  className="
                    mt-1
                    text-xs
                    font-medium
                    leading-5
                    text-slate-500
                    sm:text-sm
                  "
                >
                  {stat.label}
                </p>
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}