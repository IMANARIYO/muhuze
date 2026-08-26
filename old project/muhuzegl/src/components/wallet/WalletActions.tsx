import Button from "../ui/Button";

interface WalletActionsProps {
  onDeposit: () => void;
  onWithdraw: () => void;
}

export default function WalletActions({
  onDeposit,
  onWithdraw,
}: WalletActionsProps) {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 gap-6 mt-8">
      <Button
        variant="primary"
        className="w-full"
        onClick={onDeposit}
      >
        Deposit Money
      </Button>

      <Button
        variant="secondary"
        className="w-full"
        onClick={onWithdraw}
      >
        Withdraw Money
      </Button>
    </div>
  );
}