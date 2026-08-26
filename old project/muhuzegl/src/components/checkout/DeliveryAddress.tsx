import Input from "../../components/ui/Input";

interface Props {
  province: string;
  district: string;
  sector: string;
  streetAddress: string;

  setProvince: (value: string) => void;
  setDistrict: (value: string) => void;
  setSector: (value: string) => void;
  setStreetAddress: (value: string) => void;
}

export default function DeliveryAddress({
  province,
  district,
  sector,
  streetAddress,
  setProvince,
  setDistrict,
  setSector,
  setStreetAddress,
}: Props) {
  return (
    <div className="mt-12 max-w-2xl">

      <h2 className="text-2xl font-bold mb-6">
        DELIVERY ADDRESS
      </h2>

      <div className="space-y-5">

        <Input
          label="Province"
          type="text"
          placeholder="e.g. Kigali City"
          value={province}
          onChange={(e) => setProvince(e.target.value)}
        />

        <Input
          label="District"
          type="text"
          placeholder="e.g. Nyarugenge"
          value={district}
          onChange={(e) => setDistrict(e.target.value)}
        />

        <Input
          label="Sector"
          type="text"
          placeholder="e.g. Kimisagara"
          value={sector}
          onChange={(e) => setSector(e.target.value)}
        />

        <Input
          label="Street Address"
          type="text"
          placeholder="House number, street..."
          value={streetAddress}
          onChange={(e) => setStreetAddress(e.target.value)}
        />

      </div>

    </div>
  );
}