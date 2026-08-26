import { Link } from "react-router-dom";

import {
  FaHeart,
  FaRegHeart,
  FaMapMarkerAlt,
  FaShoppingCart,
  FaStar,
  FaArrowRight,
} from "react-icons/fa";

import type { MarketplaceItem } from "../../../types/marketplaceItem";

import { useCart } from "../../../context/CartContext";
import { useToast } from "../../ui/Toast";
import { useWishlist } from "../../../context/WishlistContext";

interface Props {
  product: MarketplaceItem;
}

export default function ProductCard({
  product,
}: Props) {
  const { addToCart } = useCart();

  const { showToast } = useToast();

  const {
    addToWishlist,
    removeFromWishlist,
    isInWishlist,
  } = useWishlist();

  const wishlistActive =
    isInWishlist(product._id);

  function handleAddToCart() {
    addToCart(product);

    showToast(
      `${product.title} added to cart.`,
      "success"
    );
  }

  function handleWishlist() {
    if (wishlistActive) {
      removeFromWishlist(product._id);

      showToast(
        "Removed from wishlist.",
        "success"
      );

      return;
    }

    addToWishlist(product);

    showToast(
      "Added to wishlist.",
      "success"
    );
  }

  return (
    <article
      className="
        group
        overflow-hidden
        rounded-3xl
        border
        border-slate-100
        bg-white
        shadow-sm
        transition-all
        duration-300
        hover:-translate-y-1
        hover:shadow-2xl
      "
    >

      {/* ======================================
          PRODUCT IMAGE
      ====================================== */}

      <div
        className="
          relative
          overflow-hidden
          bg-slate-100
        "
      >
        <img
          src={product.images[0]}
          alt={product.title}
          className="
            h-64
            w-full
            object-cover
            transition-transform
            duration-500
            group-hover:scale-105
          "
        />

        {/* Featured badge */}

        {product.featured && (
          <span
            className="
              absolute
              left-4
              top-4
              inline-flex
              items-center
              gap-2
              rounded-full
              bg-blue-600
              px-3
              py-1.5
              text-xs
              font-bold
              text-white
              shadow-lg
            "
          >
            Featured
          </span>
        )}

        {/* Wishlist */}

        <button
          type="button"
          onClick={handleWishlist}
          aria-label={
            wishlistActive
              ? "Remove from wishlist"
              : "Add to wishlist"
          }
          className="
            absolute
            right-4
            top-4
            flex
            h-10
            w-10
            items-center
            justify-center
            rounded-full
            bg-white
            shadow-lg
            transition
            hover:scale-105
          "
        >
          {wishlistActive ? (
            <FaHeart className="text-red-500" />
          ) : (
            <FaRegHeart className="text-slate-700" />
          )}
        </button>
      </div>

      {/* ======================================
          PRODUCT INFORMATION
      ====================================== */}

      <div className="p-5">

        <h3
          className="
            line-clamp-2
            min-h-[56px]
            text-lg
            font-bold
            leading-7
            text-slate-900
          "
        >
          {product.title}
        </h3>

        {/* Seller */}

        <div
          className="
            mt-2
            text-sm
            font-medium
            text-blue-600
          "
        >
          Verified Seller
        </div>

        {/* Location */}

        <div
          className="
            mt-3
            flex
            items-center
            gap-2
            text-sm
            text-slate-500
          "
        >
          <FaMapMarkerAlt />

          <span className="truncate">
            {product.location}
          </span>
        </div>

        {/* Rating */}

        <div
          className="
            mt-3
            flex
            items-center
            gap-2
            text-sm
          "
        >
         <FaStar className="text-orange-500" />

          <span className="font-semibold text-slate-800">
            {product.rating.toFixed(1)}
          </span>

          <span className="text-slate-400">
            Customer rating
          </span>
        </div>

        {/* Price */}

        <div className="mt-5">

          <p
            className="
              text-2xl
              font-extrabold
              text-blue-600
            "
          >
            {product.price.toLocaleString()}{" "}
            {product.currency}
          </p>

        </div>

        {/* ======================================
            ACTIONS
        ====================================== */}

        <div
          className="
            mt-5
            grid
            grid-cols-2
            gap-3
          "
        >
          <button
            type="button"
            onClick={handleAddToCart}
            className="
              inline-flex
              items-center
              justify-center
              gap-2
              rounded-xl
              bg-blue-600
              py-3
              font-semibold
              text-white
              transition
              hover:bg-blue-700
            "
          >
            <FaShoppingCart />

            Add
          </button>
<Link
  to={`/marketplace/${product._id}`}
  className="
    inline-flex
    items-center
    justify-center
    gap-2
    rounded-xl
    border-2
    border-orange-500
    py-3
    font-semibold
    text-orange-500
    transition
    hover:bg-orange-500
    hover:text-white
  "
>
  Details

  <FaArrowRight className="text-xs" />
</Link>
        </div>

      </div>

    </article>
  );
}