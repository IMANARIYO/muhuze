import { useEffect, useState } from "react";
import {
  Link,
  useSearchParams,
} from "react-router-dom";

import { FaCheckCircle } from "react-icons/fa";

import Container from "../../components/ui/Container";
import Button from "../../components/ui/Button";

import { orderService } from "../../business/services/orderService";

import type { Order } from "../../types/order";

export default function OrderConfirmation() {
  const [searchParams] =
    useSearchParams();

  const orderId =
    searchParams.get("orderId");

  const [order, setOrder] =
    useState<Order | null>(null);

  const [loading, setLoading] =
    useState(true);

  const [error, setError] =
    useState("");

  /**
   * ==========================================
   * LOAD THE ORDER
   * ==========================================
   */
  useEffect(() => {
    async function loadOrder() {
      /**
       * No order ID was supplied.
       */
      if (!orderId) {
        setError(
          "Order information could not be found."
        );

        setLoading(false);

        return;
      }

      try {
        setLoading(true);
        setError("");

        const data =
          await orderService.findById(
            orderId
          );

        setOrder(data);
      } catch (error) {
        console.error(
          "Failed to load order:",
          error
        );

        setError(
          "Unable to load your order information."
        );
      } finally {
        setLoading(false);
      }
    }

    loadOrder();
  }, [orderId]);

  /**
   * ==========================================
   * LOADING
   * ==========================================
   */
  if (loading) {
    return (
      <section className="py-20">
        <Container>
          <div className="max-w-2xl mx-auto text-center">

            <div className="text-4xl font-bold mb-4">
              Loading your order...
            </div>

            <p className="text-gray-500">
              Please wait while we retrieve
              your order information.
            </p>

          </div>
        </Container>
      </section>
    );
  }

  /**
   * ==========================================
   * ERROR
   * ==========================================
   */
  if (error || !order) {
    return (
      <section className="py-20">
        <Container>
          <div className="max-w-2xl mx-auto text-center">

            <h1 className="text-3xl font-bold mb-4">
              Order Confirmation
            </h1>

            <p className="text-red-500 mb-8">
              {error ||
                "Order could not be found."}
            </p>

            <Link to="/orders">
              <Button className="w-full">
                View My Orders
              </Button>
            </Link>

          </div>
        </Container>
      </section>
    );
  }

  /**
   * ==========================================
   * PAYMENT METHOD DISPLAY
   * ==========================================
   */
  const paymentMethod =
    order.paymentMethod || "Not specified";

  /**
   * ==========================================
   * PAYMENT STATUS
   * ==========================================
   */
  const paymentStatus =
    order.paymentStatus || "Pending";

  /**
   * ==========================================
   * ORDER STATUS
   * ==========================================
   */
  const orderStatus =
    order.status || "Pending";

  return (
    <section className="py-20">

      <Container>

        <div className="max-w-2xl mx-auto">

          {/* =================================
              SUCCESS HEADER
          ================================= */}
          <div className="text-center">

            <FaCheckCircle
              className="text-green-500 text-7xl mx-auto mb-6"
            />

            <h1 className="text-4xl font-bold mb-4">
              Order Placed Successfully!
            </h1>

            <p className="text-gray-600 text-lg mb-8">
              Thank you for shopping with
              MUHUZE. Your order has been
              received and is being processed.
            </p>

          </div>

          {/* =================================
              ORDER INFORMATION
          ================================= */}
          <div className="bg-white rounded-2xl shadow-md p-6 mb-8">

            <h2 className="text-2xl font-bold mb-6">
              Order Information
            </h2>

            {/* Order ID */}
            <div className="flex justify-between gap-4 py-3 border-b">
              <span className="text-gray-500">
                Order ID
              </span>

              <span className="font-semibold text-right break-all">
                {order._id}
              </span>
            </div>

            {/* Total */}
            <div className="flex justify-between gap-4 py-3 border-b">
              <span className="text-gray-500">
                Total
              </span>

              <span className="font-semibold">
                {Number(order.total).toLocaleString()} RWF
              </span>
            </div>

            {/* Payment Method */}
            <div className="flex justify-between gap-4 py-3 border-b">
              <span className="text-gray-500">
                Payment Method
              </span>

              <span className="font-semibold">
                {paymentMethod}
              </span>
            </div>

            {/* Payment Status */}
            <div className="flex justify-between gap-4 py-3 border-b">
              <span className="text-gray-500">
                Payment Status
              </span>

              <span className="font-semibold">
                {paymentStatus}
              </span>
            </div>

            {/* Order Status */}
            <div className="flex justify-between gap-4 py-3">
              <span className="text-gray-500">
                Order Status
              </span>

              <span className="font-semibold">
                {orderStatus}
              </span>
            </div>

          </div>

          {/* =================================
              PAYMENT MESSAGE
          ================================= */}
          {paymentStatus ===
            "Pending" && (
            <div className="bg-yellow-50 border border-yellow-200 rounded-xl p-4 mb-8">

              <p className="text-yellow-800">
                Your selected payment method is{" "}
                <strong>
                  {paymentMethod}
                </strong>
                . Your payment is currently
                pending.
              </p>

            </div>
          )}

          {/* =================================
              BUTTONS
          ================================= */}
          <div className="space-y-4">

            <Link to="/products">
              <Button className="w-full">
                Continue Shopping
              </Button>
            </Link>

            <Link to="/orders">
              <Button
                variant="outline"
                className="w-full"
              >
                View My Orders
              </Button>
            </Link>

          </div>

        </div>

      </Container>

    </section>
  );
}