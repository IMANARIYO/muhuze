"use client";

import { useEffect, useState } from "react";
import { TrendingUp, Wallet } from "lucide-react";
import { Card, CardContent } from "@/app/_components/ui/card";
import { revenueService, type RevenueLine } from "@/app/services/revenue.service";
import { rwf } from "@/app/lib/utils";

const payoutLabels: Record<string, string> = {
  held: "held",
  released: "released",
};

const payoutColors: Record<string, { bg: string; text: string }> = {
  held: { bg: "#fbf0ce", text: "#b58a24" },
  released: { bg: "#e8f4ed", text: "#2d7a5e" },
};

export default function EarningsPage() {
  const [earnings, setEarnings] = useState<RevenueLine[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;
    revenueService
      .mine()
      .then((rows) => { if (!cancelled) setEarnings(rows); })
      .catch((caught) => { if (!cancelled) setError(caught instanceof Error ? caught.message : "Your earnings could not be loaded."); })
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, []);

  const released = earnings.filter((e) => e.status === "released");
  const held = earnings.filter((e) => e.status === "held");
  const totalReceived = released.reduce((s, e) => s + e.seller_earning, 0);
  const pendingAmount = held.reduce((s, e) => s + e.seller_earning, 0);
  const totalCommission = earnings.reduce((s, e) => s + e.commission_amount, 0);
  const totalGross = earnings.reduce((s, e) => s + e.amount, 0);

  return (
    <div className="mx-auto max-w-4xl space-y-6">
      <div>
        <h1 className="text-2xl font-extrabold tracking-tight text-[var(--ink)]">My Earnings</h1>
        <p className="mt-1 text-sm text-[var(--muted)]">
          Your share of paid sales. Earnings are held until the buyer confirms receipt, then released.
        </p>
      </div>

      <div className="grid gap-4 sm:grid-cols-3">
        <Card className="border-[#bdded1] bg-[#e8f4ed]">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <span className="text-xs text-[#78857f]">Released</span>
              <Wallet size={16} className="text-[#59ac88]" />
            </div>
            <p className="mt-3 text-3xl font-extrabold tracking-tight text-[var(--ink)]">{rwf(totalReceived)}</p>
            <p className="mt-1 text-[11px] text-[#9aa39e]">After commission</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <span className="text-xs text-[#78857f]">Held</span>
              <TrendingUp size={16} className="text-[#a7b0aa]" />
            </div>
            <p className="mt-3 text-3xl font-extrabold tracking-tight text-[var(--ink)]">{rwf(pendingAmount)}</p>
            <p className="mt-1 text-[11px] text-[#9aa39e]">Awaiting receipt confirmation</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <span className="text-xs text-[#78857f]">Commission</span>
              <Wallet size={16} className="text-[#a7b0aa]" />
            </div>
            <p className="mt-3 text-3xl font-extrabold tracking-tight text-[var(--ink)]">{rwf(totalCommission)}</p>
            <p className="mt-1 text-[11px] text-[#9aa39e]">
              From {rwf(totalGross)} gross
            </p>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardContent className="p-0">
          {loading ? (
            <div className="p-10 text-center text-sm text-[var(--muted)]">Loading earnings…</div>
          ) : error ? (
            <p role="alert" className="m-5 rounded-lg bg-[#fbe6e0] px-4 py-3 text-sm text-[#b74d3b]">{error}</p>
          ) : earnings.length === 0 ? (
            <div className="p-14 text-center">
              <p className="font-bold">No earnings yet</p>
              <p className="mt-2 text-sm text-[var(--muted)]">Once orders are paid, your share appears here.</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-xs">
                <thead>
                  <tr className="border-b border-[var(--line)] bg-[#f9fbf9]">
                    <th className="px-5 py-3 text-left font-bold text-[var(--muted)]">Gross</th>
                    <th className="px-5 py-3 text-left font-bold text-[var(--muted)]">Rate</th>
                    <th className="px-5 py-3 text-right font-bold text-[var(--muted)]">Commission</th>
                    <th className="px-5 py-3 text-right font-bold text-[var(--muted)]">Your share</th>
                    <th className="px-5 py-3 text-left font-bold text-[var(--muted)]">Status</th>
                    <th className="px-5 py-3 text-left font-bold text-[var(--muted)]">Released</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#eff1ef]">
                  {earnings.map((e) => {
                    const pc = payoutColors[e.status] ?? payoutColors.held;
                    return (
                      <tr key={e.id} className="hover:bg-[#f9fbf9]">
                        <td className="px-5 py-3 font-semibold text-[var(--ink)]">{rwf(e.amount)}</td>
                        <td className="px-5 py-3 text-[var(--muted)]">{Math.round(e.revenue_rate)}%</td>
                        <td className="px-5 py-3 text-right text-[var(--coral)]">-{rwf(e.commission_amount)}</td>
                        <td className="px-5 py-3 text-right font-bold text-[var(--ink)]">{rwf(e.seller_earning)}</td>
                        <td className="px-5 py-3">
                          <span className="rounded-full px-2.5 py-0.5 text-[10px] font-semibold capitalize" style={{ backgroundColor: pc.bg, color: pc.text }}>
                            {payoutLabels[e.status] ?? e.status}
                          </span>
                        </td>
                        <td className="px-5 py-3 text-[var(--muted)]">
                          {e.released_at ? new Date(e.released_at).toLocaleDateString() : "—"}
                        </td>
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