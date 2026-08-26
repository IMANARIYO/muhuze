import {
  FaHome,
  FaThLarge,
  FaStore,
  FaPlusCircle,
  FaCrown,
} from "react-icons/fa";

import type { NavItem } from "./types";

export const navItems: NavItem[] = [
  {
    id: 1,
    label: "Home",
    path: "/",
    icon: FaHome,
  },

  {
    id: 2,
    label: "Categories",
    path: "/categories",
    icon: FaThLarge,
  },

  {
    id: 3,
    label: "Marketplace",
    path: "/marketplace",
    icon: FaStore,
  },

  {
    id: 4,
    label: "Sell",
    path: "/upload-product",
    icon: FaPlusCircle,
  },

  {
    id: 5,
    label: "Premium",
    path: "/premium",
    icon: FaCrown,
  },
];