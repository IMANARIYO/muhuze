import CategoryCard from "./CategoryCard";
import { categories } from "./categoryData";

export default function CategoryGrid() {
  return (
    <section className="mt-10">
      <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-8">
        {categories.map((category) => (
          <CategoryCard
            key={category.id}
            category={category}
          />
        ))}
      </div>
    </section>
  );
}