import { forwardRef, type InputHTMLAttributes } from "react";
import { cn } from "@/app/lib/utils";

const Input = forwardRef<HTMLInputElement, InputHTMLAttributes<HTMLInputElement>>(
  ({ className, type, ...props }, ref) => {
    return (
      <input
        type={type}
        className={cn(
          "flex h-10 w-full rounded-lg border border-[var(--line)] bg-white px-3 py-2 text-sm text-[var(--ink)] placeholder:text-[var(--muted)] focus:border-[var(--teal)] focus:outline-none focus:ring-1 focus:ring-[var(--teal)] disabled:cursor-not-allowed disabled:opacity-50",
          className
        )}
        ref={ref}
        {...props}
      />
    );
  }
);
Input.displayName = "Input";

export { Input };
