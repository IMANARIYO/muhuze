import type { MarketplaceItemType } from "../../../types/marketplaceItem";

interface Props {
  value: MarketplaceItemType;
  onChange: (type: MarketplaceItemType) => void;
}

export default function MarketplaceTypeSelector({
  value,
  onChange,
}: Props) {
  const types: MarketplaceItemType[] = [
    "product",
    "rental",
    "service",
    "job",
  ];

  return (
    <div className="space-y-3">

      <label className="block font-semibold text-gray-700">
        Marketplace Type
      </label>

      <div className="grid grid-cols-2 gap-4">

        {types.map((type) => (
          <button
            key={type}
            type="button"
            onClick={() => onChange(type)}
            className={`
              rounded-xl
              border
              p-4
              capitalize
              transition
              ${
                value === type
                  ? "bg-blue-600 text-white border-blue-600"
                  : "bg-white hover:bg-gray-100"
              }
            `}
          >
            {type}
          </button>
        ))}

      </div>

    </div>
  );
}