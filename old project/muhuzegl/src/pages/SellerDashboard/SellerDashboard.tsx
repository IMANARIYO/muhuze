import {
  useEffect,
  useState,
} from "react";

import Container from "../../components/ui/Container";
import SectionTitle from "../../components/ui/SectionTitle";

import { useAuth } from "../../context/AuthContext";

import { sellerDashboardApiService } from "../../business/services/sellerDashboardApiService";

import type { SellerDashboardStats } from "../../business/services/sellerDashboardApiService";

import { Link } from "react-router-dom";

export default function SellerDashboard() {
  const { currentUser } = useAuth();

  const [stats, setStats] =
    useState<SellerDashboardStats | null>(null);

  const [loading, setLoading] =
    useState(true);

  const [error, setError] =
    useState("");

  /*
   * Load seller dashboard statistics
   * from the backend.
   */
  useEffect(() => {
    async function loadDashboard() {
      if (!currentUser?._id) {
        setStats(null);
        setLoading(false);
        return;
      }

      try {
        setLoading(true);
        setError("");

        const data =
          await sellerDashboardApiService.getDashboard(
            currentUser._id
          );

        setStats(data);
      } catch (error) {
        console.error(
          "Failed to load seller dashboard:",
          error
        );

        setError(
          "Failed to load seller dashboard."
        );

        setStats(null);
      } finally {
        setLoading(false);
      }
    }

    loadDashboard();
  }, [currentUser?._id]);

  if (!currentUser) {
    return null;
  }

  return (
    <section>
      <Container>

        <SectionTitle
          title="Seller Dashboard"
          subtitle="Manage your marketplace business."
        />

        {/* Error */}

        {error && (
          <div className="mt-6 rounded-xl bg-red-100 p-4 text-red-700">
            {error}
          </div>
        )}

        {/* Statistics */}

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-10">

          {/* Total Listings */}

          <div className="bg-white rounded-2xl shadow p-6">
            <h3 className="text-gray-500">
              Total Listings
            </h3>

            <p className="text-4xl font-bold text-blue-600 mt-3">
              {loading
                ? "..."
                : stats?.totalListings ?? 0}
            </p>
          </div>

          {/* Active Listings */}

          <div className="bg-white rounded-2xl shadow p-6">
            <h3 className="text-gray-500">
              Active Listings
            </h3>

            <p className="text-4xl font-bold text-green-600 mt-3">
              {loading
                ? "..."
                : stats?.activeListings ?? 0}
            </p>
          </div>

          {/* Orders */}

          <div className="bg-white rounded-2xl shadow p-6">
            <h3 className="text-gray-500">
              Orders
            </h3>

            <p className="text-4xl font-bold text-purple-600 mt-3">
              {loading
                ? "..."
                : stats?.totalOrders ?? 0}
            </p>
          </div>

        </div>

        {/* Revenue */}

        <div className="mt-6 bg-white rounded-2xl shadow p-6">
          <h3 className="text-gray-500">
            Revenue
          </h3>

          <p className="text-3xl font-bold text-green-600 mt-3">
            {loading
              ? "..."
              : `${(
                  stats?.revenue ?? 0
                ).toLocaleString()} RWF`}
          </p>
        </div>

        {/* Order Statistics */}

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-6">

          {/* Pending */}

          <div className="bg-white rounded-2xl shadow p-6">
            <h3 className="text-gray-500">
              Pending Orders
            </h3>

            <p className="text-3xl font-bold text-yellow-600 mt-3">
              {loading
                ? "..."
                : stats?.pendingOrders ?? 0}
            </p>
          </div>

          {/* Accepted */}

          <div className="bg-white rounded-2xl shadow p-6">
            <h3 className="text-gray-500">
              Accepted Orders
            </h3>

            <p className="text-3xl font-bold text-green-600 mt-3">
              {loading
                ? "..."
                : stats?.acceptedOrders ?? 0}
            </p>
          </div>

          {/* Rejected */}

          <div className="bg-white rounded-2xl shadow p-6">
            <h3 className="text-gray-500">
              Rejected Orders
            </h3>

            <p className="text-3xl font-bold text-red-600 mt-3">
              {loading
                ? "..."
                : stats?.rejectedOrders ?? 0}
            </p>
          </div>

        </div>

        {/* Seller Actions */}

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mt-10">

          <Link
            to="/upload-product"
            className="
              bg-blue-600
              text-white
              rounded-xl
              p-5
              text-center
              hover:bg-blue-700
            "
          >
            Upload Product
          </Link>

          <Link
            to="/my-listings"
            className="
              bg-green-600
              text-white
              rounded-xl
              p-5
              text-center
              hover:bg-green-700
            "
          >
            My Listings
          </Link>

          <Link
            to="/seller-orders"
            className="
              bg-purple-600
              text-white
              rounded-xl
              p-5
              text-center
              hover:bg-purple-700
            "
          >
            Orders
          </Link>

          <Link
            to="/wallet"
            className="
              bg-yellow-500
              text-white
              rounded-xl
              p-5
              text-center
              hover:bg-yellow-600
            "
          >
            Wallet
          </Link>

        </div>

      </Container>
    </section>
  );
}