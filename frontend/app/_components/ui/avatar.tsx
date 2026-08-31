import type { HTMLAttributes } from "react";
import { cn } from "@/app/lib/utils";

interface AvatarProps extends HTMLAttributes<HTMLDivElement> {
  initials: string;
  color?: string;
  size?: "sm" | "md" | "lg";
}

const sizeClasses = {
  sm: "h-8 w-8 text-[10px]",
  md: "h-10 w-10 text-xs",
  lg: "h-12 w-12 text-sm",
};

function Avatar({ className, initials, color, size = "md", ...props }: AvatarProps) {
  return (
    <div
      className={cn(
        "inline-flex items-center justify-center rounded-full font-bold text-white",
        sizeClasses[size],
        className
      )}
      style={{ backgroundColor: color || "#d7896d" }}
      {...props}
    >
      {initials}
    </div>
  );
}

export { Avatar };
