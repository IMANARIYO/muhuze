"use client";

import { useState } from "react";
import { CheckCircle, CreditCard, Send } from "lucide-react";
import { Card, CardContent } from "@/app/_components/ui/card";
import { Button } from "@/app/_components/ui/button";
import { payments as initialPayments } from "@/app/lib/data";
import type { Payment } from "@/app/lib/types";

const statusColors: Record<string, { bg: string; text: string }> = {
  pending:   { bg: "#fbf0ce", text: "#b58a24" },
  completed: { bg: "#e8f4ed", text: "#2d7a5e" },
  refunded:  { bg: "#fbe6e0", text: "#d75e4a" },
};

const payoutColors: Record<string, { bg: string; text: string }> = {
  pending: { bg: "#fbf0ce", text: "#b58a24" },
  sent:    { bg: "#e8f4ed", text: "#2d7a5e" },
  failed:  { bg: "#fbe6e0", text: "#d75e4a" },
};

export default function PaymentsPage() {
  const [payments, setPayments] = useState<Payment[]>(initialPayments);

  const sendPayout = (id: string) => {
    setPayments((prev) =>
      prev.map((p) => (p.id === id ? { ...p, payoutStatus: "sent" } : p))
    );
  };

  const totalRevenue = payments.filter((p) => p.status === "completed").reduce((s, p) => s + p.amount, 0);
  const totalCommission = payments.filter((p) => p.status === "completed").reduce((s, p) => s + p.commission, 0);
  const pendingPayouts = payments.filter((p) => p.payoutStatus === "pending" && p.status === "completed");

  return (
    <div className="mx-auto max-w-5xl space-y-6">
      <div>
        <h1 className="text-2xl font-extrabold tracking-tight text-[var(--ink)]">Payments</h1>
        <p className="mt-1 text-sm text-[var(--muted)]">
          Manage all payments and send commission payouts to sellers.
        </p>
      </div>

      {/* Summary */}
      <div className="grid gap-4 sm:grid-cols-3">
        <Card className="border-[#bdded1] bg-[#e8f4ed]">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <span className="text-xs text-[#78857f]">Total Revenue</span>
              <CreditCard size={16} className="text-[#59ac88]" />
            </div>
            <p className="mt-3 text-3xl font-extrabold tracking-tight text-[var(--ink)]">
              ${totalRevenue.toFixed(2)}
            </p>
            <p className="mt-1 text-[11px] text-[#9aa39e]">Completed payments</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <span className="text-xs text-[#78857f]">Platform Commission</span>
              <CheckCircle size={16} className="text-[#a7b0aa]" />
            </div>
            <p className="mt-3 text-3xl font-extrabold tracking-tight text-[var(--ink)]">
              ${totalCommission.toFixed(2)}
            </p>
            <p className="mt-1 text-[11px] text-[#9aa39e]">10% of completed sales</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <span className="text-xs text-[#78857f]">Pending Payouts</span>
              <Send size={16} className="text-[#a7b0aa]" />
            </div>
            <p className="mt-3 text-3xl font-extrabold tracking-tight text-[var(--ink)]">
              {pendingPayouts.length}
            </p>
            <p className="mt-1 text-[11px] text-[#9aa39e]">
              ${pendingPayouts.reduce((s, p) => s + p.sellerPayout, 0).toFixed(2)} to send
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Payments table */}
      <Card>
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead>
                <tr className="border-b border-[var(--line)] bg-[#f9fbf9]">
                  <th className="px-5 py-3 text-left font-bold text-[var(--muted)]">Order</th>
                  <th className="px-5 py-3 text-left font-bold text-[var(--muted)]">Client</th>
                  <th className="px-5 py-3 text-left font-bold text-[var(--muted)]">Seller</th>
                  <th className="px-5 py-3 text-right font-bold text-[var(--muted)]">Amount</th>
                  <th className="px-5 py-3 text-right font-bold text-[var(--muted)]">Commission</th>
                  <th className="px-5 py-3 text-right font-bold text-[var(--muted)]">Seller Gets</th>
                  <th className="px-5 py-3 text-left font-bold text-[var(--muted)]">Payment</th>
                  <th className="px-5 py-3 text-left font-bold text-[var(--muted)]">Payout</th>
                  <th className="px-5 py-3 text-left font-bold text-[var(--muted)]">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#eff1ef]">
                {payments.map((pay) => {
                  const sc = statusColors[pay.status];
                  const pc = payoutColors[pay.payoutStatus];
                  const canPayout = pay.status === "completed" && pay.payoutStatus === "pending";
                  return (
                    <tr key={pay.id} className="hover:bg-[#f9fbf9]">
                      <td className="px-5 py-3 font-semibold text-[var(--ink)]">#{pay.orderId}</td>
                      <td className="px-5 py-3 text-[var(--muted)]">{pay.clientName}</td>
                      <td className="px-5 py-3 text-[var(--muted)]">{pay.sellerName}</td>
                      <td className="px-5 py-3 text-right font-bold text-[var(--ink)]">${pay.amount.toFixed(2)}</td>
                      <td className="px-5 py-3 text-right text-[var(--teal)]">${pay.commission.toFixed(2)}</td>
                      <td className="px-5 py-3 text-right font-bold text-[var(--ink)]">${pay.sellerPayout.toFixed(2)}</td>
                      <td className="px-5 py-3">
                        <span
                          className="rounded-full px-2.5 py-0.5 text-[10px] font-semibold capitalize"
                          style={{ backgroundColor: sc.bg, color: sc.text }}
                        >
                          {pay.status}
                        </span>
                      </td>
                      <td className="px-5 py-3">
                        <span
                          className="rounded-full px-2.5 py-0.5 text-[10px] font-semibold capitalize"
                          style={{ backgroundColor: pc.bg, color: pc.text }}
                        >
                          {pay.payoutStatus}
                        </span>
                      </td>
                      <td className="px-5 py-3">
                        {canPayout ? (
                          <Button
                            size="sm"
                            className="h-7 gap-1 px-3 text-[10px]"
                            onClick={() => sendPayout(pay.id)}
                          >
                            <Send size={11} /> Send Payout
                          </Button>
                        ) : pay.payoutStatus === "sent" ? (
                          <span className="flex items-center gap-1 text-[10px] text-[#2d7a5e]">
                            <CheckCircle size={11} /> Sent
                          </span>
                        ) : (
                          <span className="text-[10px] text-[var(--muted)]">—</span>
                        )}
                      </td>
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
