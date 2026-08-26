import { FaSearch } from "react-icons/fa";

interface SearchInputProps {
  placeholder?: string;
  value?: string;
  onChange?: (value: string) => void;
}

export default function SearchInput({
  placeholder = "Search...",
  value = "",
  onChange,
}: SearchInputProps) {
  return (
    <div className="relative w-full">

      <input
        type="text"
        value={value}
        onChange={(e) => onChange?.(e.target.value)}
        placeholder={placeholder}
        className="
          w-full
          rounded-xl
          border
          border-gray-300
          py-3
          pl-12
          pr-4
          outline-none
          focus:ring-2
          focus:ring-blue-600
          focus:border-blue-600
        "
      />

      <FaSearch
        className="
          absolute
          left-4
          top-1/2
          -translate-y-1/2
          text-gray-500
        "
      />

    </div>
  );
}