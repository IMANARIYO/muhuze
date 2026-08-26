import { useWallet } from "../../context/WalletContext";

export default function WalletBalance() {
  const { balance } = useWallet();

  return (
    <div
      className="
        rounded-3xl
        bg-gradient-to-r
        from-blue-600
        to-indigo-700
        text-white
        p-8
        shadow-xl
      "
    >
      <p className="text-lg opacity-90">
        Available Balance
      </p>

      <h2 className="text-5xl font-bold mt-4">
        {balance.toLocaleString()} RWF
      </h2>

      <p className="mt-4 opacity-80">
        Your available wallet balance.
      </p>
    </div>
  );
}