import MarketplaceGrid from "../MarketplaceGrid";

import { useMarketplace } from "../../../context/MarketplaceContext";

import type { MarketplaceItem } from "../../../types/marketplaceItem";

interface Props {
  item: MarketplaceItem;
}

export default function RelatedListings({
  item,
}: Props) {

  const { items } = useMarketplace();

  const relatedItems = items.filter(
    (listing) =>
      listing.category === item.category &&
      listing._id !== item._id
  );

  return (
    <section className="mt-12">

      <h2 className="text-2xl font-bold mb-6">
        Related Listings
      </h2>

      {relatedItems.length === 0 ? (
        <p className="text-gray-500">
          No related listings found.
        </p>
      ) : (
        <MarketplaceGrid
          items={relatedItems}
        />
      )}

    </section>
  );
}