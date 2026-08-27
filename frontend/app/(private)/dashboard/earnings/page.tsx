import { TrendingUp, Wallet } from "lucide-react";
import { Card, CardContent } from "@/app/_components/ui/card";
import { earnings, COMMISSION_RATE } from "@/app/lib/data";

const payoutColors: Record<string, { bg: string; text: string }> = {
  pending: { bg: "#fbf0ce", text: "#b58a24" },
  sent:    { bg: "#e8f4ed", text: "#2d7a5e" },
  failed:  { bg: "#fbe6e0", text: "#d75e4a" },
};

export default function EarningsPage() {
  const totalEarned = earnings.filter((e) => e.payoutStatus === "sent").reduce((s, e) => s + e.netAmount, 0);
  const pendingAmount = earnings.filter((e) => e.payoutStatus === "pending").reduce((s, e) => s + e.netAmount, 0);
  const totalGross = earnings.reduce((s, e) => s + e.grossAmount, 0);
  const totalCommission = earnings.reduce((s, e) => s + e.commission, 0);

  return (
    <div className="mx-auto max-w-4xl space-y-6">
      <div>
        <h1 className="text-2xl font-extrabold tracking-tight text-[var(--ink)]">My Earnings</h1>
        <p className="mt-1 text-sm text-[var(--muted)]">
          Track your sales revenue and payout history. Platform commission: {COMMISSION_RATE * 100}%.
        </p>
      </div>

      {/* Summary cards */}
      <div className="grid gap-4 sm:grid-cols-3">
        <Card className="border-[#bdded1] bg-[#e8f4ed]">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <span className="text-xs text-[#78857f]">Total Received</span>
              <Wallet size={16} className="text-[#59ac88]" />
            </div>
            <p className="mt-3 text-3xl font-extrabold tracking-tight text-[var(--ink)]">
              ${totalEarned.toFixed(2)}
            </p>
            <p className="mt-1 text-[11px] text-[#9aa39e]">After commission</p>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <span className="text-xs text-[#78857f]">Pending Payout</span>
              <TrendingUp size={16} className="text-[#a7b0aa]" />
            </div>
            <p className="mt-3 text-3xl font-extrabold tracking-tight text-[var(--ink)]">
              ${pendingAmount.toFixed(2)}
            </p>
            <p className="mt-1 text-[11px] text-[#9aa39e]">Awaiting admin transfer</p>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <span className="text-xs text-[#78857f]">Commission Paid</span>
              <Wallet size={16} className="text-[#a7b0aa]" />
            </div>
            <p className="mt-3 text-3xl font-extrabold tracking-tight text-[var(--ink)]">
              ${totalCommission.toFixed(2)}
            </p>
            <p className="mt-1 text-[11px] text-[#9aa39e]">
              From ${totalGross.toFixed(2)} gross
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Earnings table */}
      <Card>
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead>
                <tr className="border-b border-[var(--line)] bg-[#f9fbf9]">
                  <th className="px-5 py-3 text-left font-bold text-[var(--muted)]">Product</th>
                  <th className="px-5 py-3 text-left font-bold text-[var(--muted)]">Client</th>
                  <th className="px-5 py-3 text-right font-bold text-[var(--muted)]">Gross</th>
                  <th className="px-5 py-3 text-right font-bold text-[var(--muted)]">Commission</th>
                  <th className="px-5 py-3 text-right font-bold text-[var(--muted)]">Net</th>
                  <th className="px-5 py-3 text-left font-bold text-[var(--muted)]">Status</th>
                  <th className="px-5 py-3 text-left font-bold text-[var(--muted)]">Date</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#eff1ef]">
                {earnings.map((e) => {
                  const pc = payoutColors[e.payoutStatus];
                  return (
                    <tr key={e.id} className="hover:bg-[#f9fbf9]">
                      <td className="px-5 py-3 font-semibold text-[var(--ink)]">{e.productName}</td>
                      <td className="px-5 py-3 text-[var(--muted)]">{e.clientName}</td>
                      <td className="px-5 py-3 text-right text-[var(--ink)]">${e.grossAmount.toFixed(2)}</td>
                      <td className="px-5 py-3 text-right text-[var(--coral)]">-${e.commission.toFixed(2)}</td>
                      <td className="px-5 py-3 text-right font-bold text-[var(--ink)]">${e.netAmount.toFixed(2)}</td>
                      <td className="px-5 py-3">
                        <span
                          className="rounded-full px-2.5 py-0.5 text-[10px] font-semibold capitalize"
                          style={{ backgroundColor: pc.bg, color: pc.text }}
                        >
                          {e.payoutStatus}
                        </span>
                      </td>
                      <td className="px-5 py-3 text-[var(--muted)]">{e.createdAt}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
