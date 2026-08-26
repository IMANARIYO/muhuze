import SellerCard from "./SellerCard";
import { sellers } from "./sellerData";

export default function TopSellers() {
  return (
    <section
      className="
        bg-white
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
            Trusted Sellers
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
            Meet Our
            <span className="text-orange-500">
              {" "}Top Sellers
            </span>
          </h2>

          <p
            className="
              mx-auto
              mt-5
              max-w-2xl
              text-lg
              leading-8
              text-slate-600
            "
          >
            Shop confidently from highly rated
            sellers building trusted businesses
            on MUHUZE.
          </p>

        </div>

        {/* ======================================
            SELLERS
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
          {sellers.map((seller) => (
            <SellerCard
              key={seller.id}
              seller={seller}
            />
          ))}
        </div>

      </div>
    </section>
  );
}