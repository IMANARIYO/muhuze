import type { Wallet } from "../../types/wallet";

export class WalletEngine {
  private wallet: Wallet;

constructor(wallet: Wallet) {
  this.wallet = wallet;
}

  deposit(
    amount: number,
    description: string,
  
  ) {
    this.wallet.balance += amount;

    this.wallet.totalEarned += amount;

    this.wallet.transactions.unshift({
  id: crypto.randomUUID(),
  userId: "system",
  type: "deposit",
  amount,
  description,
  status: "completed",
  createdAt: new Date().toISOString(),
});
  }

 pay(
  amount: number,
  description: string
) {
  if (this.wallet.balance < amount) {
    throw new Error(
      "Insufficient wallet balance."
    );
  }

  this.wallet.balance -= amount;

  this.wallet.transactions.unshift({
    id: crypto.randomUUID(),

    userId: "system",

    type: "premium",

    amount,

    description,

    status: "completed",

    createdAt: new Date().toISOString(),
  });
}
  withdraw(
    amount: number
  ) {
    if (this.wallet.balance < amount) {
      throw new Error(
        "Insufficient balance."
      );
    }

    this.wallet.balance -= amount;

    this.wallet.totalWithdrawn += amount;

    this.wallet.transactions.unshift({
    id: crypto.randomUUID(),

      userId: "system",

      type: "withdraw",

      amount,

      description: "Wallet Withdrawal",
      status: "completed",

      createdAt: new Date().toISOString(),
    });
  }

  getState() {
    return this.wallet;
  }
}