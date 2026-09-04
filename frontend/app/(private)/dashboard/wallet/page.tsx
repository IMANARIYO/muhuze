"use client";

import { useEffect, useState } from "react";
import { AlertCircle, ArrowDownLeft, ArrowLeftRight, CheckCircle, Clock, Send, TrendingUp, Wallet } from "lucide-react";
import { Card, CardContent } from "@/app/_components/ui/card";
import { Button } from "@/app/_components/ui/button";
import { useAuth } from "@/app/context/auth-context";
import {
  walletService,
  type WalletSummary,
  type AdminWalletOverview,
  type WithdrawalResponse,
} from "@/app/services/wallet.service";
import { rwf } from "@/app/lib/utils";

const STATUS_COLORS: Record<string, { bg: string; text: string }> = {
  held: { bg: "#fbf0ce", text: "#b58a24" },
  released: { bg: "#e8f4ed", text: "#2d7a5e" },
  requested: { bg: "#fbf0ce", text: "#b58a24" },
  processing: { bg: "#e8f1f6", text: "#3b79a3" },
  completed: { bg: "#e8f4ed", text: "#2d7a5e" },
  cancelled: { bg: "#f3e1dd", text: "#b74d3b" },
};

export default function WalletPage() {
  const { hasRole } = useAuth();
  if (hasRole("admin")) return <AdminWallet />;
  return <SellerWallet />;
}

/* ─── Seller wallet ──────────────────────────────────────────────────────── */

function SellerWallet() {
  const [wallet, setWallet] = useState<WalletSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [withdrawOpen, setWithdrawOpen] = useState(false);
  const [wdAmount, setWdAmount] = useState("");
  const [wdNumber, setWdNumber] = useState("");
  const [wdNote, setWdNote] = useState("");
  const [wdWorking, setWdWorking] = useState(false);
  const [wdMsg, setWdMsg] = useState("");

  async function load() {
    setLoading(true);
    setError("");
    try {
      setWallet(await walletService.getMine());
    } catch (e) {
      setError(e instanceof Error ? e.message : "Wallet could not be loaded.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    let cancelled = false;
    walletService
      .getMine()
      .then((w) => { if (!cancelled) setWallet(w); })
      .catch((e) => { if (!cancelled) setError(e instanceof Error ? e.message : "Wallet could not be loaded."); })
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, []);

  async function submitWithdrawal() {
    const amount = parseFloat(wdAmount);
    if (!amount || amount <= 0) { setWdMsg("Enter a valid amount."); return; }
    if (!wdNumber.trim()) { setWdMsg("Enter your mobile-money number for the payout."); return; }
    setWdWorking(true);
    setWdMsg("");
    try {
      await walletService.requestWithdrawal({
        amount,
        mobile_money_number: wdNumber.trim(),
        note: wdNote.trim() || undefined,
      });
      setWdMsg("");
      setWithdrawOpen(false);
      setWdAmount("");
      setWdNumber("");
      setWdNote("");
      await load();
    } catch (e) {
      setWdMsg(e instanceof Error ? e.message : "Withdrawal could not be requested.");
    } finally {
      setWdWorking(false);
    }
  }

  const data = wallet?.wallet;
  const available = data?.available_balance ?? 0;

  return (
    <div className="mx-auto max-w-4xl space-y-8">
      <div>
        <p className="text-[10px] font-bold uppercase tracking-[.13em] text-[#93a09a]">Seller workspace</p>
        <h1 className="mt-1 text-3xl font-black tracking-[-.04em]">My Wallet</h1>
        <p className="mt-2 text-sm text-[var(--muted)]">
          Your earnings from completed sales. Funds are held until the buyer confirms receipt, then released and ready to withdraw to your mobile-money number.
        </p>
      </div>

      {error && <p role="alert" className="rounded-lg bg-[#fbe6e0] px-4 py-3 text-sm text-[#b74d3b]">{error}</p>}

      {loading ? (
        <div className="rounded-xl border border-[var(--line)] bg-white p-10 text-center text-sm text-[var(--muted)]">Loading wallet…</div>
      ) : wallet ? (
        <>
          {/* Balance cards */}
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <Card className="border-[#bdded1] bg-[#e8f4ed] lg:col-span-2">
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-[#2d7a5e]">Available balance</span>
                  <Wallet size={18} className="text-[#59ac88]" />
                </div>
                <p className="mt-3 text-4xl font-black tracking-tight text-[var(--ink)]">{rwf(available)}</p>
                <p className="mt-1 text-[11px] text-[#78857f]">Released earnings · ready to withdraw</p>
                <Button
                  className="mt-4 w-full"
                  onClick={() => { setWithdrawOpen((o) => !o); setWdMsg(""); }}
                  disabled={available <= 0}
                >
                  <Send size={14} /> {available <= 0 ? "Nothing to withdraw yet" : "Request withdrawal"}
                </Button>
              </CardContent>
            </Card>

            <Card className="border-[#f0d98a] bg-[#fffdf0]">
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-[#b58a24]">Held</span>
                  <Clock size={16} className="text-[#c9a84c]" />
                </div>
                <p className="mt-3 text-2xl font-black tracking-tight text-[var(--ink)]">{rwf(data?.held_balance ?? 0)}</p>
                <p className="mt-1 text-[11px] text-[#b58a24]">Awaiting buyer confirmation</p>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-[#78857f]">Total earned</span>
                  <TrendingUp size={16} className="text-[#a7b0aa]" />
                </div>
                <p className="mt-3 text-2xl font-black tracking-tight text-[var(--ink)]">{rwf(data?.total_earned ?? 0)}</p>
                <p className="mt-1 text-[11px] text-[#9aa39e]">Lifetime net earnings</p>
                {data && data.total_withdrawn > 0 && (
                  <p className="mt-1 text-[10px] text-[#9aa39e]">Withdrawn to date: {rwf(data.total_withdrawn)}</p>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Withdrawal form */}
          {withdrawOpen && (
            <Card className="border-[#bdded1] bg-[#f6fcf8]">
              <CardContent className="space-y-4 p-6">
                <div>
                  <h2 className="text-sm font-bold text-[var(--ink)]">Withdraw to mobile money</h2>
                  <p className="mt-0.5 text-xs text-[var(--muted)]">
                    Available to withdraw: <b className="text-[var(--teal)]">{rwf(available)}</b>. The payout is sent outside the system by MUHUZE to your number.
                  </p>
                </div>
                {wdMsg && <p role="alert" className={`rounded-lg px-4 py-2 text-sm ${wdMsg.startsWith("Withdrawal") ? "bg-[#e8f4ed] text-[#2d7a5e]" : "bg-[#fbe6e0] text-[#b74d3b]"}`}>{wdMsg}</p>}
                <div className="grid gap-4 sm:grid-cols-2">
                  <div>
                    <label className="mb-1 block text-xs font-bold text-[var(--muted)]">Amount (RWF) *</label>
                    <input
                      value={wdAmount}
                      onChange={(e) => setWdAmount(e.target.value.replace(/[^0-9.]/g, ""))}
                      placeholder="e.g. 10000"
                      type="number"
                      min={1}
                      max={available}
                      className="w-full rounded-lg border border-[var(--line)] px-3 py-2.5 text-sm outline-none focus:border-[var(--teal)]"
                    />
                  </div>
                  <div>
                    <label className="mb-1 block text-xs font-bold text-[var(--muted)]">Your MoMo number *</label>
                    <input
                      value={wdNumber}
                      onChange={(e) => setWdNumber(e.target.value)}
                      placeholder="e.g. 0788 123 456"
                      className="w-full rounded-lg border border-[var(--line)] px-3 py-2.5 text-sm outline-none focus:border-[var(--teal)]"
                    />
                  </div>
                </div>
                <div>
                  <label className="mb-1 block text-xs font-bold text-[var(--muted)]">Note <span className="font-normal">(optional)</span></label>
                  <input
                    value={wdNote}
                    onChange={(e) => setWdNote(e.target.value)}
                    placeholder="Anything we should know?"
                    className="w-full rounded-lg border border-[var(--line)] px-3 py-2.5 text-sm outline-none focus:border-[var(--teal)]"
                  />
                </div>
                <div className="flex gap-3">
                  <Button className="flex-1" onClick={submitWithdrawal} disabled={wdWorking}>
                    {wdWorking ? "Requesting…" : "Request withdrawal"} <Send size={14} />
                  </Button>
                  <Button variant="outline" onClick={() => setWithdrawOpen(false)}>Cancel</Button>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Withdrawal history */}
          {wallet.withdrawals.length > 0 && (
            <Card>
              <CardContent className="p-0">
                <div className="border-b border-[var(--line)] px-6 py-4">
                  <h2 className="text-sm font-bold text-[var(--ink)]">Withdrawals</h2>
                </div>
                <div className="overflow-x-auto">
                  <table className="w-full text-xs">
                    <thead>
                      <tr className="border-b border-[var(--line)] bg-[#f9fbf9]">
                        <th className="px-5 py-3 text-left font-bold text-[var(--muted)]">Amount</th>
                        <th className="px-5 py-3 text-left font-bold text-[var(--muted)]">To number</th>
                        <th className="px-5 py-3 text-left font-bold text-[var(--muted)]">Status</th>
                        <th className="px-5 py-3 text-left font-bold text-[var(--muted)]">Date</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-[#eff1ef]">
                      {wallet.withdrawals.map((w) => {
                        const sc = STATUS_COLORS[w.status] ?? STATUS_COLORS.requested;
                        return (
                          <tr key={w.id} className="hover:bg-[#f9fbf9]">
                            <td className="px-5 py-3 font-bold text-[var(--ink)]">{rwf(w.amount)}</td>
                            <td className="px-5 py-3 font-mono text-[10px] text-[var(--muted)]">{w.mobile_money_number}</td>
                            <td className="px-5 py-3">
                              <span className="rounded-full px-2.5 py-0.5 text-[10px] font-semibold capitalize" style={{ backgroundColor: sc.bg, color: sc.text }}>
                                {w.status}
                              </span>
                            </td>
                            <td className="px-5 py-3 text-[var(--muted)]">{new Date(w.created_at).toLocaleDateString()}</td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Ledger history */}
          <Card>
            <CardContent className="p-0">
              <div className="border-b border-[var(--line)] px-6 py-4">
                <h2 className="text-sm font-bold text-[var(--ink)]">Transaction history</h2>
                <p className="mt-0.5 text-xs text-[var(--muted)]">{wallet.transactions.length} entries</p>
              </div>
              {wallet.transactions.length === 0 ? (
                <div className="p-14 text-center">
                  <ArrowLeftRight className="mx-auto text-[#9aa9a1]" size={28} />
                  <p className="mt-4 font-bold">No transactions yet</p>
                  <p className="mt-2 text-sm text-[var(--muted)]">Once orders are paid and revenue released, your ledger appears here.</p>
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-xs">
                    <thead>
                      <tr className="border-b border-[var(--line)] bg-[#f9fbf9]">
                        <th className="px-5 py-3 text-left font-bold text-[var(--muted)]">Type</th>
                        <th className="px-5 py-3 text-right font-bold text-[var(--muted)]">Amount</th>
                        <th className="px-5 py-3 text-right font-bold text-[var(--muted)]">Balance</th>
                        <th className="px-5 py-3 text-left font-bold text-[var(--muted)]">Description</th>
                        <th className="px-5 py-3 text-left font-bold text-[var(--muted)]">Date</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-[#eff1ef]">
                      {wallet.transactions.map((t) => (
                        <tr key={t.id} className="hover:bg-[#f9fbf9]">
                          <td className="px-5 py-3">
                            <span className="rounded-full px-2.5 py-0.5 text-[10px] font-semibold capitalize" style={{ backgroundColor: STATUS_COLORS[t.type === "withdrawal" ? "cancelled" : t.type === "release" ? "released" : "held"]?.bg ?? "#eef1ef", color: STATUS_COLORS[t.type === "withdrawal" ? "cancelled" : t.type === "release" ? "released" : "held"]?.text ?? "#67736e" }}>
                              {t.type}
                            </span>
                          </td>
                          <td className={`px-5 py-3 text-right font-bold ${t.amount < 0 ? "text-[var(--coral)]" : "text-[var(--teal)]"}`}>
                            {t.amount < 0 ? "-" : "+"}{rwf(Math.abs(t.amount))}
                          </td>
                          <td className="px-5 py-3 text-right font-semibold text-[var(--ink)]">{rwf(t.balance_after)}</td>
                          <td className="px-5 py-3 text-[var(--muted)]">{t.description ?? "—"}</td>
                          <td className="px-5 py-3 text-[var(--muted)]">{new Date(t.created_at).toLocaleDateString()}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </CardContent>
          </Card>
        </>
      ) : null}
    </div>
  );
}

/* ─── Admin wallet ───────────────────────────────────────────────────────── */

function AdminWallet() {
  const [data, setData] = useState<AdminWalletOverview | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [wdNote, setWdNote] = useState<string>("");

  async function load() {
    setLoading(true);
    setError("");
    try {
      setData(await walletService.getAdminOverview());
    } catch (e) {
      setError(e instanceof Error ? e.message : "Wallet data could not be loaded.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    let cancelled = false;
    walletService
      .getAdminOverview()
      .then((d) => { if (!cancelled) setData(d); })
      .catch((e) => { if (!cancelled) setError(e instanceof Error ? e.message : "Wallet data could not be loaded."); })
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, []);

  async function act(w: WithdrawalResponse, status: string) {
    try {
      await walletService.updateWithdrawal(w.id, { status, note: wdNote || undefined });
      setWdNote("");
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Withdrawal could not be updated.");
    }
  }

  return (
    <div className="mx-auto max-w-5xl space-y-8">
      <div>
        <p className="text-[10px] font-bold uppercase tracking-[.13em] text-[#93a09a]">Admin workspace</p>
        <h1 className="mt-1 text-3xl font-black tracking-[-.04em]">Platform Wallet</h1>
        <p className="mt-2 text-sm text-[var(--muted)]">
          Aggregate wallet across sellers. Commission is MUHUZE&apos;s cut; payouts are what&apos;s been sent to sellers via mobile money.
        </p>
      </div>

      {error && <p role="alert" className="rounded-lg bg-[#fbe6e0] px-4 py-3 text-sm text-[#b74d3b]">{error}</p>}

      {loading ? (
        <div className="rounded-xl border border-[var(--line)] bg-white p-10 text-center text-sm text-[var(--muted)]">Loading wallet data…</div>
      ) : data ? (
        <>
          {/* Summary cards */}
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <Card className="border-[#bdded1] bg-[#e8f4ed] lg:col-span-2">
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-[#2d7a5e]">Total available</span>
                  <Wallet size={18} className="text-[#59ac88]" />
                </div>
                <p className="mt-3 text-4xl font-black tracking-tight text-[var(--ink)]">{rwf(data.total_available)}</p>
                <p className="mt-1 text-[11px] text-[#78857f]">Across {data.seller_count} seller wallets</p>
              </CardContent>
            </Card>

            <Card className="border-[#f0d98a] bg-[#fffdf0]">
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-[#b58a24]">Held (escrow)</span>
                  <Clock size={16} className="text-[#c9a84c]" />
                </div>
                <p className="mt-3 text-2xl font-black tracking-tight text-[var(--ink)]">{rwf(data.total_held)}</p>
                <p className="mt-1 text-[11px] text-[#b58a24]">Awaiting buyer confirmation</p>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-[#78857f]">Total withdrawn</span>
                  <ArrowDownLeft size={16} className="text-[#a7b0aa]" />
                </div>
                <p className="mt-3 text-2xl font-black tracking-tight text-[var(--ink)]">{rwf(data.total_withdrawn)}</p>
                <p className="mt-1 text-[11px] text-[#9aa39e]">Paid out to sellers via MoMo</p>
              </CardContent>
            </Card>
          </div>

          {/* Withdrawal queue */}
          <Card className={data.withdrawals_pending.length ? "border-[#f0d98a]" : ""}>
            <CardContent className="p-0">
              <div className="border-b border-[var(--line)] px-6 py-4">
                <h2 className="text-sm font-bold text-[var(--ink)]">Withdrawal requests</h2>
                <p className="mt-0.5 text-xs text-[var(--muted)]">
                  {data.withdrawals_pending.length} pending · send MoMo outside the system, then mark completed (this debits the wallet).
                </p>
              </div>
              {data.withdrawals_pending.length === 0 ? (
                <div className="p-12 text-center">
                  <CheckCircle className="mx-auto text-[#9aa9a1]" size={26} />
                  <p className="mt-3 font-bold">No pending withdrawals</p>
                  <p className="mt-1 text-sm text-[var(--muted)]">New requests from sellers appear here.</p>
                </div>
              ) : (
                <div className="divide-y divide-[#eff1ef]">
                  {data.withdrawals_pending.map((w) => {
                    const sc = STATUS_COLORS[w.status] ?? STATUS_COLORS.requested;
                    return (
                      <div key={w.id} className="flex flex-wrap items-center justify-between gap-4 px-6 py-4">
                        <div>
                          <div className="flex items-center gap-3">
                            <p className="text-lg font-black text-[var(--ink)]">{rwf(w.amount)}</p>
                            <span className="rounded-full px-2.5 py-0.5 text-[10px] font-semibold capitalize" style={{ backgroundColor: sc.bg, color: sc.text }}>
                              {w.status}
                            </span>
                          </div>
                          <p className="mt-1 text-xs text-[var(--muted)]">
                            Seller <span className="font-mono">{w.seller_id.slice(0, 8)}</span> · send to <b className="font-mono">{w.mobile_money_number}</b>
                          </p>
                          {w.note && <p className="mt-1 text-[11px] italic text-[#9aa39e]">“{w.note}”</p>}
                        </div>
                        <div className="flex items-center gap-2">
                          {w.status === "requested" && (
                            <Button size="sm" variant="outline" onClick={() => act(w, "processing")}>Start processing</Button>
                          )}
                          {w.status !== "cancelled" && w.status !== "completed" && (
                            <>
                              <Button size="sm" onClick={() => act(w, "completed")}><CheckCircle size={13} /> Mark sent</Button>
                              <Button size="sm" variant="ghost" className="text-[var(--coral)]" onClick={() => act(w, "cancelled")}>Cancel</Button>
                            </>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </CardContent>
          </Card>
        </>
      ) : null}
    </div>
  );
}
