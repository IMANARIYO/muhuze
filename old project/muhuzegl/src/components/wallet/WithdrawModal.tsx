import { useState } from "react";

import Modal from "../ui/Modal";
import Button from "../ui/Button";
import Input from "../ui/Input";

import { useWallet } from "../../context/WalletContext";
import { useToast } from "../ui/Toast";

import {
  FaMobileAlt,
  FaMoneyCheckAlt,
  FaUniversity,
} from "react-icons/fa";

interface Props {
  isOpen: boolean;
  onClose: () => void;
}

export default function WithdrawModal({
  isOpen,
  onClose,
}: Props) {
  const [amount, setAmount] = useState("");

  const [paymentMethod, setPaymentMethod] =
    useState("MTN Mobile Money");

  const [account, setAccount] = useState("");

  const { withdraw } = useWallet();

  const { showToast } = useToast();

  function handleWithdraw() {
    const value = Number(amount);

    if (value <= 0) {
      showToast(
        "Please enter a valid amount.",
        "warning"
      );
      return;
    }

    if (!account.trim()) {
      showToast(
        "Please enter your phone number or account number.",
        "warning"
      );
      return;
    }

    const success = withdraw(
      value,
      `${paymentMethod} Withdrawal`
    );

    if (!success) {
      showToast(
        "Insufficient wallet balance.",
        "error"
      );
      return;
    }

    showToast(
      "Withdrawal request submitted successfully.",
      "success"
    );

    setAmount("");
    setAccount("");
    setPaymentMethod("MTN Mobile Money");

    onClose();
  }

  return (
    <Modal
      isOpen={isOpen}
      title="Withdraw Money"
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

        <Input
          label="Phone Number / Account Number"
          type="text"
          placeholder="Enter your phone or bank account"
          value={account}
          onChange={(e) =>
            setAccount(e.target.value)
          }
        />

        <div>

          <label className="font-semibold block mb-4">
            Withdraw To
          </label>

          <div className="space-y-3">

            <label className="flex items-center gap-3 border rounded-xl p-4 cursor-pointer hover:border-yellow-500">

              <input
                type="radio"
                value="MTN Mobile Money"
                checked={
                  paymentMethod ===
                  "MTN Mobile Money"
                }
                onChange={(e) =>
                  setPaymentMethod(e.target.value)
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
                  setPaymentMethod(e.target.value)
                }
              />

              <FaMoneyCheckAlt className="text-red-500" />

              Airtel Money

            </label>

            <label className="flex items-center gap-3 border rounded-xl p-4 cursor-pointer hover:border-blue-600">

              <input
                type="radio"
                value="Bank Account"
                checked={
                  paymentMethod ===
                  "Bank Account"
                }
                onChange={(e) =>
                  setPaymentMethod(e.target.value)
                }
              />

              <FaUniversity className="text-blue-600" />

              Bank Account

            </label>

          </div>

        </div>

        <Button
          variant="secondary"
          className="w-full"
          onClick={handleWithdraw}
        >
          Withdraw Money
        </Button>

      </div>
    </Modal>
  );
}