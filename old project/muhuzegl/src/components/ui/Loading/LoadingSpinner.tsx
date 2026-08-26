import type { LoadingSpinnerProps } from "./types";

export default function LoadingSpinner({
  size = "md",
}: LoadingSpinnerProps) {
  const sizes = {
    sm: "w-6 h-6 border-2",
    md: "w-10 h-10 border-4",
    lg: "w-16 h-16 border-4",
  };

  return (
    <div className="flex justify-center items-center py-10">
      <div
        className={`
          ${sizes[size]}
          border-blue-600
          border-t-transparent
          rounded-full
          animate-spin
        `}
      />
    </div>
  );
}