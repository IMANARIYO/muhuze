import Button from "../../components/ui/Button";

interface Props {
  onPlaceOrder: () => void;
}

export default function PlaceOrderButton({
  onPlaceOrder,
}: Props) {
  return (
    <div className="mt-8 max-w-2xl">
      <Button
        className="w-full"
        onClick={onPlaceOrder}
      >
        Place Order
      </Button>
    </div>
  );
}