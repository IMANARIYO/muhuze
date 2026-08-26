import {
  FaMapMarkerAlt,
  FaStar,
} from "react-icons/fa";

import type { Seller } from "./types";

interface Props {
  seller: Seller;
}

export default function SellerCard({
  seller,
}: Props) {
  const Badge = seller.badge;

  return (
    <div
      className="
        group
        relative
        overflow-hidden
        rounded-3xl
        border
        border-slate-100
        bg-white
        p-7
        text-center
        shadow-sm
        transition-all
        duration-300
        hover:-translate-y-1
        hover:shadow-xl
      "
    >

      {/* ======================================
          DECORATIVE ACCENT
      ====================================== */}

      <div
        className="
          absolute
          -right-12
          -top-12
          h-28
          w-28
          rounded-full
          bg-orange-100
          transition
          duration-300
          group-hover:scale-125
        "
      />

      {/* ======================================
          SELLER AVATAR
      ====================================== */}

      <div className="relative mx-auto w-fit">

        <div
          className="
            rounded-full
            border-4
            border-blue-100
            p-1
            transition
            duration-300
            group-hover:border-orange-200
          "
        >
          <img
            src={seller.avatar}
            alt={seller.name}
            className="
              h-24
              w-24
              rounded-full
              object-cover
            "
          />
        </div>

        {/* Verified Badge */}

        {seller.verified && (
          <div
            className="
              absolute
              bottom-0
              right-0
              flex
              h-8
              w-8
              items-center
              justify-center
              rounded-full
              border-2
              border-white
              bg-blue-600
              text-white
              shadow-md
            "
          >
            <Badge className="text-sm" />
          </div>
        )}

      </div>

      {/* ======================================
          SELLER NAME
      ====================================== */}

      <div
        className="
          relative
          mt-5
          flex
          items-center
          justify-center
          gap-2
        "
      >
        <h3
          className="
            text-xl
            font-bold
            text-slate-950
          "
        >
          {seller.name}
        </h3>
      </div>

      {/* ======================================
          LOCATION
      ====================================== */}

      <div
        className="
          mt-3
          flex
          items-center
          justify-center
          gap-2
          text-sm
          text-slate-500
        "
      >
        <FaMapMarkerAlt className="text-blue-600" />

        {seller.location}
      </div>

      {/* ======================================
          RATING
      ====================================== */}

      <div
        className="
          mt-4
          flex
          items-center
          justify-center
          gap-2
        "
      >
        <FaStar className="text-orange-500" />

        <span className="font-bold text-slate-900">
          {seller.rating.toFixed(1)}
        </span>

        <span className="text-sm text-slate-400">
          rating
        </span>
      </div>

      {/* ======================================
          PRODUCTS
      ====================================== */}

      <div
        className="
          mx-auto
          mt-5
          inline-flex
          rounded-full
          bg-blue-50
          px-4
          py-2
          text-sm
          font-semibold
          text-blue-700
        "
      >
        {seller.products} Products
      </div>

      {/* ======================================
          BOTTOM ACCENT
      ====================================== */}

      <div
        className="
          mx-auto
          mt-6
          h-1
          w-10
          rounded-full
          bg-orange-500
          transition-all
          duration-300
          group-hover:w-16
        "
      />

    </div>
  );
}