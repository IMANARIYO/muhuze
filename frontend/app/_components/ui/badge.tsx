import type { HTMLAttributes } from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/app/lib/utils";

const badgeVariants = cva(
  "inline-flex items-center rounded-md border px-2.5 py-0.5 text-xs font-semibold transition-colors",
  {
    variants: {
      variant: {
        default: "border-transparent bg-[var(--ink)] text-white",
        secondary: "border-transparent bg-[#e8f3ed] text-[#39836e]",
        outline: "border-[var(--line)] text-[var(--muted)]",
        coral: "border-transparent bg-[#fbe6e0] text-[#d75e4a]",
        blue: "border-transparent bg-[#e4edfa] text-[#577ebd]",
        yellow: "border-transparent bg-[#fbf0ce] text-[#b58a24]",
        teal: "border-transparent bg-[#d5f2e2] text-[#39836e]",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  }
);

export interface BadgeProps
  extends HTMLAttributes<HTMLSpanElement>,
    VariantProps<typeof badgeVariants> {}

function Badge({ className, variant, ...props }: BadgeProps) {
  return (
    <span className={cn(badgeVariants({ variant }), className)} {...props} />
  );
}

export { Badge, badgeVariants };
