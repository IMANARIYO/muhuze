import type { ReactNode } from "react";
import { badgeVariants } from "./badgeVariants";

interface BadgeProps {
  children: ReactNode;

  variant?:
    | "success"
    | "warning"
    | "danger"
    | "primary"
    | "premium"
    | "trending";
}

export default function Badge({
  children,
  variant = "primary",
}: BadgeProps) {
  return (
    <span
      className={`
        inline-flex
        items-center
        rounded-full
        px-3
        py-1
        text-sm
        font-semibold
        ${badgeVariants[variant]}
      `}
    >
      {children}
    </span>
  );
}