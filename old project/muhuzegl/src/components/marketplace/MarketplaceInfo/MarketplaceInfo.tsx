import Button from "../../ui/Button";
import { useCart } from "../../../context/CartContext";
import type {
  MarketplaceItem,
} from "../../../types/marketplaceItem";
import { useWishlist } from "../../../context/WishlistContext";
import { useNavigate } from "react-router-dom";

interface Props {
  item: MarketplaceItem;
}

export default function MarketplaceInfo({
  item,
}: Props) {
  const {
    addToCart,
    clearCart,
  } = useCart();

  const navigate = useNavigate();

  const {
    addToWishlist,
    removeFromWishlist,
    isInWishlist,
  } = useWishlist();

  /**
   * ==========================================
   * WISHLIST
   * ==========================================
   */

  function handleWishlist() {
    if (isInWishlist(item._id)) {
      removeFromWishlist(item._id);
    } else {
      addToWishlist(item);
    }
  }

  /**
   * ==========================================
   * PRODUCT ACTIONS
   * ==========================================
   */

  function handleAddToCart() {
    addToCart(item);
  }

  function handleBuyNow() {
    clearCart();

    addToCart(item);

    navigate("/checkout");
  }

  /**
   * ==========================================
   * RENTAL ACTION
   * ==========================================
   */

  function handleRentalRequest() {
    navigate(
      `/marketplace/${item._id}?action=rental`
    );
  }

  /**
   * ==========================================
   * SERVICE ACTION
   * ==========================================
   */

  function handleServiceRequest() {
    navigate(
      `/marketplace/${item._id}?action=service`
    );
  }

  /**
   * ==========================================
   * JOB ACTION
   * ==========================================
   */

  function handleJobApplication() {
    navigate(
      `/marketplace/${item._id}?action=apply`
    );
  }

  /**
   * ==========================================
   * MARKETPLACE TYPE
   * ==========================================
   *
   * Product is the default publishing type.
   */

  const marketplaceType =
    item.marketplaceItemType || "product";

  /**
   * ==========================================
   * ACTION BUTTONS
   * ==========================================
   */

  function renderActions() {
    switch (marketplaceType) {
      /**
       * PRODUCT
       */
      case "product":
        return (
          <>
            <Button
              onClick={handleAddToCart}
            >
              Add to Cart
            </Button>

            <Button
              onClick={handleBuyNow}
            >
              Buy Now
            </Button>
          </>
        );

      /**
       * RENTAL
       */
      case "rental":
        return (
          <>
            <Button
              onClick={handleRentalRequest}
            >
              Request Rental
            </Button>

           <Button
  onClick={() => {
    document
      .getElementById("marketplace-contact")
      ?.scrollIntoView({
        behavior: "smooth",
        block: "start",
      });
  }}
>
  Contact Owner
</Button>
            
          </>
        );

      /**
       * SERVICE
       */
      case "service":
        return (
          <>
            <Button
              onClick={handleServiceRequest}
            >
              Request Service
            </Button>

            <Button
              onClick={() =>
                navigate(
                  `/marketplace/${item._id}?action=contact-provider`
                )
              }
            >
              Contact Provider
            </Button>
          </>
        );

      /**
       * JOB
       */
      case "job":
        return (
          <Button
            onClick={handleJobApplication}
          >
            Apply Now
          </Button>
        );

      default:
        return null;
    }
  }

  return (
    <div>
      {/* ======================================
          TITLE
      ======================================= */}

      <h1 className="text-4xl font-bold">
        {item.title}
      </h1>

      {/* ======================================
          PRICE
      ======================================= */}

      <p className="text-3xl text-blue-600 font-bold mt-4">
        {item.price.toLocaleString()}{" "}
        {item.currency}
      </p>

      {/* ======================================
          BASIC INFORMATION
      ======================================= */}

      <div className="flex flex-wrap gap-6 mt-6 text-gray-500">
        <span>
          📍 {item.location}
        </span>

        <span>
          ⭐ {item.rating}
        </span>

        <span>
          {item.category}
        </span>
      </div>

      {/* ======================================
          LISTING TYPE
      ======================================= */}

      <div className="mt-4">
        <span
          className="
            inline-block
            rounded-full
            bg-gray-100
            px-4
            py-2
            text-sm
            font-semibold
            uppercase
            text-gray-600
          "
        >
          {marketplaceType}
        </span>
      </div>

      {/* ======================================
          ACTION BUTTONS
      ======================================= */}

      <div className="mt-8 flex flex-wrap gap-4">
        {renderActions()}

        {/* Wishlist is available for all
            marketplace listing types. */}

        <Button
          onClick={handleWishlist}
        >
          {isInWishlist(item._id)
            ? "❤️ Saved"
            : "🤍 Save"}
        </Button>
      </div>

      {/* ======================================
          DESCRIPTION
      ======================================= */}

      <div className="mt-10">
        <h2 className="text-xl font-semibold">
          Description
        </h2>

        <p className="mt-3 text-gray-600 leading-8">
          {item.description}
        </p>
      </div>
    </div>
  );
}