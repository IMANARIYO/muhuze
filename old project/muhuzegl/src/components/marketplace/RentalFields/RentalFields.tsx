import Input from "../../ui/Input";

interface Props {
  category: string;
  subCategory: string;

  rentalPeriod: string;
  condition: string;
  quantity: string;
  securityDeposit: string;
  availability: string;

  propertyType: string;
  bedrooms: string;
  bathrooms: string;
  parking: string;
  furnished: boolean;

  vehicleType: string;
  make: string;
  model: string;
  year: string;
  transmission: string;
  seats: string;

  equipmentType: string;
  eventType: string;

  onRentalPeriodChange: (value: string) => void;
  onConditionChange: (value: string) => void;
  onQuantityChange: (value: string) => void;
  onSecurityDepositChange: (value: string) => void;
  onAvailabilityChange: (value: string) => void;

  onPropertyTypeChange: (value: string) => void;
  onBedroomsChange: (value: string) => void;
  onBathroomsChange: (value: string) => void;
  onParkingChange: (value: string) => void;
  onFurnishedChange: (value: boolean) => void;

  onVehicleTypeChange: (value: string) => void;
  onMakeChange: (value: string) => void;
  onModelChange: (value: string) => void;
  onYearChange: (value: string) => void;
  onTransmissionChange: (value: string) => void;
  onSeatsChange: (value: string) => void;

  onEquipmentTypeChange: (value: string) => void;
  onEventTypeChange: (value: string) => void;
}

export default function RentalFields({
  category,
  rentalPeriod,
  condition,
  quantity,
  securityDeposit,
  availability,

  propertyType,
  bedrooms,
  bathrooms,
  parking,
  furnished,

  vehicleType,
  make,
  model,
  year,
  transmission,
  seats,

  equipmentType,
  eventType,

  onRentalPeriodChange,
  onConditionChange,
  onQuantityChange,
  onSecurityDepositChange,
  onAvailabilityChange,

  onPropertyTypeChange,
  onBedroomsChange,
  onBathroomsChange,
  onParkingChange,
  onFurnishedChange,

  onVehicleTypeChange,
  onMakeChange,
  onModelChange,
  onYearChange,
  onTransmissionChange,
  onSeatsChange,

  onEquipmentTypeChange,
  onEventTypeChange,
}: Props) {
  const isProperty =
    category === "rental-properties";

  const isVehicle =
    category === "rental-vehicles";

  const isEquipment =
    category === "rental-equipment";

  const isElectronics =
    category === "rental-electronics";

  const isEventParty =
    category === "event-party";

  return (
    <div className="space-y-6">

      <h3 className="text-xl font-bold">
        Rental Information
      </h3>

      {/* =========================
          PROPERTY RENTAL
      ========================== */}

      {isProperty && (
        <>
          <Input
            label="Property Type"
            value={propertyType}
            onChange={(e) =>
              onPropertyTypeChange(
                e.target.value
              )
            }
          />

          <Input
            label="Bedrooms"
            type="number"
            value={bedrooms}
            onChange={(e) =>
              onBedroomsChange(
                e.target.value
              )
            }
          />

          <Input
            label="Bathrooms"
            type="number"
            value={bathrooms}
            onChange={(e) =>
              onBathroomsChange(
                e.target.value
              )
            }
          />

          <Input
            label="Parking Spaces"
            type="number"
            value={parking}
            onChange={(e) =>
              onParkingChange(
                e.target.value
              )
            }
          />

          <label className="flex items-center gap-3">
            <input
              type="checkbox"
              checked={furnished}
              onChange={(e) =>
                onFurnishedChange(
                  e.target.checked
                )
              }
            />

            <span>Furnished</span>
          </label>
        </>
      )}

      {/* =========================
          VEHICLE RENTAL
      ========================== */}

      {isVehicle && (
        <>
          <Input
            label="Vehicle Type"
            value={vehicleType}
            onChange={(e) =>
              onVehicleTypeChange(
                e.target.value
              )
            }
          />

          <Input
            label="Make"
            value={make}
            onChange={(e) =>
              onMakeChange(
                e.target.value
              )
            }
          />

          <Input
            label="Model"
            value={model}
            onChange={(e) =>
              onModelChange(
                e.target.value
              )
            }
          />

          <Input
            label="Year"
            type="number"
            value={year}
            onChange={(e) =>
              onYearChange(
                e.target.value
              )
            }
          />

          <div>
            <label className="block mb-2 font-medium">
              Transmission
            </label>

            <select
              value={transmission}
              onChange={(e) =>
                onTransmissionChange(
                  e.target.value
                )
              }
              className="w-full rounded-xl border px-4 py-3"
            >
              <option value="">
                Select Transmission
              </option>

              <option value="automatic">
                Automatic
              </option>

              <option value="manual">
                Manual
              </option>
            </select>
          </div>

          <Input
            label="Seats"
            type="number"
            value={seats}
            onChange={(e) =>
              onSeatsChange(
                e.target.value
              )
            }
          />
        </>
      )}

      {/* =========================
          EQUIPMENT RENTAL
      ========================== */}

      {isEquipment && (
        <>
          <Input
            label="Equipment Type"
            value={equipmentType}
            onChange={(e) =>
              onEquipmentTypeChange(
                e.target.value
              )
            }
          />

          <Input
            label="Quantity Available"
            type="number"
            value={quantity}
            onChange={(e) =>
              onQuantityChange(
                e.target.value
              )
            }
          />

          <Input
            label="Condition"
            value={condition}
            onChange={(e) =>
              onConditionChange(
                e.target.value
              )
            }
          />

          <Input
            label="Availability"
            value={availability}
            onChange={(e) =>
              onAvailabilityChange(
                e.target.value
              )
            }
          />
        </>
      )}

      {/* =========================
          ELECTRONICS RENTAL
      ========================== */}

      {isElectronics && (
        <>
          <Input
            label="Equipment Type"
            value={equipmentType}
            onChange={(e) =>
              onEquipmentTypeChange(
                e.target.value
              )
            }
          />

          <Input
            label="Condition"
            value={condition}
            onChange={(e) =>
              onConditionChange(
                e.target.value
              )
            }
          />

          <Input
            label="Quantity Available"
            type="number"
            value={quantity}
            onChange={(e) =>
              onQuantityChange(
                e.target.value
              )
            }
          />

          <Input
            label="Availability"
            value={availability}
            onChange={(e) =>
              onAvailabilityChange(
                e.target.value
              )
            }
          />
        </>
      )}

      {/* =========================
          EVENT & PARTY
      ========================== */}

      {isEventParty && (
        <>
          <Input
            label="Event Type"
            value={eventType}
            onChange={(e) =>
              onEventTypeChange(
                e.target.value
              )
            }
          />

          <Input
            label="Equipment Type"
            value={equipmentType}
            onChange={(e) =>
              onEquipmentTypeChange(
                e.target.value
              )
            }
          />

          <Input
            label="Quantity Available"
            type="number"
            value={quantity}
            onChange={(e) =>
              onQuantityChange(
                e.target.value
              )
            }
          />

          <Input
            label="Condition"
            value={condition}
            onChange={(e) =>
              onConditionChange(
                e.target.value
              )
            }
          />
        </>
      )}

      {/* =========================
          COMMON RENTAL FIELDS
      ========================== */}

      <div>
        <label className="block mb-2 font-medium">
          Rental Period
        </label>

        <select
          value={rentalPeriod}
          onChange={(e) =>
            onRentalPeriodChange(
              e.target.value
            )
          }
          className="w-full rounded-xl border px-4 py-3"
        >
          <option value="">
            Select Period
          </option>

          <option value="hourly">
            Hourly
          </option>

          <option value="daily">
            Daily
          </option>

          <option value="weekly">
            Weekly
          </option>

          <option value="monthly">
            Monthly
          </option>

          <option value="yearly">
            Yearly
          </option>
        </select>
      </div>

      {!isProperty && (
        <Input
          label="Security Deposit"
          type="number"
          value={securityDeposit}
          onChange={(e) =>
            onSecurityDepositChange(
              e.target.value
            )
          }
        />
      )}

    </div>
  );
}