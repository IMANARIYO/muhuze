import { useParams } from "react-router-dom";

import Container from "../../components/ui/Container";

import MarketplaceImageGallery from "../../components/marketplace/MarketplaceImageGallery";
import MarketplaceInfo from "../../components/marketplace/MarketplaceInfo";

import { useMarketplace } from "../../context/MarketplaceContext";
import MarketplaceSeller from "../../components/marketplace/MarketplaceSeller";
import MarketplaceContact from "../../components/marketplace/MarketplaceContact";
import RelatedListings from "../../components/marketplace/RelatedListings";
import MarketplaceDynamicDetails from "../../components/marketplace/MarketplaceDynamicDetails";

export default function MarketplaceDetails() {

  const { id } = useParams();

  const { items } = useMarketplace();

  const item = items.find(
    (item) => item._id ===(id)
  );

  if (!item) {

    return (
      <Container>

        <h2 className="text-3xl font-bold">

          Listing Not Found

        </h2>

      </Container>
    );

  }

  return (
<section className="py-16">
  <Container>

    {/* Top Section */}
    <div className="grid lg:grid-cols-2 gap-12">

      <MarketplaceImageGallery
        item={item}
      />

      <MarketplaceInfo
        item={item}
      />

    </div>

    {/* Full Width Sections */}

    <MarketplaceDynamicDetails
      item={item}
    />

    <MarketplaceSeller
      item={item}
    />

    <MarketplaceContact
      sellerId={item.sellerId}
    />

    <RelatedListings
      item={item}
    />

  </Container>
</section>
  );
}