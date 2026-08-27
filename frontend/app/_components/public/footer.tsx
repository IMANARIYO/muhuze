import Link from "next/link";

const footerLinks = {
  Marketplace: [
    { label: "Browse Products", href: "/dashboard/products" },
    { label: "Sell on Muhuze", href: "/dashboard/products/new" },
    { label: "How It Works", href: "#how-it-works" },
  ],
  Company: [
    { label: "About", href: "#" },
    { label: "Blog", href: "#" },
    { label: "Careers", href: "#" },
  ],
  Support: [
    { label: "Help Center", href: "#" },
    { label: "Contact", href: "#" },
    { label: "Privacy", href: "#" },
  ],
};

export function Footer() {
  return (
    <footer className="border-t border-[var(--line)] bg-white">
      <div className="mx-auto max-w-6xl px-6 py-12">
        <div className="grid gap-10 md:grid-cols-4">
          <div>
            <Link href="/" className="flex items-center gap-2.5">
              <div className="grid h-7 w-7 place-items-center rounded-lg bg-[var(--ink)] text-xs font-extrabold text-[#d6f34d] -rotate-6">
                M
              </div>
              <span className="text-lg font-extrabold tracking-tight text-[var(--ink)]">
                muhuze<span className="text-[var(--coral)]">.</span>
              </span>
            </Link>
            <p className="mt-3 max-w-xs text-sm leading-relaxed text-[var(--muted)]">
              A transparent marketplace connecting clients, sellers, and admins in one platform.
            </p>
          </div>

          {Object.entries(footerLinks).map(([category, links]) => (
            <div key={category}>
              <h4 className="mb-3 text-xs font-bold uppercase tracking-wider text-[var(--ink)]">
                {category}
              </h4>
              <ul className="flex flex-col gap-2">
                {links.map((link) => (
                  <li key={link.label}>
                    <a
                      href={link.href}
                      className="text-sm text-[var(--muted)] transition-colors hover:text-[var(--ink)]"
                    >
                      {link.label}
                    </a>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        <div className="mt-10 flex flex-col items-center justify-between gap-4 border-t border-[var(--line)] pt-8 md:flex-row">
          <p className="text-xs text-[var(--muted)]">
            &copy; {new Date().getFullYear()} Muhuze. All rights reserved.
          </p>
          <div className="flex gap-5">
            <a href="#" className="text-xs text-[var(--muted)] hover:text-[var(--ink)]">Terms</a>
            <a href="#" className="text-xs text-[var(--muted)] hover:text-[var(--ink)]">Privacy</a>
            <a href="#" className="text-xs text-[var(--muted)] hover:text-[var(--ink)]">Cookies</a>
          </div>
        </div>
      </div>
    </footer>
  );
}
