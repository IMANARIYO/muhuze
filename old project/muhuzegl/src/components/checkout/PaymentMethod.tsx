interface Props {
  paymentMethod: string;
  setPaymentMethod: (value: string) => void;
}

export default function PaymentMethod({
  paymentMethod,
  setPaymentMethod,
}: Props) {
  return (
    <div className="mt-12 max-w-2xl">
      <h2 className="text-2xl font-bold mb-6">
        PAYMENT METHOD
      </h2>

      <div className="space-y-4">

        <label className="flex items-center gap-3 cursor-pointer">
          <input
            type="radio"
            name="payment"
            value="MTN Mobile Money"
            checked={
              paymentMethod === "MTN Mobile Money"
            }
            onChange={(e) =>
              setPaymentMethod(e.target.value)
            }
          />

          <span>MTN Mobile Money</span>
        </label>

        <label className="flex items-center gap-3 cursor-pointer">
          <input
            type="radio"
            name="payment"
            value="Airtel Money"
            checked={
              paymentMethod === "Airtel Money"
            }
            onChange={(e) =>
              setPaymentMethod(e.target.value)
            }
          />

          <span>Airtel Money</span>
        </label>

        <label className="flex items-center gap-3 cursor-pointer">
          <input
            type="radio"
            name="payment"
            value="Visa / Mastercard"
            checked={
              paymentMethod === "Visa / Mastercard"
            }
            onChange={(e) =>
              setPaymentMethod(e.target.value)
            }
          />

          <span>Visa / Mastercard</span>
        </label>

        <label className="flex items-center gap-3 cursor-pointer">
          <input
            type="radio"
            name="payment"
            value="Cash on Delivery"
            checked={
              paymentMethod === "Cash on Delivery"
            }
            onChange={(e) =>
              setPaymentMethod(e.target.value)
            }
          />

          <span>Cash on Delivery</span>
        </label>

      </div>
    </div>
  );
}