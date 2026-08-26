import { Link } from "react-router-dom";

import Container from "../../ui/Container";

import type {
  MarketplaceSubCategory,
} from "../../../data/marketplaceCategories";

interface Props {
  categoryId: string;
  categoryName: string;
  subCategories: MarketplaceSubCategory[];
}

export default function MarketplaceSubCategories({
  categoryId,
  categoryName,
  subCategories,
}: Props) {
  return (
    <section className="py-8">
      <Container>

        {/* =========================
            TITLE
        ========================= */}

        <h2 className="mb-6 text-2xl font-bold">
          {categoryName} Subcategories
        </h2>

        {/* =========================
            SUBCATEGORIES
        ========================= */}

        <div className="flex flex-wrap gap-4">

          {subCategories.map((subCategory) => (

            <Link
              key={subCategory.id}
              to={`/marketplace?category=${encodeURIComponent(
                categoryId
              )}&subCategory=${encodeURIComponent(
                subCategory.id
              )}`}
              className="
                rounded-full
                border
                border-gray-200
                bg-white
                px-5
                py-2
                font-medium
                text-gray-700
                transition-all
                duration-200
                hover:border-blue-600
                hover:bg-blue-600
                hover:text-white
                hover:shadow-md
              "
            >
              {subCategory.name}
            </Link>

          ))}

        </div>

      </Container>
    </section>
  );
}