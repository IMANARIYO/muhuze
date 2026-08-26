import {
  FaShieldAlt,
  FaCreditCard,
  FaTruck,
  FaHeadset,
} from "react-icons/fa";

import type { WhyChoose } from "./types";

export const whyChooseItems: WhyChoose[] = [
  {
    id: 1,
    title: "Verified Sellers",
    description:
      "Every seller is verified to help buyers shop with confidence.",
    icon: FaShieldAlt,
  },
  {
    id: 2,
    title: "Secure Payments",
    description:
      "Safe payment options with trusted financial partners.",
    icon: FaCreditCard,
  },
  {
    id: 3,
    title: "Fast Delivery",
    description:
      "Quick and reliable delivery across Africa.",
    icon: FaTruck,
  },
  {
    id: 4,
    title: "24/7 Support",
    description:
      "Our support team is always ready to help buyers and sellers.",
    icon: FaHeadset,
  },
];