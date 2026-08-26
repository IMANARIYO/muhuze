import type { Transaction } from "../../types/transaction";

export class TransactionService {
  private storageKey = "transactions";

  getAll(): Transaction[] {
    const saved = localStorage.getItem(
      this.storageKey
    );

    return saved ? JSON.parse(saved) : [];
  }

  getByUser(userId: string) {
    return this.getAll().filter(
      (transaction) =>
        transaction.userId === userId
    );
  }

  create(transaction: Transaction) {
    const transactions = this.getAll();

    transactions.unshift(transaction);

    localStorage.setItem(
      this.storageKey,
      JSON.stringify(transactions)
    );
  }
}