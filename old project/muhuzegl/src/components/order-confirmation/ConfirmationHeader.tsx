import { FaCheckCircle } from "react-icons/fa";

export default function ConfirmationHeader() {
  return (
    <div className="text-center">

      <FaCheckCircle
        className="mx-auto text-7xl text-green-500"
      />

      <h1 className="text-4xl font-bold mt-6">
        Order Placed Successfully
      </h1>

      <p className="text-gray-500 mt-3">
        Thank you for shopping with MUHUZE.
      </p>

    </div>
  );
}