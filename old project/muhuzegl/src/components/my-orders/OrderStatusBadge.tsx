import type { OrderStatus } from "../../types/order";

interface Props {
  status: OrderStatus;
}

export default function OrderStatusBadge({
  status,
}: Props) {
  const styles: Record<OrderStatus, string> = {
    Pending:
      "bg-yellow-100 text-yellow-700",

    Accepted:
      "bg-blue-100 text-blue-700",

    Preparing:
      "bg-purple-100 text-purple-700",

    Shipped:
      "bg-indigo-100 text-indigo-700",

    Delivered:
      "bg-green-100 text-green-700",

    Cancelled:
      "bg-gray-200 text-gray-700",

    Rejected:
      "bg-red-100 text-red-700",
  };

  return (
    <span
      className={`px-3 py-1 rounded-full font-medium ${styles[status]}`}
    >
      {status}
    </span>
  );
}