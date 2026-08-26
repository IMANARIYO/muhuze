import TrendingProductCard from "./TrendingProductCard";
import { trendingProducts } from "./trendingData";

export default function TrendingProducts() {
  return (
    <section className="py-24 bg-white">

      <div className="max-w-7xl mx-auto px-6">

        <div className="text-center">

          <h2 className="text-4xl font-bold">

            🔥 Trending Products

          </h2>

          <p className="mt-4 text-gray-500">

            Most popular products this week.

          </p>

        </div>

        <div className="grid lg:grid-cols-4 md:grid-cols-2 gap-8 mt-14">

          {trendingProducts.map((product) => (
            <TrendingProductCard
              key={product.id}
              product={product}
            />
          ))}

        </div>

      </div>

    </section>
  );
}