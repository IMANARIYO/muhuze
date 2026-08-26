import Button from "../ui/Button";

interface Props {
  onView?: () => void;
  onCancel?: () => void;

  canCancel?: boolean;
}

export default function OrderActions({
  onView,
  onCancel,
  canCancel = true,
}: Props) {
  return (
    <div className="mt-6 flex flex-wrap gap-4">

      <Button
        variant="primary"
        onClick={onView}
      >
        View Details
      </Button>

      <Button
        variant="danger"
        onClick={onCancel}
        disabled={!canCancel}
      >
        Cancel Order
      </Button>

    </div>
  );
}