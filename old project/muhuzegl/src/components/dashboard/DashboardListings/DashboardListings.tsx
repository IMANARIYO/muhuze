
import { useAuth } from "../../../context/AuthContext";
import { useMarketplace } from "../../../context/MarketplaceContext";
import MarketplaceGrid from "../../marketplace/MarketplaceGrid";
import SectionTitle from "../../ui/SectionTitle";

export default function DashboardListings() {
  const { items } = useMarketplace();

  const { currentUser } = useAuth();

  const myListings = items.filter(
    (item) => item.sellerId === currentUser?._id
  );

  return (
    <section className="mt-12">
      <SectionTitle
        title="My Listings"
        subtitle="Manage everything you have published."
      />

      <MarketplaceGrid items={myListings} />
    </section>
  );
}