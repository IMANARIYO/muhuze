import Container from "../../ui/Container";
import SectionTitle from "../../ui/SectionTitle";

import {
  marketplaceCategoryGroups,
} from "../../../data/marketplaceCategories";

import { Link } from "react-router-dom";

export default function MarketplaceCategories() {
  return (
    <section className="py-16">
      <Container>

        <SectionTitle
          title="Browse Categories"
          subtitle="Find products, rentals, services and jobs by category."
        />

        <div className="space-y-12 mt-10">

          {marketplaceCategoryGroups.map(
            (group) => (
              <div key={group.type}>

                {/* Marketplace Type */}

                <h2 className="text-2xl font-bold mb-6">
                  {group.name}
                </h2>

                {/* Categories */}

                <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-6">

                  {group.categories.map(
                    (category) => (

                      <Link
                        key={`${group.type}-${category.id}`}
                        to={`/marketplace/category/${category.id}`}
                        className="
                          rounded-2xl
                          border
                          p-6
                          bg-white
                          hover:shadow-lg
                          transition
                          text-center
                          block
                        "
                      >

                        <h3 className="font-semibold">
                          {category.name}
                        </h3>

                      </Link>

                    )
                  )}

                </div>

              </div>
            )
          )}

        </div>

      </Container>
    </section>
  );
}