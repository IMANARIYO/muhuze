import type { Feature } from "./types";

interface Props {
  feature: Feature;
}

export default function FeatureCard({ feature }: Props) {
  const Icon = feature.icon;

  return (
    <div className="bg-white rounded-2xl shadow-lg p-8 text-center hover:-translate-y-2 hover:shadow-2xl transition duration-300">

      <div className="flex justify-center mb-6">
        <div className="bg-blue-100 text-blue-600 p-5 rounded-full">
          <Icon size={34} />
        </div>
      </div>

      <h3 className="text-xl font-bold">
        {feature.title}
      </h3>

      <p className="mt-4 text-gray-600 leading-7">
        {feature.description}
      </p>

    </div>
  );
}