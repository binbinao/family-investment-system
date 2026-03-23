"use client";

import { useCallback, useEffect, useState } from "react";
import { api } from "@/lib/api";
import { TransactionList } from "@/components/transactions/transaction-list";
import type { Transaction } from "@/types";

export default function HistoryPage() {
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchTransactions = useCallback(async () => {
    try {
      const data = await api.transactions.list();
      setTransactions(data);
    } catch {
      // handled by auth guard
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchTransactions();
  }, [fetchTransactions]);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-primary border-t-transparent" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">交易历史</h1>
        <p className="text-sm text-muted-foreground">
          查看所有交易记录
        </p>
      </div>

      <TransactionList transactions={transactions} />
    </div>
  );
}
