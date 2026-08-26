import { useMemo, useState } from "react";
import { useSearchParams } from "react-router-dom";

import Container from "../../components/ui/Container";
import SectionTitle from "../../components/ui/SectionTitle";
import MarketplaceGrid from "../../components/marketplace/MarketplaceGrid";

import { useMarketplace } from "../../context/MarketplaceContext";

import {
  marketplaceCategoryGroups,
} from "../../data/marketplaceCategories";

type MarketplaceFilter =
  | "all"
  | "product"
  | "rental"
  | "service"
  | "job";

export default function Marketplace() {
  const { items } = useMarketplace();

  /*
   * ==========================================
   * READ URL PARAMETERS
   *
   * Example:
   * /marketplace?category=electronics
   *
   * or:
   * /marketplace?category=electronics&subCategory=mobile-phones
   * ==========================================
   */

  const [searchParams] = useSearchParams();

  const categoryId = searchParams.get("category");
  const subCategoryId = searchParams.get("subCategory");

  /*
   * ==========================================
   * MARKETPLACE TYPE FILTER
   * ==========================================
   */

  const [activeFilter, setActiveFilter] =
    useState<MarketplaceFilter>("all");

  /*
   * ==========================================
   * FIND SELECTED MAIN CATEGORY
   * ==========================================
   */

  const selectedCategory = useMemo(() => {
    if (!categoryId) {
      return null;
    }

    for (const group of marketplaceCategoryGroups) {
      const foundCategory = group.categories.find(
        (category) =>
          category.id === categoryId
      );

      if (foundCategory) {
        return foundCategory;
      }
    }

    return null;
  }, [categoryId]);

  /*
   * ==========================================
   * FIND SELECTED SUBCATEGORY
   * ==========================================
   */

  const selectedSubCategory = useMemo(() => {
    if (
      !selectedCategory ||
      !subCategoryId
    ) {
      return null;
    }

    return (
      selectedCategory.subCategories.find(
        (subCategory) =>
          subCategory.id === subCategoryId
      ) ?? null
    );
  }, [
    selectedCategory,
    subCategoryId,
  ]);

  /*
   * ==========================================
   * FILTER ITEMS BY CATEGORY
   * ==========================================
   */

  const categoryFilteredItems = useMemo(() => {
    let result = items;

    /*
     * Main category
     */
    if (categoryId) {
      result = result.filter(
        (item) =>
          item.category === categoryId
      );
    }

    /*
     * Subcategory
     */
    if (subCategoryId) {
      result = result.filter(
        (item) =>
          item.subCategory ===
          subCategoryId
      );
    }

    return result;
  }, [
    items,
    categoryId,
    subCategoryId,
  ]);

  /*
   * ==========================================
   * FILTER ITEMS BY MARKETPLACE TYPE
   * ==========================================
   */

  const filteredItems = useMemo(() => {
    if (activeFilter === "all") {
      return categoryFilteredItems;
    }

    return categoryFilteredItems.filter(
      (item) =>
        item.marketplaceItemType ===
        activeFilter
    );
  }, [
    categoryFilteredItems,
    activeFilter,
  ]);

  /*
   * ==========================================
   * COUNT MARKETPLACE TYPES
   * ==========================================
   */

  const productCount =
    categoryFilteredItems.filter(
      (item) =>
        item.marketplaceItemType ===
        "product"
    ).length;

  const rentalCount =
    categoryFilteredItems.filter(
      (item) =>
        item.marketplaceItemType ===
        "rental"
    ).length;

  const serviceCount =
    categoryFilteredItems.filter(
      (item) =>
        item.marketplaceItemType ===
        "service"
    ).length;

  const jobCount =
    categoryFilteredItems.filter(
      (item) =>
        item.marketplaceItemType ===
        "job"
    ).length;

  /*
   * ==========================================
   * MARKETPLACE FILTER BUTTONS
   * ==========================================
   */

  const filters: {
    value: MarketplaceFilter;
    label: string;
    count: number;
  }[] = [
    {
      value: "all",
      label: "All",
      count: categoryFilteredItems.length,
    },
    {
      value: "product",
      label: "Products",
      count: productCount,
    },
    {
      value: "rental",
      label: "Renting",
      count: rentalCount,
    },
    {
      value: "service",
      label: "Services",
      count: serviceCount,
    },
    {
      value: "job",
      label: "Jobs",
      count: jobCount,
    },
  ];

  /*
   * ==========================================
   * PAGE TITLE
   * ==========================================
   */

  const pageTitle =
    selectedSubCategory?.name ??
    selectedCategory?.name ??
    "Marketplace";

  /*
   * ==========================================
   * PAGE SUBTITLE
   * ==========================================
   */

  const pageSubtitle =
    selectedSubCategory
      ? `Browse ${selectedSubCategory.name} in ${selectedCategory?.name}.`
      : selectedCategory
        ? `Browse everything in ${selectedCategory.name}.`
        : "Discover products, rentals, services and jobs.";

  /*
   * ==========================================
   * CURRENT SECTION TITLE
   * ==========================================
   */

  let sectionTitle = "All Listings";

  if (selectedSubCategory) {
    sectionTitle = selectedSubCategory.name;
  } else if (selectedCategory) {
    sectionTitle = selectedCategory.name;
  } else if (activeFilter === "product") {
    sectionTitle = "Products";
  } else if (activeFilter === "rental") {
    sectionTitle = "Renting";
  } else if (activeFilter === "service") {
    sectionTitle = "Services";
  } else if (activeFilter === "job") {
    sectionTitle = "Jobs";
  }

  /*
   * ==========================================
   * RENDER
   * ==========================================
   */

  return (
    <section className="py-16">
      <Container>

        {/* =========================
            PAGE TITLE
        ========================= */}

        <SectionTitle
          title={pageTitle}
          subtitle={pageSubtitle}
        />

        {/* =========================
            MARKETPLACE FILTERS
        ========================= */}

        <div className="mt-8 mb-10">
          <div className="flex flex-wrap gap-3">

            {filters.map((filter) => {
              const isActive =
                activeFilter ===
                filter.value;

              return (
                <button
                  key={filter.value}
                  type="button"
                  onClick={() =>
                    setActiveFilter(
                      filter.value
                    )
                  }
                  className={`
                    px-5 py-3
                    rounded-xl
                    font-semibold
                    transition-all
                    duration-200
                    border
                    ${
                      isActive
                        ? "bg-blue-600 text-white border-blue-600 shadow-md"
                        : "bg-white text-gray-700 border-gray-200 hover:border-blue-500 hover:text-blue-600"
                    }
                  `}
                >
                  {filter.label}

                  <span
                    className={`
                      ml-2
                      px-2
                      py-1
                      rounded-full
                      text-xs
                      ${
                        isActive
                          ? "bg-white/20 text-white"
                          : "bg-gray-100 text-gray-600"
                      }
                    `}
                  >
                    {filter.count}
                  </span>
                </button>
              );
            })}

          </div>
        </div>

        {/* =========================
            CURRENT SECTION TITLE
        ========================= */}

        <div className="mb-6">

          <h2 className="text-2xl font-bold text-gray-900">
            {sectionTitle}
          </h2>

          <p className="text-gray-500 mt-1">
            {filteredItems.length}{" "}
            {filteredItems.length === 1
              ? "listing"
              : "listings"}{" "}
            available
          </p>

        </div>

        {/* =========================
            LISTINGS
        ========================= */}

        {filteredItems.length === 0 ? (
          <div className="text-center mt-20 py-16">

            <h2 className="text-2xl font-bold">
              No Listings Available
            </h2>

            <p className="text-gray-500 mt-3">
              There are no listings in
              this category yet.
            </p>

          </div>
        ) : (
          <MarketplaceGrid
            items={filteredItems}
          />
        )}

      </Container>
    </section>
  );
}