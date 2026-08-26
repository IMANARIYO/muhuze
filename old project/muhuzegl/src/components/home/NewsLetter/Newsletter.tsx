import { useState } from "react";

import {
  FaPaperPlane,
  FaCheckCircle,
  FaEnvelope,
} from "react-icons/fa";

import Container from "../../ui/Container";
import { useToast } from "../../ui/Toast";

export default function Newsletter() {
  const [email, setEmail] = useState("");

  const { showToast } = useToast();

  const handleSubscribe = () => {
    if (!email.trim()) {
      showToast(
        "Please enter your email.",
        "warning"
      );

      return;
    }

    showToast(
      "Thank you for subscribing!",
      "success"
    );

    setEmail("");
  };

  return (
    <section
      className="
        bg-white
        py-12
        lg:py-16
      "
    >
      <Container>

        {/* ======================================
            NEWSLETTER CONTAINER
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
              -left-24
              -top-24
              h-72
              w-72
              rounded-full
              bg-white/10
            "
          />

          <div
            className="
              absolute
              -bottom-32
              -right-24
              h-96
              w-96
              rounded-full
              bg-orange-500/10
            "
          />

          <div
            className="
              absolute
              right-1/3
              top-1/2
              h-48
              w-48
              -translate-y-1/2
              rounded-full
              bg-blue-400/10
              blur-3xl
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
                LEFT
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
                  border-white/20
                  bg-white/10
                  px-4
                  py-2
                  text-sm
                  font-semibold
                  text-white
                  backdrop-blur
                "
              >
                <FaEnvelope className="text-orange-400" />

                Stay Connected
              </div>

              {/* Heading */}

              <h2
                className="
                  mt-7
                  text-4xl
                  font-extrabold
                  leading-tight
                  text-white
                  sm:text-5xl
                  lg:text-6xl
                "
              >
                Stay Connected

                <span
                  className="
                    block
                    text-orange-400
                  "
                >
                  with MUHUZE
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
                Receive marketplace updates,
                exclusive offers, seller opportunities
                and useful information directly in
                your inbox.
              </p>

              {/* ==================================
                  FORM
              ================================== */}

              <div
                className="
                  mt-8
                  flex
                  flex-col
                  gap-3
                  sm:flex-row
                "
              >

                <input
                  type="email"
                  placeholder="Enter your email address..."
                  value={email}
                  onChange={(event) =>
                    setEmail(event.target.value)
                  }
                  className="
                    h-14
                    flex-1
                    rounded-xl
                    border
                    border-white/20
                    bg-white
                    px-5
                    text-slate-900
                    outline-none
                    placeholder:text-slate-400
                    focus:ring-2
                    focus:ring-orange-400
                  "
                />

                <button
  type="button"
  onClick={handleSubscribe}
  className="
    h-14
    rounded-xl
    bg-orange-500
    px-7
    font-bold
    text-white
    transition
    hover:bg-orange-600
    flex
    items-center
    justify-center
    gap-2
  "
>
  <FaPaperPlane />
  Subscribe
</button>

              </div>

              {/* ==================================
                  BENEFITS
              ================================== */}

              <div
                className="
                  mt-8
                  grid
                  gap-4
                  sm:grid-cols-2
                "
              >

                <div
                  className="
                    flex
                    items-center
                    gap-3
                    text-sm
                    text-white
                  "
                >
                  <FaCheckCircle className="text-orange-400" />

                  Weekly Updates
                </div>

                <div
                  className="
                    flex
                    items-center
                    gap-3
                    text-sm
                    text-white
                  "
                >
                  <FaCheckCircle className="text-orange-400" />

                  Exclusive Deals
                </div>

                <div
                  className="
                    flex
                    items-center
                    gap-3
                    text-sm
                    text-white
                  "
                >
                  <FaCheckCircle className="text-orange-400" />

                  No Spam
                </div>

                <div
                  className="
                    flex
                    items-center
                    gap-3
                    text-sm
                    text-white
                  "
                >
                  <FaCheckCircle className="text-orange-400" />

                  Unsubscribe Anytime
                </div>

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
                  max-w-md
                "
              >

                <img
                  src="/images/newsletter/newsletter-banner.png"
                  alt="Stay connected with MUHUZE"
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

      </Container>
    </section>
  );
}