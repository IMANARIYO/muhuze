import PartnerCard from "./PartnerCard";
import { partners } from "./partnerData";

export default function Partners() {
  return (
    <section className="py-24 bg-white">

      <div className="max-w-7xl mx-auto px-6">

        <div className="text-center">

          <h2 className="text-4xl font-bold">
            Trusted Partners
          </h2>

          <p className="mt-4 text-gray-600">
            Working together with trusted organizations to build a secure marketplace.
          </p>

        </div>

        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-8 mt-16">

          {partners.map((partner) => (
            <PartnerCard
              key={partner.id}
              partner={partner}
            />
          ))}

        </div>

      </div>

    </section>
  );
}