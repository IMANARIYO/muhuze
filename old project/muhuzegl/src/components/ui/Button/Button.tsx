import type {
  ButtonHTMLAttributes,
  ReactNode,
} from "react";

import { buttonVariants } from "./buttonVariants";

interface ButtonProps
  extends ButtonHTMLAttributes<HTMLButtonElement> {
  children: ReactNode;

  variant?:
    | "primary"
    | "secondary"
    | "outline"
    | "danger"
    | "success";

  size?: "sm" | "md" | "lg";

  loading?: boolean;
}

const sizeClasses = {
  sm: "px-4 py-2 text-sm",
  md: "px-6 py-3 text-base",
  lg: "px-8 py-4 text-lg",
};

export default function Button({
  children,
  variant = "primary",
  size = "md",
  loading = false,
  disabled,
  className = "",
  ...props
}: ButtonProps) {
  return (
    <button
      {...props}
      disabled={disabled || loading}
      className={`
        rounded-xl
        font-semibold
        transition-all
        duration-300
        hover:scale-105
        disabled:opacity-60
        disabled:cursor-not-allowed
        disabled:hover:scale-100
        ${sizeClasses[size]}
        ${buttonVariants[variant]}
        ${className}
      `}
    >
      {loading ? "Loading..." : children}
    </button>
  );
}