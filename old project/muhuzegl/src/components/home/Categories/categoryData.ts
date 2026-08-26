import {
  FaMobileAlt,
  FaLaptop,
  FaCar,
  FaHome,
  FaTshirt,
  FaCouch,
  FaSeedling,
  FaBriefcase,
  FaTools,
  FaHeartbeat,
  FaBuilding,
  FaDumbbell,
  FaBook,
  FaChild,
} from "react-icons/fa";

import {
  marketplaceCategoryGroups,
  type MarketplaceCategory,
} from "../../../data/marketplaceCategories";

import type { Category } from "./types";

/*
 * Home category icons.
 *
 * The category information itself comes from
 * marketplaceCategories.ts.
 *
 * This object only controls how categories look
 * on the Home page.
 */
const categoryIcons: Record<string, Category["icon"]> = {
  electronics: FaMobileAlt,
  "phones-tablets": FaMobileAlt,
  "computers-it": FaLaptop,
  vehicles: FaCar,
  "real-estate": FaHome,
  fashion: FaTshirt,
  "home-furniture": FaCouch,
  agriculture: FaSeedling,
  "jobs-careers": FaBriefcase,
  services: FaTools,
  "health-beauty": FaHeartbeat,
  "business-equipment": FaBuilding,
  "sports-fitness": FaDumbbell,
  "books-education": FaBook,
  "toys-kids": FaChild,
};

/*
 * Get the Product categories from the
 * existing marketplace category system.
 */
const productCategories =
  marketplaceCategoryGroups.find(
    (group) => group.type === "product"
  )?.categories ?? [];

/*
 * Convert MarketplaceCategory into the
 * structure already expected by the Home UI.
 */
export const categories: Category[] =
  productCategories.map(
    (category: MarketplaceCategory) => ({
      id: Number(
        category.id
          .split("-")
          .reduce(
            (total, part) =>
              total + part.charCodeAt(0),
            0
          )
      ),

      name: category.name,

      path: `/products?category=${category.id}`,

      icon:
        categoryIcons[category.id] ??
        FaBuilding,

      description:
        category.subCategories.length > 0
          ? `${category.name} and related products.`
          : `Explore ${category.name}.`,

      subcategories:
        category.subCategories.map(
          (subcategory) => ({
            id: Number(
              subcategory.id
                .split("-")
                .reduce(
                  (total, part) =>
                    total +
                    part.charCodeAt(0),
                  0
                )
            ),

            name: subcategory.name,

            path:
              `/products?category=${subcategory.id}`,
          })
        ),
    })
  );