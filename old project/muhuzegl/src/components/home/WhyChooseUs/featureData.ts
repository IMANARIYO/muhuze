import {
  FaShieldAlt,
  FaTruck,
  FaHeadset,
  FaUserCheck,
  FaMobileAlt,
  FaGlobeAfrica,
} from "react-icons/fa";

import type { Feature } from "./types";

export const features: Feature[] = [
  {
    id: 1,
    title: "Secure Payments",
    description: "Your transactions are protected with secure payment methods.",
    icon: FaShieldAlt,
  },
  {
    id: 2,
    title: "Fast Delivery",
    description: "Reliable delivery across Rwanda and East Africa.",
    icon: FaTruck,
  },
  {
    id: 3,
    title: "24/7 Support",
    description: "Our support team is always ready to help.",
    icon: FaHeadset,
  },
  {
    id: 4,
    title: "Verified Sellers",
    description: "Buy confidently from trusted and verified sellers.",
    icon: FaUserCheck,
  },
  {
    id: 5,
    title: "Mobile Friendly",
    description: "Shop anywhere using your phone, tablet or computer.",
    icon: FaMobileAlt,
  },
  {
    id: 6,
    title: "East Africa Marketplace",
    description: "Connect buyers and sellers across the region.",
    icon: FaGlobeAfrica,
  },
];