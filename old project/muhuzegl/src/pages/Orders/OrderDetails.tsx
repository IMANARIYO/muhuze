import { useParams } from "react-router-dom";

import Container from "../../components/ui/Container";
import SectionTitle from "../../components/ui/SectionTitle";

import { useOrders } from "../../context/OrderContext";

export default function OrderDetails() {
  const { id } = useParams();

  const { orders } = useOrders();

  const order = orders.find(
    (order) => order._id === id
  );

  if (!order) {
    return (
      <Container>
        <h2 className="text-3xl font-bold">
          Order Not Found
        </h2>
      </Container>
    );
  }

  return (
    <Container>
      <SectionTitle
        title={`Order #${order._id}`}
        subtitle="Track your order"
      />

      {/* ==========================================
          ORDER STATUS
      ========================================== */}

      <div className="mt-10 rounded-2xl border bg-white p-6 shadow-sm">

        <div className="flex items-center justify-between">

          <h2 className="text-2xl font-bold">
            Order Status
          </h2>

          <span
            className={`
              px-4
              py-2
              rounded-full
              font-semibold

              ${
                order.status === "Pending"
                  ? "bg-yellow-100 text-yellow-700"
                  : order.status === "Accepted"
                  ? "bg-blue-100 text-blue-700"
                  : order.status === "Delivered"
                  ? "bg-green-100 text-green-700"
                  : order.status === "Cancelled"
                  ? "bg-red-100 text-red-700"
                  : "bg-gray-100 text-gray-700"
              }
            `}
          >
            {order.status}
          </span>

        </div>

      </div>

      {/* ==========================================
          CUSTOMER INFORMATION
      ========================================== */}

      <div className="mt-6 rounded-2xl border bg-white p-6 shadow-sm">

        <h2 className="text-2xl font-bold">
          Customer Information
        </h2>

        <div className="mt-5 space-y-3 text-gray-700">

          <p>
            <span className="font-semibold">
              Buyer:
            </span>{" "}
            {order.buyer}
          </p>

          <p>
            <span className="font-semibold">
              Buyer ID:
            </span>{" "}
            {order.buyerId}
          </p>

          <p>
            <span className="font-semibold">
              Payment Method:
            </span>{" "}
            {order.paymentMethod}
          </p>

          <p>
            <span className="font-semibold">
              Payment Status:
            </span>{" "}
            {order.paymentStatus}
          </p>

          <p>
            <span className="font-semibold">
              Delivery Address:
            </span>{" "}
            {order.deliveryAddress}
          </p>

        </div>

      </div>

      {/* ==========================================
          PRODUCTS
      ========================================== */}

      <div className="mt-6 rounded-2xl border bg-white p-6 shadow-sm">

        <h2 className="text-2xl font-bold">
          Products
        </h2>

        <div className="mt-5 space-y-4">

          {order.products.map(
            (product, index) => (
              <div
                key={`${product.productId}-${index}`}
                className="
                  flex
                  items-center
                  justify-between
                  gap-4
                  border-b
                  pb-4
                  last:border-b-0
                "
              >

                <div>

                  <h3 className="font-semibold text-lg">
                    Product
                  </h3>

                  <p className="text-gray-500 mt-1">
                    Product ID:{" "}
                    {product.productId}
                  </p>

                  <p className="text-gray-500 mt-1">
                    Quantity:{" "}
                    {product.quantity}
                  </p>

                </div>

              </div>
            )
          )}

        </div>

      </div>

      {/* ==========================================
          ORDER SUMMARY
      ========================================== */}

      <div className="mt-6 rounded-2xl border bg-white p-6 shadow-sm">

        <h2 className="text-2xl font-bold">
          Order Summary
        </h2>

        <div className="mt-5 space-y-4">

          <div className="flex justify-between">

            <span className="text-gray-600">
              Total
            </span>

            <span className="text-2xl font-bold text-blue-600">
              {Number(
                order.total
              ).toLocaleString()}{" "}
              RWF
            </span>

          </div>

          <div className="flex justify-between">

            <span className="text-gray-600">
              Payment Method
            </span>

            <span>
              {order.paymentMethod}
            </span>

          </div>

          <div className="flex justify-between">

            <span className="text-gray-600">
              Payment Status
            </span>

            <span>
              {order.paymentStatus}
            </span>

          </div>

          <div className="flex justify-between">

            <span className="text-gray-600">
              Order Date
            </span>

            <span>
              {new Date(
                order.createdAt
              ).toLocaleString()}
            </span>

          </div>

          <div className="flex justify-between">

            <span className="text-gray-600">
              Last Updated
            </span>

            <span>
              {new Date(
                order.updatedAt
              ).toLocaleString()}
            </span>

          </div>

        </div>

      </div>

    </Container>
  );
}