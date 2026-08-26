import type { Statistic } from "./types";

interface Props {
  statistic: Statistic;
}

export default function StatCard({ statistic }: Props) {
  return (
    <div className="bg-white rounded-2xl shadow-lg p-8 text-center hover:-translate-y-2 hover:shadow-xl transition duration-300">

      <h3 className={`text-5xl font-bold ${statistic.color}`}>
        {statistic.value}
      </h3>

      <p className="mt-4 text-gray-600 text-lg">
        {statistic.label}
      </p>

    </div>
  );
}