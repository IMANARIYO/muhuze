import WhyChooseCard from "./WhyChooseCard";
import { whyChooseItems } from "./whyChooseData";

export default function WhyChoose() {
  return (
    <section
      className="
        bg-slate-50
        py-16
        lg:py-20
      "
    >
      <div className="mx-auto max-w-7xl px-6">

        {/* ======================================
            SECTION HEADER
        ====================================== */}

        <div className="mx-auto max-w-3xl text-center">

          <span
            className="
              font-semibold
              uppercase
              tracking-[0.2em]
              text-blue-600
            "
          >
            Why Choose MUHUZE
          </span>

          <h2
            className="
              mt-4
              text-4xl
              font-extrabold
              tracking-tight
              text-slate-950
              lg:text-5xl
            "
          >
            A Marketplace Built
            <span className="text-orange-500">
              {" "}for Trust
            </span>
          </h2>

          <p
            className="
              mt-5
              text-lg
              leading-8
              text-slate-600
            "
          >
            We connect buyers and sellers through a
            secure, reliable and modern marketplace
            experience.
          </p>

        </div>

        {/* ======================================
            TRUST FEATURES
        ====================================== */}

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
          {whyChooseItems.map((item) => (
            <WhyChooseCard
              key={item.id}
              item={item}
            />
          ))}
        </div>

      </div>
    </section>
  );
}