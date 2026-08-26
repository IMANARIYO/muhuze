import type { FooterSection } from "./types";

export const footerSections: FooterSection[] = [
  {
    title: "Marketplace",
    links: [
      { label: "Products", path: "/products" },
      { label: "Categories", path: "/categories" },
      { label: "Sell Product", path: "/seller" },
      { label: "Wallet", path: "/wallet" },
      { label: "Referral", path: "/referral" },
    ],
  },

  {
    title: "Company",
    links: [
      { label: "About Us", path: "/about" },
      { label: "Careers", path: "/careers" },
      { label: "Blog", path: "/blog" },
      { label: "Contact", path: "/contact" },
    ],
  },

  {
    title: "Support",
    links: [
      { label: "Help Center", path: "/help" },
      { label: "Privacy Policy", path: "/privacy" },
      { label: "Terms & Conditions", path: "/terms" },
      { label: "FAQs", path: "/faq" },
    ],
  },
];