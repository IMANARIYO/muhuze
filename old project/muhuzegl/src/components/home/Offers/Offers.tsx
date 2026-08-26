import { Link } from "react-router-dom";

import {
  FaArrowRight,
  FaBolt,
  FaCheckCircle,
  FaShieldAlt,
  FaTags,
  FaTruck,
} from "react-icons/fa";

export default function Offers() {
  return (
    <section
      className="
        bg-slate-50
        py-12
        lg:py-16
      "
    >
      <div className="mx-auto max-w-7xl px-6">

        {/* ======================================
            OFFER CONTAINER
        ====================================== */}

        <div
          className="
            relative
            overflow-hidden
            rounded-[2rem]
            bg-gradient-to-br
            from-blue-700
            via-blue-600
            to-slate-950
            shadow-2xl
          "
        >

          {/* ====================================
              DECORATIVE BACKGROUND
          ==================================== */}

          <div
            className="
              absolute
              -right-24
              -top-24
              h-72
              w-72
              rounded-full
              bg-orange-500/20
            "
          />

          <div
            className="
              absolute
              -bottom-32
              -left-20
              h-80
              w-80
              rounded-full
              bg-white/10
            "
          />

          <div
            className="
              absolute
              right-1/3
              top-1/2
              h-40
              w-40
              -translate-y-1/2
              rounded-full
              bg-blue-400/10
              blur-2xl
            "
          />

          {/* ====================================
              CONTENT
          ==================================== */}

          <div
            className="
              relative
              z-10
              grid
              items-center
              gap-12
              p-8
              sm:p-12
              lg:grid-cols-2
              lg:p-16
            "
          >

            {/* ==================================
                LEFT CONTENT
            ================================== */}

            <div>

              {/* Badge */}

              <div
                className="
                  inline-flex
                  items-center
                  gap-2
                  rounded-full
                  border
                  border-orange-300/30
                  bg-orange-500
                  px-4
                  py-2
                  text-sm
                  font-bold
                  text-white
                  shadow-lg
                "
              >
                <FaBolt />

                SPECIAL MUHUZE OFFERS
              </div>

              {/* Heading */}

              <h2
                className="
                  mt-7
                  text-4xl
                  font-extrabold
                  leading-tight
                  tracking-tight
                  text-white
                  sm:text-5xl
                  lg:text-6xl
                "
              >
                Great Deals.

                <span
                  className="
                    block
                    text-orange-400
                  "
                >
                  More Value.
                </span>
              </h2>

              {/* Description */}

              <p
                className="
                  mt-6
                  max-w-xl
                  text-lg
                  leading-8
                  text-blue-100
                "
              >
                Discover special offers from trusted
                sellers across electronics, fashion,
                vehicles, home, technology and more.
              </p>

              {/* ==================================
                  BENEFITS
              ================================== */}

              <div
                className="
                  mt-8
                  grid
                  gap-4
                  sm:grid-cols-3
                "
              >

                <div
                  className="
                    flex
                    items-center
                    gap-2
                    text-sm
                    font-medium
                    text-white
                  "
                >
                  <FaShieldAlt className="text-orange-400" />

                  Secure
                </div>

                <div
                  className="
                    flex
                    items-center
                    gap-2
                    text-sm
                    font-medium
                    text-white
                  "
                >
                  <FaTruck className="text-orange-400" />

                  Fast Delivery
                </div>

                <div
                  className="
                    flex
                    items-center
                    gap-2
                    text-sm
                    font-medium
                    text-white
                  "
                >
                  <FaTags className="text-orange-400" />

                  Great Prices
                </div>

              </div>

              {/* ==================================
                  BUTTONS
              ================================== */}

              <div
                className="
                  mt-10
                  flex
                  flex-wrap
                  gap-4
                "
              >

                <Link
                  to="/products"
                  className="
                    group
                    inline-flex
                    items-center
                    gap-3
                    rounded-xl
                    bg-orange-500
                    px-7
                    py-4
                    font-bold
                    text-white
                    shadow-lg
                    shadow-orange-500/20
                    transition
                    hover:bg-orange-600
                  "
                >
                  Shop Offers

                  <FaArrowRight
                    className="
                      transition
                      group-hover:translate-x-1
                    "
                  />
                </Link>

                <Link
                  to="/register"
                  className="
                    inline-flex
                    items-center
                    gap-2
                    rounded-xl
                    border
                    border-white/40
                    bg-white/10
                    px-7
                    py-4
                    font-bold
                    text-white
                    backdrop-blur
                    transition
                    hover:bg-white
                    hover:text-blue-700
                  "
                >
                  Become a Seller
                </Link>

              </div>

              {/* Trust message */}

              <div
                className="
                  mt-7
                  flex
                  items-center
                  gap-2
                  text-sm
                  text-blue-100
                "
              >
                <FaCheckCircle className="text-orange-400" />

                Trusted marketplace opportunities
              </div>

            </div>

            {/* ==================================
                RIGHT VISUAL
            ================================== */}

            <div
              className="
                relative
                flex
                justify-center
              "
            >

              {/* Orange glow */}

              <div
                className="
                  absolute
                  h-72
                  w-72
                  rounded-full
                  bg-orange-500/20
                  blur-3xl
                "
              />

              <div
                className="
                  relative
                  w-full
                  max-w-lg
                "
              >

                <img
                  src="/images/offers/shopping-offer.png"
                  alt="MUHUZE special offers"
                  className="
                    relative
                    z-10
                    w-full
                    drop-shadow-2xl
                  "
                />

              </div>

            </div>

          </div>

        </div>

      </div>
    </section>
  );
}