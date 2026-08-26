import {
  FaShoppingBag,
  FaWallet,
  FaBell,
  FaComments,
  FaShieldAlt,
  FaTruck,
} from "react-icons/fa";

import type { AppFeature } from "./types";

export const appFeatures: AppFeature[] = [
  {
    id: 1,
    title: "Buy & Sell Anywhere",
    icon: FaShoppingBag,
  },
  {
    id: 2,
    title: "Manage Your Wallet",
    icon: FaWallet,
  },
  {
    id: 3,
    title: "Instant Notifications",
    icon: FaBell,
  },
  {
    id: 4,
    title: "Live Chat",
    icon: FaComments,
  },
  {
    id: 5,
    title: "Secure Payments",
    icon: FaShieldAlt,
  },
  {
    id: 6,
    title: "Track Deliveries",
    icon: FaTruck,
  },
];