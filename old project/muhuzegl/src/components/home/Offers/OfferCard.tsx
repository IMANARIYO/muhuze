import { Link } from "react-router-dom";

import {
  FaArrowRight,
  FaBolt,
} from "react-icons/fa";

import type { Offer } from "./types";

interface Props {
  offer: Offer;
}

export default function OfferCard({
  offer,
}: Props) {
  return (
    <div
      className="
        group
        rounded-2xl
        bg-gradient-to-br
        from-blue-600
        to-blue-800
        p-7
        text-white
        shadow-lg
        transition
        duration-300
        hover:-translate-y-1
        hover:shadow-2xl
      "
    >

      <div
        className="
          inline-flex
          items-center
          gap-2
          rounded-full
          bg-orange-500
          px-3
          py-1
          text-xs
          font-bold
        "
      >
        <FaBolt />

        SPECIAL OFFER
      </div>

      <h3
        className="
          mt-5
          text-2xl
          font-bold
        "
      >
        {offer.title}
      </h3>

      <p
        className="
          mt-3
          text-blue-100
        "
      >
        {offer.description}
      </p>

      <h4
        className="
          mt-5
          text-3xl
          font-extrabold
          text-orange-400
        "
      >
        {offer.discount}
      </h4>

      <Link
        to="/products"
        className="
          mt-7
          inline-flex
          items-center
          gap-2
          rounded-xl
          bg-white
          px-6
          py-3
          font-semibold
          text-blue-700
          transition
          hover:bg-orange-500
          hover:text-white
        "
      >
        {offer.button}

        <FaArrowRight />
      </Link>

    </div>
  );
}