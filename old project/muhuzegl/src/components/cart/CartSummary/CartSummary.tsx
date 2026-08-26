import { Link } from "react-router-dom";
import { useCart } from "../../../context/CartContext";
export default function CartSummary() {
  const { cart } = useCart();

  const totalItems = cart.reduce(
    (sum, item) => sum + item.quantity,
    0
  );

  const subtotal = cart.reduce(
    (sum, item) =>
      sum +
      item.item.price * item.quantity,
    0
  );

  const deliveryFee =
    cart.length > 0 ? 2000 : 0;

  const total =
    subtotal + deliveryFee;

  return (
    <div
      className="
        border
        rounded-xl
        p-6
        bg-white
        shadow-sm
      "
    >
      <h2 className="text-2xl font-bold">
        Order Summary
      </h2>

      <div className="mt-6 space-y-4">

        <div className="flex justify-between">
          <span>Items</span>

          <span>{totalItems}</span>
        </div>

        <div className="flex justify-between">
          <span>Subtotal</span>

          <span>
            {subtotal.toLocaleString()} RWF
          </span>
        </div>

        <div className="flex justify-between">
          <span>Delivery</span>

          <span>
            {deliveryFee.toLocaleString()} RWF
          </span>
        </div>

        <hr />

        <div className="flex justify-between text-2xl font-bold">

          <span>Total</span>

          <span className="text-blue-600">
            {total.toLocaleString()} RWF
          </span>

        </div>

      </div>

      <div className="mt-8 space-y-4">

        <Link to="/marketplace">

          <button
            className="
              w-full
              border
              border-blue-600
              text-blue-600
              py-3
              rounded-xl
            "
          >
            Continue Shopping
          </button>

        </Link>

        <Link to="/checkout">

          <button
            className="
              w-full
              bg-blue-600
              text-white
              py-3
              rounded-xl
            "
          >
            Proceed to Checkout
          </button>

        </Link>

      </div>
    </div>
  );
}