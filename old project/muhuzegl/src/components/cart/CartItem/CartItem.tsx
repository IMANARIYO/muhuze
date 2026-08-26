import { useCart } from "../../../context/CartContext";
import type { CartItem } from "../../../types/cart";

interface Props {
  item: CartItem;
}

export default function CartItem({
  item,
}: Props) {
  const {
    increaseQuantity,
    decreaseQuantity,
    removeFromCart,
  } = useCart();

  return (
    <div
      className="
        flex
        items-center
        justify-between
        border
        rounded-xl
        p-6
        mb-4
      "
    >
      <div className="flex items-center gap-5">

        <img
          src={item.item.images[0]}
          alt={item.item.title}
          className="
            w-28
            h-28
            object-cover
            rounded-lg
          "
        />

        <div>

          <h3 className="text-xl font-bold">
            {item.item.title}
          </h3>

          <p className="text-gray-500">
            {item.item.category}
          </p>

          <p className="text-blue-600 font-bold mt-2">
            {item.item.price.toLocaleString()}{" "}
            {item.item.currency}
          </p>

        </div>

      </div>

      <div className="flex items-center gap-3">

        <button
          onClick={() =>
            decreaseQuantity(item.item._id)
          }
          className="
            w-8
            h-8
            rounded-full
            bg-gray-300
          "
        >
          -
        </button>

        <span className="font-bold">
          {item.quantity}
        </span>

        <button
          onClick={() =>
            increaseQuantity(item.item._id)
          }
          className="
            w-8
            h-8
            rounded-full
            bg-blue-600
            text-white
          "
        >
          +
        </button>

        <button
          onClick={() =>
            removeFromCart(item.item._id)
          }
          className="
            w-8
            h-8
            rounded-full
            bg-red-600
            text-white
          "
        >
          ×
        </button>

      </div>
    </div>
  );
}