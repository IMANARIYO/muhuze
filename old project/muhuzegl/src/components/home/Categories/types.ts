import type { IconType } from "react-icons";

export interface Subcategory {
  id: number;
  name: string;
  path: string;
}

export interface Category {
  id: number;
  name: string;
  path: string;
  icon: IconType;
  description: string;
  subcategories: Subcategory[];
}