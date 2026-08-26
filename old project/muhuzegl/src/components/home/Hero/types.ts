export interface HeroButton {
  text: string;
  path: string;
  variant: "primary" | "secondary";
}

export interface HeroStat {
  id: number;
  value: string;
  label: string;
  icon: string;   // ← must be string
}