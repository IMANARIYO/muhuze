import { Link } from "react-router-dom";

import type { Category } from "./types";

interface CategoryCardProps {
  category: Category;
}

export default function CategoryCard({
  category,
}: CategoryCardProps) {
  return (
    <Link
      to={`/marketplace/category/${category.id}`}
      className="
        group
        bg-white
        rounded-3xl
        overflow-hidden
        shadow-lg
        hover:shadow-2xl
        transition
        duration-300
      "
    >
      <img
        src={category.image}
        alt={category.name}
        className="
          w-full
          h-52
          object-cover
          group-hover:scale-105
          transition
          duration-300
        "
      />

      <div className="p-6">
        <h2 className="text-2xl font-bold">
          {category.name}
        </h2>

        <p className="text-gray-500 mt-2">
          {category.description}
        </p>

        <div className="mt-5 flex items-center justify-between">
          <span className="text-blue-600 font-semibold">
            {category.productCount} Products
          </span>

          <span className="text-sm text-gray-400 group-hover:text-blue-600">
            View →
          </span>
        </div>
      </div>
    </Link>
  );
}