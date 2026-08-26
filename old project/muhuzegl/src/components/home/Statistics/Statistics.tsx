import StatCard from "./StatCard";
import { statistics } from "./statisticsData";

export default function Statistics() {
  return (
    <section className="py-24 bg-slate-50">

      <div className="max-w-7xl mx-auto px-6">

        <div className="text-center">

          <h2 className="text-4xl font-bold">
            MUHUZE Marketplace in Numbers
          </h2>

          <p className="text-gray-500 mt-4">
            Growing every day with trusted buyers and sellers.
          </p>

        </div>

        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8 mt-16">

          {statistics.map((statistic) => (
            <StatCard
              key={statistic.id}
              statistic={statistic}
            />
          ))}

        </div>

      </div>

    </section>
  );
}