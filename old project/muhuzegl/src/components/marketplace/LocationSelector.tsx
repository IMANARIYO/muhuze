import {
  rwandaProvinces,
  getDistrictsByProvinceId,
} from "../../data/location/rwanda";

interface Props {
  province: string;
  district: string;

  onProvinceChange: (
    value: string
  ) => void;

  onDistrictChange: (
    value: string
  ) => void;
}

export default function LocationSelector({
  province,
  district,
  onProvinceChange,
  onDistrictChange,
}: Props) {
  const districts =
    getDistrictsByProvinceId(province);

  function handleProvinceChange(
    value: string
  ) {
    onProvinceChange(value);

    // Reset district whenever
    // province changes.
    onDistrictChange("");
  }

  return (
    <div className="space-y-6">

      {/* =========================
          COUNTRY
      ========================== */}

      <div>
        <label className="block mb-2 font-medium">
          Country
        </label>

        <select
          value="rwanda"
          disabled
          className="
            w-full
            rounded-xl
            border
            px-4
            py-3
            bg-gray-100
            text-gray-700
          "
        >
          <option value="rwanda">
            Rwanda
          </option>
        </select>
      </div>

      {/* =========================
          PROVINCE
      ========================== */}

      <div>
        <label className="block mb-2 font-medium">
          Province
        </label>

        <select
          value={province}
          onChange={(e) =>
            handleProvinceChange(
              e.target.value
            )
          }
          className="
            w-full
            rounded-xl
            border
            px-4
            py-3
          "
        >
          <option value="">
            Select Province
          </option>

          {rwandaProvinces.map(
            (provinceItem) => (
              <option
                key={provinceItem.id}
                value={provinceItem.id}
              >
                {provinceItem.name}
              </option>
            )
          )}
        </select>
      </div>

      {/* =========================
          DISTRICT
      ========================== */}

      <div>
        <label className="block mb-2 font-medium">
          District
        </label>

        <select
          value={district}
          onChange={(e) =>
            onDistrictChange(
              e.target.value
            )
          }
          disabled={!province}
          className="
            w-full
            rounded-xl
            border
            px-4
            py-3
            disabled:bg-gray-100
            disabled:text-gray-400
          "
        >
          <option value="">
            {province
              ? "Select District"
              : "Select Province First"}
          </option>

          {districts.map(
            (districtItem) => (
              <option
                key={districtItem.id}
                value={districtItem.id}
              >
                {districtItem.name}
              </option>
            )
          )}
        </select>
      </div>

    </div>
  );
}