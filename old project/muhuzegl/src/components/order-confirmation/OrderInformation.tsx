interface Props {
  orderNumber: string;
  orderDate: string;
}

export default function OrderInformation({
  orderNumber,
  orderDate,
}: Props) {
  return (
    <div className="bg-white rounded-xl shadow p-6">

      <h2 className="text-xl font-bold mb-4">
        Order Information
      </h2>

      <p>
        <strong>Order Number:</strong>
        {" "}
        {orderNumber}
      </p>

      <p>
        <strong>Date:</strong>
        {" "}
        {orderDate}
      </p>

    </div>
  );
}