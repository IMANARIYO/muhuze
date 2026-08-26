import { useEffect, useState } from "react";

import OrderCard from "../../components/my-orders/OrderCard";
import Container from "../../components/ui/Container";
import SectionTitle from "../../components/ui/SectionTitle";

import { useAuth } from "../../context/AuthContext";
import { orderService } from "../../business/services/orderService";

import type { Order } from "../../types/order";

export default function MyOrders() {
  const { currentUser } = useAuth();

  const [orders, setOrders] = useState<Order[]>([]);

  const [loading, setLoading] = useState(true);

  const [error, setError] = useState("");

  /*
   * Load orders belonging to
   * the currently logged-in buyer.
   */
  useEffect(() => {
    async function loadOrders() {
      if (!currentUser?._id) {
        setOrders([]);
        setLoading(false);
        return;
      }

      try {
        setLoading(true);
        setError("");

        const data = await orderService.findByBuyer(
          currentUser._id
        );

        setOrders(data);
      } catch (error) {
        console.error(
          "Failed to load buyer orders:",
          error
        );

        setError("Failed to load your orders.");

        setOrders([]);
      } finally {
        setLoading(false);
      }
    }

    loadOrders();
  }, [currentUser?._id]);

  /*
   * User is not logged in.
   */
  if (!currentUser) {
    return null;
  }

  /*
   * Loading state.
   */
  if (loading) {
    return (
      <section>
        <Container>
          <SectionTitle
            title="My Orders"
            subtitle="View all your orders."
          />

          <div className="text-center mt-16">
            <h2 className="text-2xl font-bold">
              Loading Orders...
            </h2>
          </div>
        </Container>
      </section>
    );
  }

  return (
    <section>
      <Container>
        <SectionTitle
          title="My Orders"
          subtitle="Track all your purchases."
        />

        {/* Error */}

        {error && (
          <div className="mt-6 p-4 bg-red-100 text-red-700 rounded-xl">
            {error}
          </div>
        )}

        {/* No Orders */}

        {orders.length === 0 ? (
          <div className="text-center mt-16">
            <h2 className="text-2xl font-bold">
              No Orders Yet
            </h2>

            <p className="text-gray-500 mt-3">
              Your orders will appear here after checkout.
            </p>
          </div>
        ) : (
          /* Orders */

          <div className="mt-10 space-y-8">
            {orders.map((order) => (
              <OrderCard
                key={order._id}
                order={order}
              />
            ))}
          </div>
        )}
      </Container>
    </section>
  );
}