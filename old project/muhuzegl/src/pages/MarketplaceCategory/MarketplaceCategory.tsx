import { useParams } from "react-router-dom";

import Container from "../../components/ui/Container";
import SectionTitle from "../../components/ui/SectionTitle";

import {
  marketplaceCategoryGroups,
} from "../../data/marketplaceCategories";

import MarketplaceSubCategories from "../../components/marketplace/MarketplaceSubCategories";

export default function MarketplaceCategory() {
  const { categoryId } = useParams();

  /*
   * Search through all marketplace types
   * to find the requested category.
   */
  let category = null;

  for (const group of marketplaceCategoryGroups) {
    const foundCategory = group.categories.find(
      (item) => item.id === categoryId
    );

    if (foundCategory) {
      category = foundCategory;
      break;
    }
  }

  /*
   * If the category does not exist,
   * show the "Category Not Found" page.
   */
  if (!category) {
    return (
      <Container>
        <SectionTitle
          title="Category Not Found"
          subtitle="The category you requested does not exist."
        />
      </Container>
    );
  }

  return (
    <Container>
      <SectionTitle
        title={category.name}
        subtitle={`Browse everything in ${category.name}.`}
      />

      <MarketplaceSubCategories
        categoryId={category.id}
        categoryName={category.name}
        subCategories={category.subCategories}
      />
    </Container>
  );
}