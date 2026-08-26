import Input from "../../ui/Input";

import {
  getCategoriesByMarketplaceType,
} from "../../../data/marketplaceCategories";

import type { MarketplaceItemType } from "../../../types/marketplaceItem";

import LocationSelector from "../LocationSelector";

interface Props {
  marketplaceType: MarketplaceItemType;

  title: string;
  description: string;
  category: string;
  subCategory: string;
  price: string;
  location: string;

  province: string;
  district: string;

  onTitleChange: (value: string) => void;
  onDescriptionChange: (value: string) => void;
  onCategoryChange: (value: string) => void;
  onSubCategoryChange: (value: string) => void;
  onPriceChange: (value: string) => void;
  onLocationChange: (value: string) => void;

  onProvinceChange: (value: string) => void;
  onDistrictChange: (value: string) => void;
}

export default function BasicInformation({
  marketplaceType,

  title,
  description,
  category,
  subCategory,
  price,
  location,

  province,
  district,

  onTitleChange,
  onDescriptionChange,
  onCategoryChange,
  onSubCategoryChange,
  onPriceChange,
  onLocationChange,

  onProvinceChange,
  onDistrictChange,
}: Props) {
  /*
   * Get categories according to the
   * selected marketplace type.
   *
   * product → Product categories
   * rental  → Rental categories
   * service → Service categories
   * job     → Job categories
   */
  const categories =
    getCategoriesByMarketplaceType(
      marketplaceType
    );

  /*
   * Find the selected category so we
   * can display its subcategories.
   */
  const selectedCategory =
    categories.find(
      (categoryItem) =>
        categoryItem.id === category
    );

  /*
   * Build the location string whenever
   * province or district changes.
   *
   * This keeps compatibility with the
   * existing marketplace item's
   * `location: string` field.
   */
  function updateLocation(
    nextProvince: string,
    nextDistrict: string
  ) {
    const parts = [
      "Rwanda",
      nextProvince,
      nextDistrict,
    ].filter(Boolean);

    onLocationChange(
      parts.join(", ")
    );
  }

  function handleProvinceChange(
    value: string
  ) {
    onProvinceChange(value);

    onDistrictChange("");

    updateLocation(
      value,
      ""
    );
  }

  function handleDistrictChange(
    value: string
  ) {
    onDistrictChange(value);

    updateLocation(
      province,
      value
    );
  }

  return (
    <div className="space-y-6">

      {/* =========================
          TITLE
      ========================== */}

      <Input
        label="Title"
        value={title}
        onChange={(e) =>
          onTitleChange(
            e.target.value
          )
        }
      />

      {/* =========================
          DESCRIPTION
      ========================== */}

      <div>
        <label className="block mb-2 font-medium">
          Description
        </label>

        <textarea
          value={description}
          onChange={(e) =>
            onDescriptionChange(
              e.target.value
            )
          }
          className="
            w-full
            rounded-xl
            border
            px-4
            py-3
            h-40
            resize-none
          "
        />
      </div>

      {/* =========================
          CATEGORY
      ========================== */}

      <div>
        <label className="block mb-2 font-medium">
          Category
        </label>

        <select
          value={category}
          onChange={(e) =>
            onCategoryChange(
              e.target.value
            )
          }
          className="
            w-full
            rounded-xl
            border
            px-4
            py-3
          "
        >
          <option value="">
            Select Category
          </option>

          {categories.map(
            (categoryItem) => (
              <option
                key={categoryItem.id}
                value={categoryItem.id}
              >
                {categoryItem.name}
              </option>
            )
          )}
        </select>
      </div>

      {/* =========================
          SUBCATEGORY
      ========================== */}

      <div>
        <label className="block mb-2 font-medium">
          Subcategory
        </label>

        <select
          value={subCategory}
          onChange={(e) =>
            onSubCategoryChange(
              e.target.value
            )
          }
          disabled={!category}
          className="
            w-full
            rounded-xl
            border
            px-4
            py-3
            disabled:bg-gray-100
            disabled:text-gray-400
          "
        >
          <option value="">
            {category
              ? "Select Subcategory"
              : "Select Category First"}
          </option>

          {selectedCategory?.subCategories.map(
            (subCategoryItem) => (
              <option
                key={subCategoryItem.id}
                value={subCategoryItem.id}
              >
                {subCategoryItem.name}
              </option>
            )
          )}
        </select>
      </div>

      {/* =========================
          PRICE
      ========================== */}

      <Input
        label="Price"
        type="number"
        value={price}
        onChange={(e) =>
          onPriceChange(
            e.target.value
          )
        }
      />

      {/* =========================
          LOCATION
      ========================== */}

      <LocationSelector
        province={province}
        district={district}
        onProvinceChange={
          handleProvinceChange
        }
        onDistrictChange={
          handleDistrictChange
        }
      />

      {/* Current location value */}

      {location && (
        <div className="rounded-xl bg-gray-50 border p-4">
          <p className="text-sm text-gray-500">
            Selected Location
          </p>

          <p className="font-medium mt-1">
            {location}
          </p>
        </div>
      )}

    </div>
  );
}