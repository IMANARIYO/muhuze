import Container from "../../ui/Container";
import Button from "../../ui/Button";

export default function MarketplaceHero() {
  return (
    <section className="bg-slate-100 py-20">
      <Container>

        <div className="max-w-4xl mx-auto text-center">

          <h1 className="text-5xl font-bold text-slate-900">
            Explore the MUHUZE Global Link Marketplace
          </h1>

          <p className="mt-6 text-xl text-slate-600">
            Buy products, rent properties, hire professionals,
            and discover jobs across Africa.
          </p>

          <div className="mt-10 flex gap-3">

            <input
              type="text"
              placeholder="Search products, rentals, jobs or services..."
              className="
                flex-1
                rounded-xl
                border
                px-5
                py-4
                text-lg
              "
            />

            <Button>
              Search
            </Button>

          </div>

          <div className="mt-10 flex justify-center gap-4 flex-wrap">

            <span className="rounded-full bg-white px-5 py-2 shadow">
              🛒 Products
            </span>

            <span className="rounded-full bg-white px-5 py-2 shadow">
              🏠 Rentals
            </span>

            <span className="rounded-full bg-white px-5 py-2 shadow">
              🛠 Services
            </span>

            <span className="rounded-full bg-white px-5 py-2 shadow">
              💼 Jobs
            </span>

          </div>

        </div>

      </Container>
    </section>
  );
}