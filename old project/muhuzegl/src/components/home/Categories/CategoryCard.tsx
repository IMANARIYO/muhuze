import { Link } from "react-router-dom";
import {
  FaArrowRight,
  FaLayerGroup,
} from "react-icons/fa";

import type { Category } from "./types";

interface Props {
  category: Category;
}

export default function CategoryCard({
  category,
}: Props) {
  const Icon = category.icon;

  return (
    <Link
      to={category.path}
      className="
        group
        relative
        overflow-hidden
        rounded-3xl
        border
        border-slate-100
        bg-white
        p-7
        shadow-sm
        transition-all
        duration-300
        hover:-translate-y-2
        hover:border-blue-100
        hover:shadow-2xl
      "
    >

      {/* Orange accent */}
      <div
        className="
          absolute
          right-0
          top-0
          h-24
          w-24
          rounded-bl-full
          bg-orange-50
          transition
          group-hover:bg-orange-100
        "
      />

      {/* Icon */}
      <div
        className="
          relative
          flex
          h-16
          w-16
          items-center
          justify-center
          rounded-2xl
          bg-blue-50
          text-blue-600
          transition-all
          duration-300
          group-hover:bg-blue-600
          group-hover:text-white
        "
      >
        <Icon className="text-3xl" />
      </div>

      {/* Content */}
      <h3
        className="
          mt-6
          text-xl
          font-bold
          text-slate-900
        "
      >
        {category.name}
      </h3>

      <p
        className="
          mt-3
          min-h-[48px]
          text-sm
          leading-6
          text-slate-500
        "
      >
        {category.description}
      </p>

      {/* Subcategory indicator */}
      <div
        className="
          mt-5
          flex
          items-center
          gap-2
          text-sm
          font-semibold
          text-blue-600
        "
      >
        <FaLayerGroup />

        {category.subcategories.length} subcategories

      </div>

      {/* Browse */}
      <div
        className="
          mt-5
          flex
          items-center
          gap-2
          text-sm
          font-bold
          text-orange-500
          transition
          group-hover:gap-3
        "
      >
        Explore category

        <FaArrowRight />
      </div>

    </Link>
  );
}