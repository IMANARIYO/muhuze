import type {
  MarketplaceItem,
} from "../../../types/marketplaceItem";

import MarketplaceCard from "../MarketplaceCard";

interface Props {
  items: MarketplaceItem[];
}

export default function MarketplaceGrid({
  items,
}: Props) {
  /*
   * Protect the marketplace grid from invalid
   * or deleted marketplace items returned
   * from the backend.
   */
  const validItems = items.filter(
    (item): item is MarketplaceItem =>
      item !== null &&
      item !== undefined &&
      typeof item._id === "string"
  );

  return (
    <div
      className="
        grid
        grid-cols-1
        sm:grid-cols-2
        lg:grid-cols-3
        xl:grid-cols-4
        gap-6
      "
    >
      {validItems.map((item) => (
        <MarketplaceCard
          key={item._id}
          item={item}
        />
      ))}
    </div>
  );
}