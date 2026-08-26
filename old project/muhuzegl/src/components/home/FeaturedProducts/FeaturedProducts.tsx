import { Link } from "react-router-dom";
import { FaArrowRight } from "react-icons/fa";

import ProductCard from "./ProductCard";
import { useMarketplace } from "../../../context/MarketplaceContext";

export default function FeaturedProducts() {
  const { items } = useMarketplace();

  const featuredProducts = items
    .filter((item) => item.featured)
    .slice(0, 4);

  return (
    <section
  className="
    bg-white
    py-12
    lg:py-16
  "
>
      <div className="mx-auto max-w-7xl px-6">

        {/* ======================================
            SECTION HEADER
        ====================================== */}

        <div
          className="
            flex
            flex-col
            gap-6
            lg:flex-row
            lg:items-end
            lg:justify-between
          "
        >
          <div className="max-w-3xl">

            <span
              className="
                font-semibold
                uppercase
                tracking-[0.2em]
                text-blue-600
              "
            >
              Marketplace Picks
            </span>

            <h2
              className="
                mt-3
                text-4xl
                font-extrabold
                tracking-tight
                text-slate-950
                lg:text-5xl
              "
            >
              Featured Products
            </h2>

            <p
              className="
                mt-4
                max-w-2xl
                text-lg
                leading-8
                text-slate-600
              "
            >
              Discover selected products from sellers
              across the MUHUZE marketplace.
            </p>

          </div>

        <Link
  to="/products"
  className="
    group
    inline-flex
    items-center
    gap-3
    self-start
    rounded-xl
    bg-blue-600
    px-6
    py-3
    font-semibold
    text-white
    shadow-lg
    shadow-blue-600/20
    transition
    hover:bg-orange-500
    lg:self-auto
  "
>
  View All Products

  <FaArrowRight
    className="
      transition
      group-hover:translate-x-1
    "
  />
</Link>
        </div>

        {/* ======================================
            PRODUCTS
        ====================================== */}

        {featuredProducts.length > 0 ? (
          <div
            className="
              mt-12
              grid
              grid-cols-1
              gap-6
              sm:grid-cols-2
              lg:grid-cols-4
            "
          >
            {featuredProducts.map((product) => (
              <ProductCard
                key={product._id}
                product={product}
              />
            ))}
          </div>
        ) : (
          <div
            className="
              mt-12
              rounded-3xl
              border
              border-slate-200
              bg-white
              px-6
              py-16
              text-center
              shadow-sm
            "
          >
            <h3
              className="
                text-xl
                font-bold
                text-slate-900
              "
            >
              Featured products are coming soon.
            </h3>

            <p
              className="
                mx-auto
                mt-3
                max-w-lg
                text-slate-500
              "
            >
              Explore the marketplace to discover
              products from MUHUZE sellers.
            </p>

            <Link
              to="/products"
              className="
                mt-6
                inline-flex
                items-center
                gap-2
                font-semibold
                text-blue-600
                transition
                hover:text-orange-500
              "
            >
              Explore Marketplace

              <FaArrowRight />
            </Link>
          </div>
        )}

      </div>
    </section>
  );
}