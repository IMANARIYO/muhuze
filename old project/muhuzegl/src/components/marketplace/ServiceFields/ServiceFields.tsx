import Input from "../../ui/Input";

interface Props {
  serviceCategory: string;
  experience: string;
  availability: string;
  serviceArea: string;
  pricingType: string;

  onServiceCategoryChange: (value: string) => void;
  onExperienceChange: (value: string) => void;
  onAvailabilityChange: (value: string) => void;
  onServiceAreaChange: (value: string) => void;
  onPricingTypeChange: (value: string) => void;
}

export default function ServiceFields({
  serviceCategory,
  experience,
  availability,
  serviceArea,
  pricingType,
  onServiceCategoryChange,
  onExperienceChange,
  onAvailabilityChange,
  onServiceAreaChange,
  onPricingTypeChange,
}: Props) {
  return (
    <div className="space-y-6">

      <h3 className="text-xl font-bold">
        Service Information
      </h3>

      <Input
        label="Service Category"
        value={serviceCategory}
        onChange={(e) =>
          onServiceCategoryChange(e.target.value)
        }
      />

      <Input
        label="Years of Experience"
        type="number"
        value={experience}
        onChange={(e) =>
          onExperienceChange(e.target.value)
        }
      />

      <div>
        <label className="block mb-2 font-medium">
          Availability
        </label>

        <select
          value={availability}
          onChange={(e) =>
            onAvailabilityChange(e.target.value)
          }
          className="w-full rounded-xl border px-4 py-3"
        >
          <option value="">
            Select Availability
          </option>

          <option value="full-time">
            Full Time
          </option>

          <option value="part-time">
            Part Time
          </option>

          <option value="weekends">
            Weekends
          </option>

          <option value="on-demand">
            On Demand
          </option>
        </select>
      </div>

      <Input
        label="Service Area"
        value={serviceArea}
        onChange={(e) =>
          onServiceAreaChange(e.target.value)
        }
      />

      <div>
        <label className="block mb-2 font-medium">
          Pricing Type
        </label>

        <select
          value={pricingType}
          onChange={(e) =>
            onPricingTypeChange(e.target.value)
          }
          className="w-full rounded-xl border px-4 py-3"
        >
          <option value="">
            Select Pricing
          </option>

          <option value="hourly">
            Per Hour
          </option>

          <option value="daily">
            Per Day
          </option>

          <option value="weekly">
            Per Week
          </option>

          <option value="monthly">
            Per Month
          </option>

          <option value="fixed">
            Fixed Price
          </option>
        </select>
      </div>

    </div>
  );
}