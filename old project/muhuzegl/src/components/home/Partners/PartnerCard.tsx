import type { Partner } from "./types";

interface Props {
  partner: Partner;
}

export default function PartnerCard({ partner }: Props) {
  return (
    <div className="bg-white rounded-xl shadow hover:shadow-lg transition p-6 flex items-center justify-center">

      <img
        src={partner.logo}
        alt={partner.name}
        className="h-16 object-contain"
      />

    </div>
  );
}