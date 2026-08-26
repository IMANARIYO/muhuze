import { FaCheckCircle } from "react-icons/fa";
import type { Seller } from "./types";

export const sellers: Seller[] = [
  {
    id: 1,
    name: "Apple Store Rwanda",
    location: "Kigali",
    rating: 4.9,
    products: 125,
    avatar: "/images/sellers/apple-store.jpg",
    verified: true,
    badge: FaCheckCircle,
  },
  {
    id: 2,
    name: "Computer World",
    location: "Musanze",
    rating: 4.8,
    products: 94,
    avatar: "/images/sellers/computer-world.jpg",
    verified: true,
    badge: FaCheckCircle,
  },
  {
    id: 3,
    name: "Fashion Hub",
    location: "Huye",
    rating: 4.7,
    products: 167,
    avatar: "/images/sellers/fashion-hub.jpg",
    verified: true,
    badge: FaCheckCircle,
  },
  {
    id: 4,
    name: "Auto Market",
    location: "Rubavu",
    rating: 4.9,
    products: 58,
    avatar: "/images/sellers/auto-market.jpg",
    verified: true,
    badge: FaCheckCircle,
  },
];