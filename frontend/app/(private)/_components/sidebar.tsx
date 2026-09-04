"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import {
  CircleHelp,
  ClipboardList,
  CreditCard,
  LayoutDashboard,
  Layers,
  LogOut,
  Package,
  Plus,
  Settings,
  ShoppingBag,
  ShoppingCart,
  Tag,
  Store,
  User,
  UserCheck,
  Users,
  Wallet,
  TrendingUp,
} from "lucide-react";
import { Button } from "@/app/_components/ui/button";
import { cn } from "@/app/lib/utils";
import { navItems, bottomNavItems } from "@/app/lib/data";
import type { UserRole } from "@/app/lib/types";
import { RoleSwitcher } from "./role-switcher";
import { useAuth } from "@/app/context/auth-context";
import { useRouter } from "next/navigation";
import { cartService } from "@/app/services/cart.service";

const iconMap: Record<string, React.ComponentType<{ size?: number }>> = {
  LayoutDashboard,
  ShoppingBag,
  ShoppingCart,
  Tag,
  Package,
  Plus,
  Store,
  ClipboardList,
  Wallet,
  CreditCard,
  Layers,
  Users,
  User,
  UserCheck,
  Settings,
  TrendingUp,
};

interface SidebarProps {
  role: UserRole;
  onRoleChange: (role: UserRole) => void;
  availableRoles: string[];
  mobileOpen: boolean;
  onMobileClose: () => void;
}

export function Sidebar({ role, onRoleChange, availableRoles, mobileOpen, onMobileClose }: SidebarProps) {
  const pathname = usePathname();
  const router = useRouter();
  const { user, logout } = useAuth();
  const [cartCount, setCartCount] = useState<number | null>(null);

  useEffect(() => {
    if (role !== "client" || !user) return;
    let cancelled = false;
    cartService
      .get()
      .then((cart) => { if (!cancelled) setCartCount(cart.item_count); })
      .catch(() => { if (!cancelled) setCartCount(0); });
    return () => { cancelled = true; };
  }, [role, user]);

  const filteredNav = navItems.filter((item) => item.roles.includes(role));
  const filteredBottom = bottomNavItems.filter((item) => item.roles.includes(role));

  async function handleLogout() {
    await logout();
    onMobileClose();
    router.replace("/");
  }

  return (
    <aside
      className={cn(
        "flex h-screen w-60 shrink-0 flex-col overflow-hidden border-r border-[var(--line)] bg-[#fbfcfa] transition-transform duration-200",
        "fixed inset-y-0 left-0 z-30 lg:sticky lg:top-0 lg:translate-x-0",
        mobileOpen ? "translate-x-0" : "-translate-x-full"
      )}
    >
      {/* Brand */}
      <div className="flex items-center gap-2.5 px-5 pb-6 pt-5">
        <div className="grid h-8 w-8 place-items-center rounded-lg bg-[var(--ink)] text-sm font-extrabold text-[#d6f34d] -rotate-6">
          M
        </div>
        <span className="text-xl font-extrabold tracking-tight text-[var(--ink)]">
          muhuze<span className="text-[var(--coral)]">.</span>
        </span>
        <Button
          variant="ghost"
          size="icon"
          className="ml-auto lg:hidden"
          onClick={onMobileClose}
          aria-label="Close menu"
        >
          &times;
        </Button>
      </div>

      {/* Role Switcher */}
      <div className="px-3 pb-4">
        <RoleSwitcher role={role} onRoleChange={onRoleChange} availableRoles={availableRoles} />
      </div>

      {/* Main Nav */}
      <div className="px-4 pb-1">
        <p className="mb-2 text-[10px] font-bold uppercase tracking-[0.1em] text-[#a4aaa6]">
          {role === "admin" ? "Management" : role === "seller" ? "Seller Hub" : "Shopping"}
        </p>
      </div>

      <nav className="flex flex-1 flex-col gap-0.5 px-3" aria-label="Main navigation">
        {filteredNav.map((item) => {
          const Icon = iconMap[item.icon];
          const isActive =
            item.href === "/dashboard"
              ? pathname === "/dashboard"
              : pathname.startsWith(item.href);

          return (
            <Link
              key={item.label}
              href={item.href}
              onClick={onMobileClose}
              className={cn(
                "flex items-center gap-3 rounded-lg px-3 py-2.5 text-[13px] transition-colors",
                isActive
                  ? "bg-[#e8f3ed] font-bold text-[var(--ink)]"
                  : "text-[#67736e] hover:bg-[#e8f3ed] hover:text-[var(--ink)]"
              )}
            >
              {Icon && <Icon size={17} />}
              <span className="flex-1">{item.label}</span>
              {item.href === "/dashboard/cart" && role === "client" && cartCount !== null && cartCount > 0 && (
                <span className="rounded-full bg-[#d5f2e2] px-2 py-0.5 text-[10px] font-semibold text-[#39836e]">
                  {cartCount}
                </span>
              )}
            </Link>
          );
        })}

        <div className="my-3 border-t border-[var(--line)]" />

        <p className="mb-2 px-3 text-[10px] font-bold uppercase tracking-[0.1em] text-[#a4aaa6]">
          Account
        </p>

        {filteredBottom.map((item) => {
          const Icon = iconMap[item.icon];
          const isActive = pathname === item.href;

          return (
            <Link
              key={item.label}
              href={item.href}
              onClick={onMobileClose}
              className={cn(
                "flex items-center gap-3 rounded-lg px-3 py-2.5 text-[13px] transition-colors",
                isActive
                  ? "bg-[#e8f3ed] font-bold text-[var(--ink)]"
                  : "text-[#67736e] hover:bg-[#e8f3ed] hover:text-[var(--ink)]"
              )}
            >
              {Icon && <Icon size={17} />}
              <span>{item.label}</span>
            </Link>
          );
        })}
      </nav>

      {/* Footer */}
      <div className="mt-auto flex items-center gap-2.5 border-t border-[var(--line)] px-4 py-4">
        <div className="grid h-7 w-7 place-items-center rounded-lg bg-[#f0e9d8] text-[#c29142]">
          <CircleHelp size={15} />
        </div>
        <div className="flex-1">
          <p className="truncate text-[11px] font-bold text-[var(--ink)]">{user?.email ?? "Need help?"}</p>
          <p className="text-[10px] text-[var(--muted)]">{user ? "Account connected" : "Visit our help center"}</p>
        </div>
        {user && (
          <Button variant="ghost" size="icon" onClick={handleLogout} aria-label="Log out" title="Log out">
            <LogOut size={15} />
          </Button>
        )}
      </div>
    </aside>
  );
}
