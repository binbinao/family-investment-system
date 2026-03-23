"use client";

import { useCallback, useEffect, useState } from "react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { api } from "@/lib/api";
import { AddHoldingForm } from "@/components/holdings/add-holding-form";
import { AddTransactionForm } from "@/components/transactions/add-transaction-form";
import type { Holding } from "@/types";

export default function TradePage() {
  const [holdings, setHoldings] = useState<Holding[]>([]);

  const fetchHoldings = useCallback(async () => {
    try {
      const data = await api.holdings.list();
      setHoldings(data);
    } catch {
      // handled by auth guard
    }
  }, []);

  useEffect(() => {
    fetchHoldings();
  }, [fetchHoldings]);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">记账</h1>
        <p className="text-sm text-muted-foreground">
          添加新持仓或记录交易
        </p>
      </div>

      <Tabs defaultValue="holding" className="w-full">
        <TabsList>
          <TabsTrigger value="holding">添加持仓</TabsTrigger>
          <TabsTrigger value="transaction">记录交易</TabsTrigger>
        </TabsList>
        <TabsContent value="holding" className="mt-4">
          <AddHoldingForm onSuccess={fetchHoldings} />
        </TabsContent>
        <TabsContent value="transaction" className="mt-4">
          <AddTransactionForm
            holdings={holdings}
            onSuccess={fetchHoldings}
          />
        </TabsContent>
      </Tabs>
    </div>
  );
}
