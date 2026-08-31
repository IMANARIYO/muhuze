"use client";

import { useEffect, useState } from "react";
import { CheckCircle, CreditCard, Send } from "lucide-react";
import { Card, CardContent } from "@/app/_components/ui/card";
import { revenueService, type RevenueTransactionResponse } from "@/app/services/revenue.service";
import { rwf } from "@/app/lib/utils";

const payoutColors: Record<string, { bg: string; text: string }> = {
  held: { bg: "#fbf0ce", text: "#b58a24" },
  released: { bg: "#e8f4ed", text: "#2d7a5e" },
};

export default function PaymentsPage() {
  const [txns, setTxns] = useState<RevenueTransactionResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;
    revenueService
      .all()
      .then((rows) => { if (!cancelled) setTxns(rows); })
      .catch((caught) => { if (!cancelled) setError(caught instanceof Error ? caught.message : "Payments could not be loaded."); })
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, []);

  const totalRevenue = txns.reduce((s, t) => s + t.amount, 0);
  const totalCommission = txns.reduce((s, t) => s + t.commission_amount, 0);
  const pendingPayouts = txns.filter((t) => t.status === "held");
  const pendingPayoutAmount = pendingPayouts.reduce((s, t) => s + t.seller_earning, 0);

  return (
    <div className="mx-auto max-w-5xl space-y-6">
      <div>
        <h1 className="text-2xl font-extrabold tracking-tight text-[var(--ink)]">Payments</h1>
        <p className="mt-1 text-sm text-[var(--muted)]">
          The MUHUZE commission split, derived the moment a payment clears. Earnings are held until the buyer confirms receipt.
        </p>
      </div>

      {/* Summary */}
      <div className="grid gap-4 sm:grid-cols-3">
        <Card className="border-[#bdded1] bg-[#e8f4ed]">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <span className="text-xs text-[#78857f]">Gross volume</span>
              <CreditCard size={16} className="text-[#59ac88]" />
            </div>
            <p className="mt-3 text-3xl font-extrabold tracking-tight text-[var(--ink)]">{rwf(totalRevenue)}</p>
            <p className="mt-1 text-[11px] text-[#9aa39e]">Cleared payments</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <span className="text-xs text-[#78857f]">Platform commission</span>
              <CheckCircle size={16} className="text-[#a7b0aa]" />
            </div>
            <p className="mt-3 text-3xl font-extrabold tracking-tight text-[var(--ink)]">{rwf(totalCommission)}</p>
            <p className="mt-1 text-[11px] text-[#9aa39e]">7% premium / 12% basic</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <span className="text-xs text-[#78857f]">Held payouts</span>
              <Send size={16} className="text-[#a7b0aa]" />
            </div>
            <p className="mt-3 text-3xl font-extrabold tracking-tight text-[var(--ink)]">{pendingPayouts.length}</p>
            <p className="mt-1 text-[11px] text-[#9aa39e]">{rwf(pendingPayoutAmount)} awaiting receipt</p>
          </CardContent>
        </Card>
      </div>

      {/* Transactions table */}
      <Card>
        <CardContent className="p-0">
          {loading ? (
            <div className="p-10 text-center text-sm text-[var(--muted)]">Loading payments…</div>
          ) : error ? (
            <p role="alert" className="m-5 rounded-lg bg-[#fbe6e0] px-4 py-3 text-sm text-[#b74d3b]">{error}</p>
          ) : txns.length === 0 ? (
            <div className="p-14 text-center">
              <p className="font-bold">No payments yet</p>
              <p className="mt-2 text-sm text-[var(--muted)]">Once buyers complete MOMO payments, the split appears here.</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-xs">
                <thead>
                  <tr className="border-b border-[var(--line)] bg-[#f9fbf9]">
                    <th className="px-5 py-3 text-left font-bold text-[var(--muted)]">Order</th>
                    <th className="px-5 py-3 text-left font-bold text-[var(--muted)]">Payment</th>
                    <th className="px-5 py-3 text-right font-bold text-[var(--muted)]">Amount</th>
                    <th className="px-5 py-3 text-right font-bold text-[var(--muted)]">Commission</th>
                    <th className="px-5 py-3 text-right font-bold text-[var(--muted)]">Seller gets</th>
                    <th className="px-5 py-3 text-left font-bold text-[var(--muted)]">Status</th>
                    <th className="px-5 py-3 text-left font-bold text-[var(--muted)]">Date</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#eff1ef]">
                  {txns.map((txn) => {
                    const pc = payoutColors[txn.status] ?? payoutColors.held;
                    return (
                      <tr key={txn.id} className="hover:bg-[#f9fbf9]">
                        <td className="px-5 py-3 font-semibold text-[var(--ink)]">#{txn.order_id.slice(0, 8)}</td>
                        <td className="px-5 py-3 font-mono text-[10px] text-[var(--muted)]">{txn.payment_id.slice(0, 8)}</td>
                        <td className="px-5 py-3 text-right font-bold text-[var(--ink)]">{rwf(txn.amount)}</td>
                        <td className="px-5 py-3 text-right text-[var(--teal)]">{rwf(txn.commission_amount)}</td>
                        <td className="px-5 py-3 text-right font-bold text-[var(--ink)]">{rwf(txn.seller_earning)}</td>
                        <td className="px-5 py-3">
                          <span className="rounded-full px-2.5 py-0.5 text-[10px] font-semibold capitalize" style={{ backgroundColor: pc.bg, color: pc.text }}>
                            {txn.status}
                          </span>
                        </td>
                        <td className="px-5 py-3 text-[var(--muted)]">{new Date(txn.created_at).toLocaleDateString()}</td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}