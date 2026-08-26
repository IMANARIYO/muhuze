import type {
  HeroButton,
} from "./types";

/**
 * ==========================================
 * HERO ACTION BUTTONS
 * ==========================================
 */

export const heroButtons: HeroButton[] = [
  {
    text: "Start Shopping",
    path: "/products",
    variant: "primary",
  },
  {
    text: "Become a Seller",
    path: "/register",
    variant: "secondary",
  },
];