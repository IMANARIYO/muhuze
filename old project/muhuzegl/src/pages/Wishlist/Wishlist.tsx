import Container from "../../components/ui/Container";
import SectionTitle from "../../components/ui/SectionTitle";
import MarketplaceGrid from "../../components/marketplace/MarketplaceGrid";

import { useWishlist } from "../../context/WishlistContext";

export default function Wishlist() {
  const { wishlist } = useWishlist();

  return (
    <section className="py-16">
      <Container>

        <SectionTitle
          title="My Wishlist"
          subtitle="Marketplace listings you've saved for later."
        />

        {wishlist.length === 0 ? (
          <div className="text-center mt-20">

            <h2 className="text-2xl font-bold">
              Your Wishlist is Empty
            </h2>

            <p className="text-gray-500 mt-3">
              Save marketplace listings by clicking the ❤️ button.
            </p>

          </div>
        ) : (
          <MarketplaceGrid items={wishlist} />
        )}

      </Container>
    </section>
  );
}