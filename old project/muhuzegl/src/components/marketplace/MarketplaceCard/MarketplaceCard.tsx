import { Link, useNavigate } from "react-router-dom";

import type {
  MarketplaceItem,
} from "../../../types/marketplaceItem";

import { getImageUrl } from "../../../utils/imageUrl";

interface Props {
  item: MarketplaceItem;
}

export default function MarketplaceCard({
  item,
}: Props) {
  const navigate = useNavigate();

  const image =
    item.images && item.images.length > 0
      ? item.images[0]
      : undefined;

  const marketplaceType =
    item.marketplaceItemType || "product";

  /**
   * ==========================================
   * HANDLE PRODUCT CART
   * ==========================================
   *
   * For now we navigate to the product page.
   * The actual cart operation can be connected
   * to your CartContext/API afterwards.
   */
  const handleAddToCart = (
    e: React.MouseEvent<HTMLButtonElement>
  ) => {
    e.preventDefault();
    e.stopPropagation();

    navigate(`/marketplace/${item._id}`);
  };

  /**
   * ==========================================
   * HANDLE RENTAL
   * ==========================================
   */
  const handleRentalRequest = (
    e: React.MouseEvent<HTMLButtonElement>
  ) => {
    e.preventDefault();
    e.stopPropagation();

    navigate(
      `/marketplace/${item._id}?action=rental`
    );
  };

  /**
   * ==========================================
   * HANDLE SERVICE
   * ==========================================
   */
  const handleServiceRequest = (
    e: React.MouseEvent<HTMLButtonElement>
  ) => {
    e.preventDefault();
    e.stopPropagation();

    navigate(
      `/marketplace/${item._id}?action=service`
    );
  };

  /**
   * ==========================================
   * HANDLE JOB APPLICATION
   * ==========================================
   */
  const handleJobApplication = (
    e: React.MouseEvent<HTMLButtonElement>
  ) => {
    e.preventDefault();
    e.stopPropagation();

    navigate(
      `/marketplace/${item._id}?action=apply`
    );
  };

  /**
   * ==========================================
   * RENDER ACTION
   * ==========================================
   */

  const renderAction = () => {
    switch (marketplaceType) {
      /**
       * PRODUCT
       */
      case "product":
        return (
          <button
            type="button"
            onClick={handleAddToCart}
            className="
              w-full
              rounded-xl
              bg-blue-600
              px-4
              py-3
              text-sm
              font-semibold
              text-white
              transition
              hover:bg-blue-700
            "
          >
            Add to Cart
          </button>
        );

      /**
       * RENTAL
       */
      case "rental":
        return (
          <button
            type="button"
            onClick={handleRentalRequest}
            className="
              w-full
              rounded-xl
              bg-green-600
              px-4
              py-3
              text-sm
              font-semibold
              text-white
              transition
              hover:bg-green-700
            "
          >
            Request Rental
          </button>
        );

      /**
       * SERVICE
       */
      case "service":
        return (
          <button
            type="button"
            onClick={handleServiceRequest}
            className="
              w-full
              rounded-xl
              bg-purple-600
              px-4
              py-3
              text-sm
              font-semibold
              text-white
              transition
              hover:bg-purple-700
            "
          >
            Request Service
          </button>
        );

      /**
       * JOB
       */
      case "job":
        return (
          <button
            type="button"
            onClick={handleJobApplication}
            className="
              w-full
              rounded-xl
              bg-orange-500
              px-4
              py-3
              text-sm
              font-semibold
              text-white
              transition
              hover:bg-orange-600
            "
          >
            Apply Now
          </button>
        );

      default:
        return null;
    }
  };

  return (
    <div
      className="
        overflow-hidden
        rounded-2xl
        border
        bg-white
        shadow-sm
        hover:shadow-lg
        transition
      "
    >
      {/* ======================================
          LISTING LINK
      ======================================= */}

      <Link
        to={`/marketplace/${item._id}`}
        className="block"
      >
        {/* IMAGE */}

        <div className="h-56 w-full overflow-hidden bg-gray-100">
          <img
            src={getImageUrl(image)}
            alt={item.title}
            className="
              h-full
              w-full
              object-cover
              transition
              duration-300
              hover:scale-105
            "
          />
        </div>

        {/* INFORMATION */}

        <div className="p-5 pb-3">
          <h3 className="text-lg font-semibold">
            {item.title}
          </h3>

          <p className="mt-2 text-gray-500">
            {item.category}
          </p>

          <p className="mt-2 text-blue-600 font-bold text-xl">
            {item.price.toLocaleString()}{" "}
            {item.currency}
          </p>

          <div className="mt-3 flex justify-between text-sm text-gray-500">
            <span>
              📍 {item.location}
            </span>

            <span>
              ⭐ {item.rating}
            </span>
          </div>
        </div>
      </Link>

      {/* ======================================
          TYPE LABEL
      ======================================= */}

      <div className="px-5 pb-2">
        <span
          className="
            inline-block
            rounded-full
            bg-gray-100
            px-3
            py-1
            text-xs
            font-semibold
            uppercase
            text-gray-600
          "
        >
          {marketplaceType}
        </span>
      </div>

      {/* ======================================
          ACTION
      ======================================= */}

      <div className="p-5 pt-2">
        {renderAction()}
      </div>
    </div>
  );
}