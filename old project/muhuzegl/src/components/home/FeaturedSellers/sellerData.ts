import type { Seller } from "./types";

export const sellers: Seller[] = [
  {
    id: 1,
    name: "Tech Store Kigali",
    image: "/images/sellers/seller1.jpg",
    location: "Kigali",
    verified: true,
    rating: 4.9,
    products: 120,
  },
  {
    id: 2,
    name: "Auto Rwanda",
    image: "/images/sellers/seller2.jpg",
    location: "Musanze",
    verified: true,
    rating: 4.8,
    products: 95,
  },
  {
    id: 3,
    name: "Dream Homes",
    image: "/images/sellers/seller3.jpg",
    location: "Huye",
    verified: true,
    rating: 5.0,
    products: 40,
  },
];