import { useState } from "react";
import { FaSearch } from "react-icons/fa";
import { useNavigate } from "react-router-dom";

export default function SearchBar() {
  const [search, setSearch] = useState("");
  const navigate = useNavigate();

  const handleSearch = () => {
    if (!search.trim()) return;

    navigate(`/products?search=${encodeURIComponent(search)}`);
  };

  return (
    <div className="hidden md:flex flex-1 max-w-2xl">

      <div
        className="
          flex
          items-center
          w-full
          overflow-hidden
          rounded-xl
          border
          border-gray-300
          bg-white
          shadow-sm
          focus-within:border-blue-600
          focus-within:ring-2
          focus-within:ring-blue-200
          transition
        "
      >

        <input
          type="text"
          placeholder="Search products, sellers or categories..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter") {
              handleSearch();
            }
          }}
          className="
            flex-1
            px-5
            py-3
            outline-none
          "
        />

        <button
          onClick={handleSearch}
          className="
            h-full
            px-6
            bg-blue-600
            text-white
            hover:bg-blue-700
            transition
          "
        >
          <FaSearch />
        </button>

      </div>

    </div>
  );
}