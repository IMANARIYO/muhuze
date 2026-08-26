import {
  FaQuoteLeft,
  FaStar,
} from "react-icons/fa";

import type { Testimonial } from "./types";

interface Props {
  testimonial: Testimonial;
}

export default function TestimonialCard({
  testimonial,
}: Props) {
  return (
    <article
      className="
        group
        relative
        overflow-hidden
        rounded-3xl
        border
        border-slate-100
        bg-white
        p-7
        shadow-sm
        transition-all
        duration-300
        hover:-translate-y-1
        hover:shadow-xl
      "
    >

      {/* ======================================
          ORANGE DECORATIVE ACCENT
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
          QUOTE ICON
      ====================================== */}

      <div
        className="
          relative
          flex
          h-11
          w-11
          items-center
          justify-center
          rounded-xl
          bg-blue-50
          text-blue-600
        "
      >
        <FaQuoteLeft />
      </div>

      {/* ======================================
          COMMENT
      ====================================== */}

      <p
        className="
          relative
          mt-6
          min-h-[140px]
          text-base
          leading-7
          text-slate-600
        "
      >
        "{testimonial.comment}"
      </p>

      {/* ======================================
          RATING
      ====================================== */}

      <div
        className="
          mt-5
          flex
          items-center
          gap-1
          text-orange-500
        "
      >
        {Array.from({
          length: testimonial.rating,
        }).map((_, index) => (
          <FaStar key={index} />
        ))}
      </div>

      {/* ======================================
          USER
      ====================================== */}

      <div
        className="
          mt-6
          flex
          items-center
          gap-4
          border-t
          border-slate-100
          pt-6
        "
      >

        <img
          src={testimonial.image}
          alt={testimonial.name}
          className="
            h-14
            w-14
            rounded-full
            border-2
            border-blue-100
            object-cover
            transition
            group-hover:border-orange-200
          "
        />

        <div>

          <h3
            className="
              font-bold
              text-slate-950
            "
          >
            {testimonial.name}
          </h3>

          <p
            className="
              mt-1
              text-sm
              font-medium
              text-blue-600
            "
          >
            {testimonial.role}
          </p>

        </div>

      </div>

      {/* ======================================
          BOTTOM ACCENT
      ====================================== */}

      <div
        className="
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

    </article>
  );
}