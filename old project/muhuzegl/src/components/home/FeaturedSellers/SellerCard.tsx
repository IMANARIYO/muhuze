import { Link } from "react-router-dom";
import type { Seller } from "./types";
import { FaMapMarkerAlt, FaStar, FaCheckCircle } from "react-icons/fa";

interface Props {
  seller: Seller;
}

export default function SellerCard({ seller }: Props) {
  return (
    <div className="bg-white rounded-2xl shadow-lg overflow-hidden hover:shadow-2xl transition">

      <img
        src={seller.image}
        alt={seller.name}
        className="w-full h-56 object-cover"
      />

      <div className="p-6">

        <div className="flex items-center gap-2">

          <h3 className="text-xl font-bold">
            {seller.name}
          </h3>

          {seller.verified && (
            <FaCheckCircle className="text-blue-600" />
          )}

        </div>

        <div className="flex items-center gap-2 mt-3 text-gray-500">

          <FaMapMarkerAlt />

          {seller.location}

        </div>

        <div className="flex items-center gap-2 mt-3">

          <FaStar className="text-yellow-500" />

          {seller.rating}

        </div>

        <p className="mt-3">
          {seller.products} Products
        </p>

        <Link
          to={`/seller/${seller.id}`}
          className="block mt-6 text-center bg-blue-600 text-white py-3 rounded-xl hover:bg-blue-700"
        >
          Visit Store
        </Link>

      </div>

    </div>
  );
}