export type UserRole = "client" | "seller" | "admin";

export interface NavItem {
  label: string;
  icon: string;
  href: string;
  roles: UserRole[];
}