import { FaTruck, FaShieldAlt } from "react-icons/fa";
import { useCart } from "../../context/CartContext";

export default function OrderReview() {
  const { cart } = useCart();

  const subtotal = cart.reduce(
    (sum, item) =>
      sum + item.item.price * item.quantity,
    0
  );

  const deliveryFee = cart.length > 0 ? 2000 : 0;

  const total = subtotal + deliveryFee;

  const totalItems = cart.reduce(
    (sum, item) => sum + item.quantity,
    0
  );

  const estimatedDelivery = new Date();
  estimatedDelivery.setDate(
    estimatedDelivery.getDate() + 3
  );

  return (
    <div className="bg-white rounded-2xl shadow-md p-6 sticky top-24">

      <h2 className="text-2xl font-bold mb-6">
        Order Review
      </h2>

      <div className="space-y-5">

        {cart.map((cartItem) => (

          <div
            key={cartItem.item._id}
            className="flex justify-between border-b pb-4"
          >
            <div>

              <h3 className="font-semibold">
                {cartItem.item.title}
              </h3>

              <p className="text-sm text-gray-500">
                Qty: {cartItem.quantity}
              </p>

            </div>

            <span className="font-semibold">

              {(cartItem.item.price * cartItem.quantity).toLocaleString()} RWF

            </span>

          </div>

        ))}

      </div>

      <div className="mt-6 space-y-3">

        <div className="flex justify-between">

          <span>Total Items</span>

          <span>{totalItems}</span>

        </div>

        <div className="flex justify-between">

          <span>Subtotal</span>

          <span>{subtotal.toLocaleString()} RWF</span>

        </div>

        <div className="flex justify-between">

          <span>Delivery</span>

          <span>{deliveryFee.toLocaleString()} RWF</span>

        </div>

        <hr />

        <div className="flex justify-between text-2xl font-bold">

          <span>Total</span>

          <span className="text-blue-600">
            {total.toLocaleString()} RWF
          </span>

        </div>

      </div>

      <div className="mt-8 border-t pt-6 space-y-4">

        <div className="flex items-center gap-3">

          <FaTruck className="text-blue-600" />

          <div>

            <p className="font-semibold">
              Estimated Delivery
            </p>

            <p className="text-sm text-gray-500">
              {estimatedDelivery.toDateString()}
            </p>

          </div>

        </div>

        <div className="flex items-center gap-3">

          <FaShieldAlt className="text-green-600" />

          <div>

            <p className="font-semibold">
              Secure Checkout
            </p>

            <p className="text-sm text-gray-500">
              Your payment is protected.
            </p>

          </div>

        </div>

      </div>

    </div>
  );
}