import { useState } from "react";

import Modal from "../ui/Modal";
import Button from "../ui/Button";
import Input from "../ui/Input";

import { useWallet } from "../../context/WalletContext";
import { useToast } from "../ui/Toast";

import {
  FaMobileAlt,
  FaMoneyCheckAlt,
  FaCreditCard,
} from "react-icons/fa";

interface Props {
  isOpen: boolean;
  onClose: () => void;
}

export default function DepositModal({
  isOpen,
  onClose,
}: Props) {
  const [amount, setAmount] = useState("");

  const [paymentMethod, setPaymentMethod] =
    useState("MTN Mobile Money");

  const { deposit } = useWallet();

  const { showToast } = useToast();

  function handleDeposit() {
    const value = Number(amount);

    if (value <= 0) {
      showToast(
        "Please enter a valid amount.",
        "warning"
      );
      return;
    }

    const success = deposit(
      value,
      `${paymentMethod} Deposit`
    );

    if (!success) {
      showToast(
        "Deposit failed.",
        "error"
      );
      return;
    }

    showToast(
      "Money deposited successfully!",
      "success"
    );

    setAmount("");
    setPaymentMethod("MTN Mobile Money");

    onClose();
  }

  return (
    <Modal
      isOpen={isOpen}
      title="Deposit Money"
      onClose={onClose}
    >
      <div className="space-y-6">

        <Input
          label="Amount (RWF)"
          type="number"
          value={amount}
          onChange={(e) =>
            setAmount(e.target.value)
          }
        />

        <div>

          <label className="font-semibold block mb-4">
            Payment Method
          </label>

          <div className="space-y-3">

            <label className="flex items-center gap-3 border rounded-xl p-4 cursor-pointer hover:border-blue-600">

              <input
                type="radio"
                value="MTN Mobile Money"
                checked={
                  paymentMethod ===
                  "MTN Mobile Money"
                }
                onChange={(e) =>
                  setPaymentMethod(
                    e.target.value
                  )
                }
              />

              <FaMobileAlt className="text-yellow-500" />

              MTN Mobile Money

            </label>

            <label className="flex items-center gap-3 border rounded-xl p-4 cursor-pointer hover:border-red-500">

              <input
                type="radio"
                value="Airtel Money"
                checked={
                  paymentMethod ===
                  "Airtel Money"
                }
                onChange={(e) =>
                  setPaymentMethod(
                    e.target.value
                  )
                }
              />

              <FaMoneyCheckAlt className="text-red-500" />

              Airtel Money

            </label>

            <label className="flex items-center gap-3 border rounded-xl p-4 cursor-pointer hover:border-blue-500">

              <input
                type="radio"
                value="Visa / Mastercard"
                checked={
                  paymentMethod ===
                  "Visa / Mastercard"
                }
                onChange={(e) =>
                  setPaymentMethod(
                    e.target.value
                  )
                }
              />

              <FaCreditCard className="text-blue-600" />

              Visa / Mastercard

            </label>

          </div>

        </div>

        <Button
          className="w-full"
          onClick={handleDeposit}
        >
          Deposit Money
        </Button>

      </div>
    </Modal>
  );
}