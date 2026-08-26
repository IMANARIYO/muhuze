import type { MarketplaceItem } from "../../../types/marketplaceItem";

export default function MarketplaceSeller({
  item,
}: {
  item: MarketplaceItem;
}) {
  const seller =
    typeof item.sellerId === "string"
      ? null
      : item.sellerId;

  return (
    <section className="mt-12 rounded-3xl border p-6 bg-white">

      <h2 className="text-2xl font-bold mb-8">
        Seller Information
      </h2>

      <div className="flex items-center gap-6">

        <div
          className="
            w-20
            h-20
            rounded-full
            bg-blue-100
            flex
            items-center
            justify-center
            text-3xl
            font-bold
            text-blue-700
          "
        >
          {seller
            ? seller.fullName.charAt(0).toUpperCase()
            : "S"}
        </div>

        <div>

          <h3 className="text-xl font-semibold">
            {seller
              ? seller.fullName
              : `Seller #${item.sellerId}`}
          </h3>

          <p className="text-gray-500">
            {seller
              ? seller.email
              : "MUHUZE Marketplace Seller"}
          </p>

          {seller && (
            <p className="text-gray-500">
              {seller.phone}
            </p>
          )}

        </div>

      </div>

      <div className="grid md:grid-cols-2 gap-6 mt-8">

        <div>
          <h4 className="font-semibold">
            Verified
          </h4>

          <p>
            {item.verified
              ? "✅ Verified Seller"
              : "❌ Not Verified"}
          </p>
        </div>

        <div>
          <h4 className="font-semibold">
            Rating
          </h4>

          <p>
            ⭐ {item.rating}
          </p>
        </div>

        <div>
          <h4 className="font-semibold">
            Reviews
          </h4>

          <p>
            {item.reviews}
          </p>
        </div>

        <div>
          <h4 className="font-semibold">
            Status
          </h4>

          <p className="capitalize">
            {item.status}
          </p>
        </div>

      </div>

    </section>
  );
}