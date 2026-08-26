interface Props {
  address: string;
  estimatedDelivery: string;
}

export default function DeliveryInformation({
  address,
  estimatedDelivery,
}: Props) {
  return (
    <div className="bg-white rounded-xl shadow p-6">

      <h2 className="text-xl font-bold mb-4">
        Delivery
      </h2>

      <p>{address}</p>

      <p className="mt-4">

        <strong>Estimated Delivery:</strong>

        {" "}

        {estimatedDelivery}

      </p>

    </div>
  );
}