import {
  marketplaceCategoryGroups,
} from "../../data/marketplaceCategories";

import type { Category } from "./types";

/*
 * Images used by the Categories page.
 *
 * The category information comes from
 * marketplaceCategories.ts.
 *
 * These paths only control the visual
 * representation of each category.
 */
const categoryImages: Record<string, string> = {
  electronics:
    "/images/categories/electronics.png",

  "phones-tablets":
    "/images/categories/phones-tablets.png",

  "computers-it":
    "/images/categories/computers-it.png",

  vehicles:
    "/images/categories/vehicles.png",

  "real-estate":
    "/images/categories/real-estate.png",

  fashion:
    "/images/categories/fashion.png",

  "home-furniture":
    "/images/categories/home-furniture.png",

  agriculture:
    "/images/categories/agriculture.png",

  "health-beauty":
    "/images/categories/health-beauty.png",

  services:
    "/images/categories/services.png",

  "business-equipment":
    "/images/categories/business-equipment.png",

  "sports-fitness":
    "/images/categories/sports-fitness.png",

  "books-education":
    "/images/categories/books-education.png",

  "toys-kids":
    "/images/categories/toys-kids.png",
};

const productGroup =
  marketplaceCategoryGroups.find(
    (group) => group.type === "product"
  );

export const categories: Category[] =
  (productGroup?.categories ?? []).map(
    (category) => ({
      id: category.id,

      name: category.name,

      image:
        categoryImages[category.id] ??
        "/images/categories/default.png",

      productCount:
        category.subCategories.length,

      description:
        `Explore ${category.name} products and offers on MUHUZE.`,
    })
  );