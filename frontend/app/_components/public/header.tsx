"use client";

import { useState } from "react";
import Link from "next/link";
import { LogOut, Menu, X } from "lucide-react";
import { Button } from "@/app/_components/ui/button";
import { useAuth } from "@/app/context/auth-context";

const navLinks = [
  { label: "How It Works", href: "#how-it-works" },
  { label: "For Sellers", href: "#how-it-works" },
  { label: "For Clients", href: "#how-it-works" },
];

export function Header() {
  const [mobileOpen, setMobileOpen] = useState(false);
  const { isAuthenticated, logout } = useAuth();

  async function handleLogout() {
    await logout();
    setMobileOpen(false);
  }

  return (
    <header className="sticky top-0 z-50 border-b border-[var(--line)] bg-white/80 backdrop-blur-md">
      <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-6">
        <Link href="/" className="flex items-center gap-2.5">
          <div className="grid h-8 w-8 place-items-center rounded-lg bg-[var(--ink)] text-[14px] font-extrabold text-[#d6f34d] -rotate-6">
            M
          </div>
          <span className="text-xl font-extrabold tracking-tight text-[var(--ink)]">
            muhuze<span className="text-[var(--coral)]">.</span>
          </span>
        </Link>

        <nav className="hidden items-center gap-8 md:flex">
          {navLinks.map((link) => (
            <a
              key={link.label}
              href={link.href}
              className="text-sm font-medium text-[var(--muted)] transition-colors hover:text-[var(--ink)]"
            >
              {link.label}
            </a>
          ))}
        </nav>

        <div className="hidden items-center gap-3 md:flex">
          {isAuthenticated ? (
            <Button variant="ghost" size="sm" onClick={handleLogout}>
              <LogOut size={14} /> Log out
            </Button>
          ) : (
            <>
              <Link href="/login">
                <Button variant="ghost" size="sm">Log in</Button>
              </Link>
              <Link href="/register">
                <Button size="sm">Get Started</Button>
              </Link>
            </>
          )}
        </div>

        <Button
          variant="ghost"
          size="icon"
          className="md:hidden"
          onClick={() => setMobileOpen(!mobileOpen)}
          aria-label="Toggle menu"
        >
          {mobileOpen ? <X size={20} /> : <Menu size={20} />}
        </Button>
      </div>

      {mobileOpen && (
        <div className="border-t border-[var(--line)] bg-white px-6 py-4 md:hidden">
          <nav className="flex flex-col gap-3">
            {navLinks.map((link) => (
              <a
                key={link.label}
                href={link.href}
                className="text-sm font-medium text-[var(--muted)] hover:text-[var(--ink)]"
                onClick={() => setMobileOpen(false)}
              >
                {link.label}
              </a>
            ))}
            <hr className="border-[var(--line)]" />
            {isAuthenticated ? (
              <Button variant="ghost" size="sm" className="w-full justify-start" onClick={handleLogout}>
                <LogOut size={15} /> Log out
              </Button>
            ) : (
              <>
                <Link href="/login">
                  <Button variant="ghost" size="sm" className="w-full justify-start">Log in</Button>
                </Link>
                <Link href="/register">
                  <Button size="sm" className="w-full">Get Started</Button>
                </Link>
              </>
            )}
          </nav>
        </div>
      )}
    </header>
  );
}
