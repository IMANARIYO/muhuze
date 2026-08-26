import { FaArrowRight } from "react-icons/fa6";
import CategoryCard from "./CategoryCard";
import { categories } from "./categoryData";

export default function Categories() {
  return (
    <section
      className="
        bg-gradient-to-b
        from-white
        to-slate-50
        py-16
      "
    >
      <div className="mx-auto max-w-7xl px-6">

        {/* Section Header */}
        <div className="mx-auto max-w-3xl text-center">

          <span
            className="
              font-semibold
              uppercase
              tracking-[0.2em]
              text-blue-600
            "
          >
            Marketplace Categories
          </span>

          <h2
            className="
              mt-4
              text-4xl
              font-extrabold
              tracking-tight
              text-slate-950
              lg:text-5xl
            "
          >
            Explore MUHUZE
          </h2>

          <p
            className="
              mt-5
              text-lg
              leading-8
              text-slate-600
            "
          >
            Discover products, services and
            opportunities across our growing
            marketplace. Choose a category to
            explore what's available.
          </p>

        </div>

        {/* Category Grid */}
        <div
          className="
            mt-12
            grid
            grid-cols-1
            gap-6
            sm:grid-cols-2
            lg:grid-cols-3
            xl:grid-cols-4
          "
        >
          {categories.map((category) => (
            <CategoryCard
              key={category.id}
              category={category}
            />
          ))}
        </div>

        {/* Bottom CTA */}
        <div className="mt-12 text-center">

          <p className="text-slate-500">
            Can't find what you're looking for?
          </p>

          <a
            href="/products"
            className="
              mt-3
              inline-flex
              items-center
              gap-2
              font-bold
              text-blue-600
              transition
              hover:text-orange-500
            "
          >
            Explore the full marketplace

            <FaArrowRight />
          </a>

        </div>

      </div>
    </section>
  );
}