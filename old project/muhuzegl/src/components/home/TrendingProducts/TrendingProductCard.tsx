import { FaFire, FaMapMarkerAlt, FaStar } from "react-icons/fa";
import { Link } from "react-router-dom";
import type { TrendingProduct } from "./types";

interface Props {
  product: TrendingProduct;
}

export default function TrendingProductCard({ product }: Props) {
  return (
    <div className="bg-white rounded-2xl overflow-hidden shadow-lg hover:shadow-2xl transition duration-300">

      <div className="relative">

        <img
          src={product.image}
          alt={product.name}
          className="w-full h-60 object-cover"
        />

        <div className="absolute top-4 left-4 bg-red-600 text-white px-3 py-1 rounded-full flex items-center gap-2 text-sm">

          <FaFire />

          Trending

        </div>

      </div>

      <div className="p-6">

        <h3 className="text-xl font-bold">
          {product.name}
        </h3>

        <div className="flex gap-3 mt-3">

          <span className="text-blue-600 text-2xl font-bold">
            {product.price}
          </span>

          <span className="line-through text-gray-400">
            {product.oldPrice}
          </span>

        </div>

        <p className="mt-3 text-gray-600">
          {product.seller}
        </p>

        <div className="flex items-center gap-2 mt-2 text-gray-500">

          <FaMapMarkerAlt />

          {product.location}

        </div>

        <div className="flex justify-between mt-4">

          <div className="flex items-center gap-2">

            <FaStar className="text-yellow-500" />

            {product.rating}

          </div>

          <p className="text-sm text-gray-500">

            {product.sold} sold

          </p>

        </div>

        <Link
          to={`/products/${product.id}`}
          className="block mt-6 bg-blue-600 text-white text-center py-3 rounded-xl hover:bg-blue-700"
        >
          View Product
        </Link>

      </div>

    </div>
  );
}