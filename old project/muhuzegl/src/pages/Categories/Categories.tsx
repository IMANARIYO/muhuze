import Container from "../../components/ui/Container";
import SectionTitle from "../../components/ui/SectionTitle";

import {
  CategoryBanner,
  CategoryFilter,
  CategoryGrid,
} from "../../components/categories";

export default function Categories() {
  return (
    <section className="py-16 bg-slate-50 min-h-screen">
      <Container>

        <SectionTitle
          title="Marketplace Categories"
          subtitle="Browse products by category."
        />

        <CategoryBanner />

        <CategoryFilter />

        <CategoryGrid />

      </Container>
    </section>
  );
}