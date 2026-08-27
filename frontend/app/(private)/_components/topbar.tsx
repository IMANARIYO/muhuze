"use client";

import { usePathname } from "next/navigation";
import { Bell, Menu, Search } from "lucide-react";
import { Button } from "@/app/_components/ui/button";
import { Avatar } from "@/app/_components/ui/avatar";

interface TopbarProps {
  onMenuClick: () => void;
}

const breadcrumbMap: Record<string, string> = {
  "/dashboard": "Overview",
  "/dashboard/products": "Products",
  "/dashboard/cart": "My Cart",
  "/dashboard/orders": "Orders",
  "/dashboard/earnings": "My Earnings",
  "/dashboard/payments": "Payments",
  "/dashboard/users": "Users",
  "/dashboard/profile": "Profile",
  "/dashboard/settings": "Settings",
};

export function Topbar({ onMenuClick }: TopbarProps) {
  const pathname = usePathname();
  const current = breadcrumbMap[pathname] ?? "Overview";

  return (
    <header className="flex min-h-[68px] items-center justify-between border-b border-[var(--line)] bg-[rgba(251,252,250,0.82)] px-6 backdrop-blur-md lg:px-10">
      <Button
        variant="ghost"
        size="icon"
        className="lg:hidden"
        onClick={onMenuClick}
        aria-label="Open menu"
      >
        <Menu size={20} />
      </Button>

      <div className="flex items-center gap-2.5 text-xs text-[#a0a8a3]">
        <span>Dashboard</span>
        <span className="text-[#ccd1cd]">/</span>
        <span className="font-semibold text-[var(--ink)]">{current}</span>
      </div>

      <div className="flex items-center gap-4">
        <div className="hidden items-center gap-2 border-b border-[var(--line)] md:flex">
          <Search size={15} className="text-[#8d9892]" />
          <input
            type="text"
            placeholder="Search..."
            className="w-44 bg-transparent py-1.5 text-xs text-[var(--ink)] outline-none placeholder:text-[#8d9892]"
          />
          <kbd className="rounded border border-[var(--line)] px-1.5 py-0.5 text-[9px] text-[var(--muted)]">
            ⌘K
          </kbd>
        </div>

        <button
          className="relative rounded-lg p-2 text-[#73807a] transition-colors hover:bg-[#edf1ed] hover:text-[var(--ink)]"
          aria-label="Notifications"
        >
          <Bell size={18} />
          <span className="absolute right-1.5 top-1.5 h-1.5 w-1.5 rounded-full bg-[var(--coral)]" />
        </button>

        <Avatar initials="AM" size="sm" />
      </div>
    </header>
  );
}
