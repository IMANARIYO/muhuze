import { useNavigate } from "react-router-dom";

import type { Order } from "../../types/order";

import { useOrders } from "../../context/OrderContext";
import { useToast } from "../ui/Toast";

import OrderStatusBadge from "./OrderStatusBadge";
import OrderProducts from "./OrderProducts";
import OrderActions from "./OrderActions";

interface Props {
  order: Order;
}

export default function OrderCard({
  order,
}: Props) {
  const navigate = useNavigate();

  const { updateOrderStatus } =
    useOrders();

  const { showToast } =
    useToast();

  function handleView() {
    navigate(
      `/orders/${order._id}`
    );
  }

  async function handleCancel() {
    try {
      await updateOrderStatus(
        order._id,
        "Cancelled"
      );

      showToast(
        "Order cancelled successfully.",
        "success"
      );
    } catch (error) {
      console.error(
        "Failed to cancel order:",
        error
      );

      showToast(
        "Failed to cancel order.",
        "error"
      );
    }
  }

  return (
    <div
      className="
        border
        rounded-2xl
        p-6
        bg-white
        shadow-sm
      "
    >

      {/* =================================
          HEADER
      ================================= */}

      <div className="flex items-center justify-between">

        <h2 className="text-xl font-bold">
          Order #{order._id}
        </h2>

        <OrderStatusBadge
          status={order.status}
        />

      </div>

      {/* =================================
          ORDER INFORMATION
      ================================= */}

      <div className="mt-5 space-y-2">

        <p>
          <strong>Buyer:</strong>{" "}
          {order.buyer}
        </p>

        <p>
          <strong>Payment Method:</strong>{" "}
          {order.paymentMethod}
        </p>

        <p>
          <strong>Payment Status:</strong>{" "}
          {order.paymentStatus}
        </p>

        <p>
          <strong>Delivery:</strong>{" "}
          {order.deliveryAddress}
        </p>

        <p>
          <strong>Total:</strong>{" "}
          {Number(
            order.total
          ).toLocaleString()}{" "}
          RWF
        </p>

        <p>
          <strong>Date:</strong>{" "}
          {order.createdAt
            ? new Date(
                order.createdAt
              ).toLocaleString()
            : "N/A"}
        </p>

      </div>

      {/* =================================
          PRODUCTS
      ================================= */}

      <OrderProducts
        products={order.products}
      />

      {/* =================================
          ACTIONS
      ================================= */}

      <OrderActions
        onView={handleView}
        onCancel={handleCancel}
        canCancel={
          order.status === "Pending"
        }
      />

    </div>
  );
}