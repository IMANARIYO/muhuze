import { useState } from "react";

import {
  FaGlobeAfrica,
} from "react-icons/fa";

export default function HeroImage() {
  const [imageError, setImageError] = useState(false);

  return (
    <div className="relative z-10">

      {/* Main Marketplace Visual */}

      <div
        className="
          relative
          overflow-hidden
          rounded-[2rem]
          border
          border-white
          bg-white
          p-3
          shadow-2xl
          shadow-slate-300/50
        "
      >

        {!imageError ? (

          <img
            src="/images/hero-marketplace.png"
            alt="MUHUZE Global Link Marketplace"
            onError={() => setImageError(true)}
            className="
              h-[380px]
              w-full
              rounded-[1.5rem]
              object-cover
              object-center
              sm:h-[460px]
              lg:h-[500px]
            "
          />

        ) : (

          /* Fallback */

          <div
            className="
              flex
              h-[380px]
              flex-col
              items-center
              justify-center
              rounded-[1.5rem]
              bg-gradient-to-br
              from-blue-600
              via-blue-700
              to-slate-950
              px-8
              text-center
              text-white
              sm:h-[460px]
              lg:h-[500px]
            "
          >

            <div
              className="
                flex
                h-20
                w-20
                items-center
                justify-center
                rounded-3xl
                bg-white/10
                text-4xl
                backdrop-blur
              "
            >
              <FaGlobeAfrica />
            </div>

            <h2 className="mt-6 text-3xl font-extrabold">
              MUHUZE
            </h2>

            <p className="mt-2 max-w-sm text-blue-100">
              Your global link to products,
              businesses and opportunities.
            </p>

          </div>

        )}

      </div>

    </div>
  );
}