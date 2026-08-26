import type { AppFeature } from "./types";
interface Props {
  feature: AppFeature;
}

export default function FeatureItem({ feature }: Props) {
  const Icon = feature.icon;

  return (
    <div className="flex items-center gap-4">
      <div className="bg-blue-100 text-blue-600 p-3 rounded-full">
        <Icon size={22} />
      </div>

      <span>{feature.title}</span>
    </div>
  );
}