export default function CategoryFilter() {
  return (
    <div className="mt-10">
      <input
        type="text"
        placeholder="Search categories..."
        className="
          w-full
          border
          rounded-xl
          px-5
          py-4
          outline-none
          focus:ring-2
          focus:ring-blue-600
        "
      />
    </div>
  );
}