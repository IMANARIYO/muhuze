import type { NavItem } from "./types";

export const navItems: NavItem[] = [
  { label: "Overview", icon: "LayoutDashboard", href: "/dashboard", roles: ["client", "seller", "admin"] },
  { label: "Browse Products", icon: "ShoppingBag", href: "/dashboard/products", roles: ["client"] },
  { label: "My Cart", icon: "ShoppingCart", href: "/dashboard/cart", roles: ["client"] },
  { label: "My Orders", icon: "Package", href: "/dashboard/orders", roles: ["client"] },
  { label: "Catalog Products", icon: "Package", href: "/dashboard/products", roles: ["seller"] },
  { label: "My Listings", icon: "Tag", href: "/dashboard/listings", roles: ["seller"] },
  { label: "Create Listing", icon: "Plus", href: "/dashboard/listings/new", roles: ["seller"] },
  { label: "Orders Received", icon: "ClipboardList", href: "/dashboard/orders", roles: ["seller"] },
  { label: "My Earnings", icon: "Wallet", href: "/dashboard/earnings", roles: ["seller"] },
  { label: "Seller Profile", icon: "Store", href: "/dashboard/seller", roles: ["seller"] },
  { label: "All Orders", icon: "ClipboardList", href: "/dashboard/orders", roles: ["admin"] },
  { label: "Payments", icon: "CreditCard", href: "/dashboard/payments", roles: ["admin"] },
  { label: "Seller Review", icon: "UserCheck", href: "/dashboard/sellers", roles: ["admin"] },
  { label: "Products", icon: "Package", href: "/dashboard/products", roles: ["admin"] },
  { label: "Listing Review", icon: "Tag", href: "/dashboard/listings", roles: ["admin"] },
  { label: "Catalog Setup", icon: "Layers", href: "/dashboard/catalog", roles: ["admin"] },
  { label: "Users", icon: "Users", href: "/dashboard/users", roles: ["admin"] },
];

export const bottomNavItems: NavItem[] = [
  { label: "Profile", icon: "User", href: "/dashboard/profile", roles: ["client", "seller", "admin"] },
  { label: "Settings", icon: "Settings", href: "/dashboard/settings", roles: ["client", "seller", "admin"] },
];