interface Props {
  method: string;
}

export default function PaymentInformation({
  method,
}: Props) {
  return (
    <div className="bg-white rounded-xl shadow p-6">

      <h2 className="text-xl font-bold mb-4">
        Payment
      </h2>

      <p>{method}</p>

    </div>
  );
}