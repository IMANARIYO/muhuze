export default function CategoryBanner() {
  return (
    <section
      className="
        rounded-3xl
        bg-gradient-to-r
        from-blue-700
        via-indigo-600
        to-purple-700
        text-white
        p-12
      "
    >
      <h1 className="text-5xl font-bold">
        Browse Categories
      </h1>

      <p className="mt-5 text-lg text-blue-100 max-w-2xl">
        Discover thousands of products across
        different categories on MUHUZE
        Marketplace.
      </p>
    </section>
  );
}