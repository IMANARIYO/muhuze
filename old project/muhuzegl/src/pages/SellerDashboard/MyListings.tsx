import {
  useEffect,
  useState,
} from "react";

import { Link } from "react-router-dom";

import Container from "../../components/ui/Container";
import SectionTitle from "../../components/ui/SectionTitle";

import { useAuth } from "../../context/AuthContext";
import { useToast } from "../../components/ui/Toast";

import { sellerApiService } from "../../business/services/sellerApiService";

import type { MarketplaceItem } from "../../types/marketplaceItem";

import { getImageUrl } from "../../utils/imageUrl";

export default function MyListings() {
  const { currentUser } = useAuth();

  const { showToast } = useToast();

  const [listings, setListings] =
    useState<MarketplaceItem[]>([]);

  const [loading, setLoading] =
    useState(true);

  const [error, setError] =
    useState("");

  /*
   * Load products belonging to
   * the currently logged-in seller.
   */
  useEffect(() => {
    async function loadMyListings() {
      if (!currentUser?._id) {
        setListings([]);
        setLoading(false);
        return;
      }

      try {
        setLoading(true);
        setError("");

        const data =
          await sellerApiService.getSellerProducts(
            currentUser._id
          );

        setListings(data);
      } catch (error) {
        console.error(
          "Failed to load seller listings:",
          error
        );

        setError(
          "Failed to load your listings."
        );

        setListings([]);
      } finally {
        setLoading(false);
      }
    }

    loadMyListings();
  }, [currentUser?._id]);

  /*
   * Delete seller listing.
   */
  async function handleDelete(id: string) {
    const confirmed = window.confirm(
      "Are you sure you want to delete this listing?"
    );

    if (!confirmed) {
      return;
    }

    if (!currentUser?._id) {
      return;
    }

    try {
      await sellerApiService.deleteSellerProduct(
        currentUser._id,
        id
      );

      /*
       * Remove the deleted listing
       * from the current screen.
       */
      setListings((current) =>
        current.filter(
          (item) => item._id !== id
        )
      );

      showToast(
        "Listing deleted successfully.",
        "success"
      );
    } catch (error) {
      console.error(
        "Failed to delete listing:",
        error
      );

      showToast(
        "Failed to delete listing.",
        "error"
      );
    }
  }

  if (!currentUser) {
    return null;
  }

  return (
    <section>
      <Container>

        <SectionTitle
          title="My Listings"
          subtitle="Manage your marketplace listings."
        />

        {/* Error */}

        {error && (
          <div className="mt-6 rounded-xl bg-red-100 p-4 text-red-700">
            {error}
          </div>
        )}

        {/* Loading */}

        {loading ? (
          <div className="mt-10 bg-white rounded-2xl shadow p-10 text-center">

            <p className="text-gray-500">
              Loading your listings...
            </p>

          </div>
        ) : listings.length === 0 ? (

          /* No listings */

          <div className="mt-10 bg-white rounded-2xl shadow p-10 text-center">

            <h2 className="text-2xl font-bold">
              No Listings Yet
            </h2>

            <p className="text-gray-500 mt-3">
              Start selling by uploading your
              first product.
            </p>

            <Link
              to="/upload-product"
              className="
                inline-block
                mt-6
                bg-blue-600
                text-white
                px-6
                py-3
                rounded-xl
                hover:bg-blue-700
              "
            >
              Upload Product
            </Link>

          </div>

        ) : (

          /* Seller listings */

          <div className="grid gap-6 mt-10">

            {listings.map((item) => (

              <div
                key={item._id}
                className="
                  bg-white
                  rounded-2xl
                  shadow
                  p-6
                  flex
                  flex-col
                  md:flex-row
                  md:items-center
                  justify-between
                  gap-6
                "
              >

                {/* Product information */}

                <div className="flex gap-5 items-center">

                  {/* Product image */}

                  <img
                    src={
                      item.images?.[0]
                        ? getImageUrl(
                            item.images[0]
                          )
                        : "/placeholder-image.png"
                    }
                    alt={
                      item.title ||
                      "Marketplace item"
                    }
                    className="
                      w-28
                      h-28
                      object-cover
                      rounded-xl
                      border
                      flex-shrink-0
                    "
                  />

                  {/* Details */}

                  <div>

                    <h3 className="text-xl font-bold">
                      {item.title}
                    </h3>

                    <p className="text-gray-500 mt-2">
                      {item.category}
                    </p>

                    <p className="text-blue-600 font-bold mt-3">
                      {item.price.toLocaleString()}{" "}
                      {item.currency}
                    </p>

                    <p className="text-sm text-gray-500 mt-2">
                      Status:{" "}
                      <span
                        className={
                          item.status ===
                          "published"
                            ? "text-green-600 font-semibold"
                            : "text-gray-600"
                        }
                      >
                        {item.status}
                      </span>
                    </p>

                  </div>

                </div>

                {/* Actions */}

                <div className="flex flex-wrap gap-3">

                  {/* View */}

                  <Link
                    to={`/marketplace/${item._id}`}
                    className="
                      px-4
                      py-2
                      rounded-lg
                      border
                      border-blue-600
                      text-blue-600
                      hover:bg-blue-50
                    "
                  >
                    View
                  </Link>

                  {/* Edit */}

                  <Link
                    to={`/upload-product/${item._id}`}
                    className="
                      px-4
                      py-2
                      rounded-lg
                      bg-green-600
                      text-white
                      hover:bg-green-700
                    "
                  >
                    Edit
                  </Link>

                  {/* Delete */}

                  <button
                    type="button"
                    onClick={() =>
                      handleDelete(item._id)
                    }
                    className="
                      px-4
                      py-2
                      rounded-lg
                      bg-red-600
                      text-white
                      hover:bg-red-700
                    "
                  >
                    Delete
                  </button>

                </div>

              </div>

            ))}

          </div>

        )}

      </Container>
    </section>
  );
}