import SellerCard from "./SellerCard";
import { sellers } from "./sellerData";

export default function FeaturedSellers() {
  return (
    <section className="py-20 bg-gray-100">

      <div className="max-w-7xl mx-auto px-6">

        <div className="text-center">

          <h2 className="text-4xl font-bold">
            Featured Sellers
          </h2>

          <p className="mt-4 text-gray-600">
            Shop from trusted and verified sellers across Rwanda.
          </p>

        </div>

        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8 mt-12">

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