import {
  FaFacebook,
  FaInstagram,
  FaLinkedin,
  FaYoutube,
  FaXTwitter,
  FaGooglePlay,
  FaApple,
} from "react-icons/fa6";

import FooterColumn from "./FooterColumn";
import { footerSections } from "./footerData";

export default function Footer() {
  return (
    <footer className="bg-slate-950 text-white">

      <div className="mx-auto max-w-7xl px-6 py-16 lg:py-20">

        {/* ======================================
            TOP FOOTER
        ====================================== */}

        <div className="grid gap-12 lg:grid-cols-4">

          {/* ====================================
              COMPANY
          ==================================== */}

          <div>

            <div className="flex items-center gap-3">

              <div
                className="
                  flex
                  h-12
                  w-12
                  items-center
                  justify-center
                  rounded-xl
                  bg-blue-600
                  text-2xl
                  font-extrabold
                "
              >
                M
              </div>

              <div>
                <h2 className="text-3xl font-extrabold">
                  MUHUZE
                </h2>

                <p className="text-sm text-slate-400">
                  Global Link Marketplace
                </p>
              </div>

            </div>

            <p
              className="
                mt-4
                font-semibold
                text-orange-400
              "
            >
              Buy • Sell • Grow
            </p>

            <p
              className="
                mt-5
                leading-7
                text-slate-400
              "
            >
              MUHUZE is a digital marketplace connecting
              buyers and sellers through a secure, reliable
              and modern commerce experience across Africa
              and beyond.
            </p>

            {/* ==================================
                SOCIAL LINKS
            ================================== */}

            <div className="mt-7 flex gap-3">

              {[
                FaFacebook,
                FaInstagram,
                FaLinkedin,
                FaYoutube,
                FaXTwitter,
              ].map((Icon, index) => (

                <a
                  key={index}
                  href="#"
                  aria-label="Social media"
                  className="
                    flex
                    h-10
                    w-10
                    items-center
                    justify-center
                    rounded-full
                    bg-slate-800
                    text-slate-300
                    transition-all
                    duration-300
                    hover:bg-blue-600
                    hover:text-white
                  "
                >
                  <Icon />
                </a>

              ))}

            </div>

          </div>

          {/* ======================================
              FOOTER COLUMNS
          ====================================== */}

          {footerSections.map((section) => (
            <FooterColumn
              key={section.title}
              section={section}
            />
          ))}

        </div>

        {/* ======================================
            APP + PAYMENT AREA
        ====================================== */}

        <div
          className="
            mt-16
            border-t
            border-slate-800
            pt-12
          "
        >

          <div
            className="
              flex
              flex-col
              gap-12
              lg:flex-row
              lg:items-center
              lg:justify-between
            "
          >

            {/* APP */}

            <div>

              <h3 className="text-xl font-bold">
                Download MUHUZE App
              </h3>

              <p className="mt-2 text-slate-400">
                Shop anywhere, anytime with MUHUZE Global ink.
              </p>

              <div className="mt-5 flex flex-wrap gap-3">

                <button
                  type="button"
                  className="
                    flex
                    items-center
                    gap-3
                    rounded-xl
                    bg-white
                    px-5
                    py-3
                    font-semibold
                    text-slate-900
                    transition
                    hover:bg-slate-200
                  "
                >
                  <FaGooglePlay className="text-lg" />

                  Google Play
                </button>

                <button
                  type="button"
                  className="
                    flex
                    items-center
                    gap-3
                    rounded-xl
                    border
                    border-slate-700
                    bg-slate-900
                    px-5
                    py-3
                    font-semibold
                    text-white
                    transition
                    hover:border-blue-500
                  "
                >
                  <FaApple className="text-lg" />

                  App Store
                </button>

              </div>

            </div>

            {/* ==================================
                PAYMENTS
            ================================== */}

            <div>

              <h3 className="text-center text-xl font-bold lg:text-right">
                Accepted Payments
              </h3>

              <div className="mt-5 flex flex-wrap justify-center gap-3 lg:justify-end">

                <span
                  className="
                    rounded-lg
                    bg-yellow-400
                    px-4
                    py-2
                    font-semibold
                    text-black
                  "
                >
                  MTN MoMo
                </span>

                <span
                  className="
                    rounded-lg
                    bg-red-500
                    px-4
                    py-2
                    font-semibold
                    text-white
                  "
                >
                  Airtel Money
                </span>

                <span
                  className="
                    rounded-lg
                    bg-blue-600
                    px-4
                    py-2
                    font-semibold
                    text-white
                  "
                >
                  Visa
                </span>

                <span
                  className="
                    rounded-lg
                    bg-slate-700
                    px-4
                    py-2
                    font-semibold
                    text-white
                  "
                >
                  Mastercard
                </span>

              </div>

            </div>

          </div>

        </div>

        {/* ======================================
            BOTTOM FOOTER
        ====================================== */}

        <div
          className="
            mt-12
            border-t
            border-slate-800
            pt-8
            text-center
          "
        >

          <p className="text-sm text-slate-400">

            © 2026{" "}

            <span className="font-semibold text-white">
              MUHUZE GLOBAL LINK
            </span>

          </p>

          <p className="mt-2 text-sm text-slate-500">
            Connecting people, businesses and opportunities.
          </p>

        </div>

      </div>

    </footer>
  );
}