import Input from "../../ui/Input";

interface Props {
  brand: string;
  model: string;
  condition: string;
  quantity: string;
  warranty: string;

  onBrandChange: (value: string) => void;
  onModelChange: (value: string) => void;
  onConditionChange: (value: string) => void;
  onQuantityChange: (value: string) => void;
  onWarrantyChange: (value: string) => void;
}

export default function ProductFields({
  brand,
  model,
  condition,
  quantity,
  warranty,
  onBrandChange,
  onModelChange,
  onConditionChange,
  onQuantityChange,
  onWarrantyChange,
}: Props) {
  return (
    <div className="space-y-6">

      <h3 className="text-xl font-bold">
        Product Information
      </h3>

      <Input
        label="Brand"
        value={brand}
        onChange={(e) =>
          onBrandChange(e.target.value)
        }
      />

      <Input
        label="Model"
        value={model}
        onChange={(e) =>
          onModelChange(e.target.value)
        }
      />

      <div>
        <label className="block mb-2 font-medium">
          Condition
        </label>

        <select
          value={condition}
          onChange={(e) =>
            onConditionChange(e.target.value)
          }
          className="w-full rounded-xl border px-4 py-3"
        >
          <option value="">
            Select Condition
          </option>

          <option value="new">New</option>
          <option value="like-new">
            Like New
          </option>
          <option value="used">
            Used
          </option>
          <option value="refurbished">
            Refurbished
          </option>
        </select>
      </div>

      <Input
        label="Quantity"
        type="number"
        value={quantity}
        onChange={(e) =>
          onQuantityChange(e.target.value)
        }
      />

      <Input
        label="Warranty"
        value={warranty}
        onChange={(e) =>
          onWarrantyChange(e.target.value)
        }
      />

    </div>
  );
}