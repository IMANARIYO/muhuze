import {
  FaArrowDown,
  FaArrowUp,
  FaGift,
  FaMoneyBillWave,
} from "react-icons/fa";

import { useWallet } from "../../context/WalletContext";

export default function TransactionHistory() {
  const { transactions } = useWallet();

  function getIcon(type: string) {
    switch (type) {
      case "Deposit":
        return (
          <FaArrowDown className="text-green-600" />
        );

      case "Withdraw":
        return (
          <FaArrowUp className="text-red-600" />
        );

      case "Sale":
        return (
          <FaMoneyBillWave className="text-blue-600" />
        );

      case "Referral":
        return (
          <FaGift className="text-yellow-500" />
        );

      default:
        return null;
    }
  }

  if (transactions.length === 0) {
    return (
      <div className="bg-white rounded-3xl shadow-lg p-12 mt-10 text-center">
        <h2 className="text-2xl font-bold">
          Transaction History
        </h2>

        <p className="text-gray-500 mt-4">
          No transactions available.
        </p>
      </div>
    );
  }

  return (
    <section className="mt-12">
      <h2 className="text-2xl font-bold mb-6">
        Recent Transactions
      </h2>

      <div className="bg-white rounded-3xl shadow-lg overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-slate-100">
              <tr>
                <th className="text-left p-5">
                  Type
                </th>

                <th className="text-left p-5">
                  Description
                </th>

                <th className="text-left p-5">
                  Amount
                </th>

                <th className="text-left p-5">
                  Status
                </th>

                <th className="text-left p-5">
                  Date
                </th>
              </tr>
            </thead>

            <tbody>
              {transactions.map((transaction) => (
                <tr
                  key={transaction.id}
                  className="border-b hover:bg-slate-50"
                >
                  <td className="p-5">
                    <div className="flex items-center gap-3">
                      {getIcon(transaction.type)}

                      {transaction.type}
                    </div>
                  </td>

                  <td className="p-5">
                    {transaction.description}
                  </td>

                  <td className="p-5 font-bold">
                    {transaction.amount.toLocaleString()}{" "}
                    RWF
                  </td>

                  <td className="p-5">
                    <span
                      className="
                        px-3
                        py-1
                        rounded-full
                        bg-green-100
                        text-green-700
                        text-sm
                      "
                    >
                      {transaction.status}
                    </span>
                  </td>

                  <td className="p-5 text-gray-500">
                    {transaction.date}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </section>
  );
}