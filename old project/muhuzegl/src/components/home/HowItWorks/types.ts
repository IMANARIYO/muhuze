import type { IconType } from "react-icons/lib";

export interface Step {
  id: number;
  title: string;
  description: string;
  icon: IconType;
}