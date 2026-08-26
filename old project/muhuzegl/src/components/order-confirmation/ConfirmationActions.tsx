import { Link } from "react-router-dom";
import Button from "../ui/Button";

export default function ConfirmationActions() {
  return (
    <div className="grid md:grid-cols-2 gap-4">

      <Link to="/marketplace">

        <Button className="w-full">
          Continue Shopping
        </Button>

      </Link>

      <Link to="/my-orders">

        <Button
          variant="outline"
          className="w-full"
        >
          View My Orders
        </Button>

      </Link>

    </div>
  );
}