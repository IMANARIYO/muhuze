import {
  FaUserPlus,
  FaIdBadge,
  FaSearch,
  FaShoppingCart,
  FaMoneyCheckAlt,
  FaCheckCircle,
} from "react-icons/fa";

import type { Step } from "./types";

export const steps: Step[] = [
  {
    id: 1,
    title: "Create Account",
    description: "Register for free as a buyer or seller.",
    icon: FaUserPlus,
  },
  {
    id: 2,
    title: "Verify Profile",
    description: "Verify your identity to build trust.",
    icon: FaIdBadge,
  },
  {
    id: 3,
    title: "Browse or Upload",
    description: "Shop products or start selling.",
    icon: FaSearch,
  },
  {
    id: 4,
    title: "Buy or Sell",
    description: "Trade securely with verified users.",
    icon: FaShoppingCart,
  },
  {
    id: 5,
    title: "Secure Payment",
    description: "Pay safely using trusted payment methods.",
    icon: FaMoneyCheckAlt,
  },
  {
    id: 6,
    title: "Complete Transaction",
    description: "Receive your order or your earnings.",
    icon: FaCheckCircle,
  },
];