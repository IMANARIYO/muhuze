import { useEffect, useState } from "react";

import Container from "../../components/ui/Container";
import SectionTitle from "../../components/ui/SectionTitle";
import Button from "../../components/ui/Button";

import { useAuth } from "../../context/AuthContext";
import { sellerApiService } from "../../business/services/sellerApiService";

import type {
  Order,
  OrderStatus,
} from "../../types/order";

export default function SellerOrders() {
  const { currentUser } = useAuth();

  const [orders, setOrders] =
    useState<Order[]>([]);

  const [loading, setLoading] =
    useState(true);

  const [error, setError] =
    useState("");

  /*
   * ==========================================
   * LOAD SELLER ORDERS
   * ==========================================
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

        const data =
          await sellerApiService.getSellerOrders(
            currentUser._id
          );

        setOrders(data);
      } catch (error) {
        console.error(
          "Failed to load seller orders:",
          error
        );

        setError(
          "Failed to load seller orders."
        );

        setOrders([]);
      } finally {
        setLoading(false);
      }
    }

    loadOrders();
  }, [currentUser?._id]);

  /*
   * ==========================================
   * UPDATE ORDER STATUS
   * ==========================================
   */
  const updateStatus = async (
    orderId: string,
    status: OrderStatus
  ) => {
    if (!currentUser?._id) {
      return;
    }

    try {
      setError("");

      const updatedOrder =
        await sellerApiService.updateOrderStatus(
          currentUser._id,
          orderId,
          status
        );

      setOrders((currentOrders) =>
        currentOrders.map((order) =>
          order._id === updatedOrder._id
            ? updatedOrder
            : order
        )
      );
    } catch (error) {
      console.error(
        "Failed to update order status:",
        error
      );

      setError(
        "Failed to update order status."
      );
    }
  };

  /*
   * ==========================================
   * ACCEPT ORDER
   * ==========================================
   */
  const acceptOrder = async (
    id: string
  ) => {
    await updateStatus(
      id,
      "Accepted"
    );
  };

  /*
   * ==========================================
   * REJECT ORDER
   * ==========================================
   */
  const rejectOrder = async (
    id: string
  ) => {
    await updateStatus(
      id,
      "Rejected"
    );
  };

  /*
   * ==========================================
   * NOT LOGGED IN
   * ==========================================
   */
  if (!currentUser) {
    return null;
  }

  /*
   * ==========================================
   * LOADING
   * ==========================================
   */
  if (loading) {
    return (
      <section>
        <Container>

          <SectionTitle
            title="Seller Orders"
            subtitle="Manage customer purchases."
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
          title="Seller Orders"
          subtitle="Manage customer purchases."
        />

        {/* =================================
            ERROR
        ================================= */}

        {error && (
          <div className="mt-6 p-4 bg-red-100 text-red-700 rounded-lg">
            {error}
          </div>
        )}

        {/* =================================
            NO ORDERS
        ================================= */}

        {orders.length === 0 ? (
          <div className="text-center mt-16">

            <h2 className="text-2xl font-bold">
              No Orders Yet
            </h2>

            <p className="text-gray-500 mt-3">
              When customers purchase your
              products, their orders will
              appear here.
            </p>

          </div>
        ) : (

          /* =================================
             ORDERS
          ================================= */

          <div className="space-y-8 mt-10">

            {orders.map((order) => (

              <div
                key={order._id}
                className="
                  border
                  rounded-xl
                  p-6
                  bg-white
                  shadow
                "
              >

                {/* =============================
                    ORDER HEADER
                ============================== */}

                <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">

                  <h2 className="font-bold text-xl">
                    Order #{order._id}
                  </h2>

                  <span
                    className={`
                      inline-flex
                      w-fit
                      px-4
                      py-1
                      rounded-full
                      font-medium

                      ${
                        order.status ===
                        "Accepted"
                          ? "bg-green-100 text-green-700"
                          : order.status ===
                            "Rejected"
                          ? "bg-red-100 text-red-700"
                          : order.status ===
                            "Pending"
                          ? "bg-yellow-100 text-yellow-700"
                          : "bg-gray-100 text-gray-700"
                      }
                    `}
                  >
                    {order.status}
                  </span>

                </div>

                {/* =============================
                    BUYER INFORMATION
                ============================== */}

                <div className="mt-4 space-y-1">

                  <p>
                    <strong>
                      Buyer:
                    </strong>{" "}
                    {order.buyer}
                  </p>

                  <p>
                    <strong>
                      Total:
                    </strong>{" "}
                    {Number(
                      order.total
                    ).toLocaleString()}{" "}
                    RWF
                  </p>

                  <p>
                    <strong>
                      Payment Method:
                    </strong>{" "}
                    {order.paymentMethod}
                  </p>

                  <p>
                    <strong>
                      Payment Status:
                    </strong>{" "}
                    {order.paymentStatus}
                  </p>

                  <p>
                    <strong>
                      Delivery:
                    </strong>{" "}
                    {order.deliveryAddress}
                  </p>

                </div>

                {/* =============================
                    PRODUCTS
                ============================== */}

                <div className="mt-6">

                  <h3 className="font-bold mb-3">
                    Products
                  </h3>

                  <div className="space-y-2">

                    {order.products.map(
                      (product, index) => (

                        <div
                          key={`${order._id}-${product.productId}-${index}`}
                          className="
                            flex
                            justify-between
                            items-center
                            py-3
                            px-4
                            bg-gray-50
                            rounded-lg
                          "
                        >

                          <div>

                            <span className="font-medium">
                              Product
                            </span>

                            <p className="text-sm text-gray-500">
                              Product ID:{" "}
                              {product.productId}
                            </p>

                          </div>

                          <span className="text-gray-600">
                            x{product.quantity}
                          </span>

                        </div>

                      )
                    )}

                  </div>

                </div>

                {/* =============================
                    ACTIONS
                ============================== */}

                {order.status ===
                  "Pending" && (

                  <div className="flex flex-wrap gap-4 mt-8">

                    <Button
                      onClick={() =>
                        acceptOrder(
                          order._id
                        )
                      }
                    >
                      Accept
                    </Button>

                    <Button
                      variant="danger"
                      onClick={() =>
                        rejectOrder(
                          order._id
                        )
                      }
                    >
                      Reject
                    </Button>

                  </div>

                )}

                {/* =============================
                    ACCEPTED MESSAGE
                ============================== */}

                {order.status ===
                  "Accepted" && (

                  <p className="mt-6 text-green-600 font-medium">
                    This order has been accepted.
                  </p>

                )}

                {/* =============================
                    REJECTED MESSAGE
                ============================== */}

                {order.status ===
                  "Rejected" && (

                  <p className="mt-6 text-red-600 font-medium">
                    This order has been rejected.
                  </p>

                )}

              </div>

            ))}

          </div>

        )}

      </Container>
    </section>
  );
}