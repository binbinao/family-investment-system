"use client";

import { useCallback, useEffect, useState } from "react";
import { api } from "@/lib/api";
import { SummaryCards } from "@/components/dashboard/summary-cards";
import { AllocationChart } from "@/components/dashboard/allocation-chart";
import { HoldingsTable } from "@/components/dashboard/holdings-table";
import { NetValueChart } from "@/components/dashboard/net-value-chart";
import { DeviationAlert } from "@/components/dashboard/deviation-alert";
import { MarketStatusBar } from "@/components/dashboard/market-status-bar";
import type { AllocationItem, DashboardSummary, Holding } from "@/types";

export default function HomePage() {
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [allocation, setAllocation] = useState<AllocationItem[]>([]);
  const [holdings, setHoldings] = useState<Holding[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchData = useCallback(async () => {
    try {
      const [s, a, h] = await Promise.all([
        api.dashboard.summary(),
        api.dashboard.allocation(),
        api.holdings.list(),
      ]);
      setSummary(s);
      setAllocation(a);
      setHoldings(h);
    } catch {
      // handled by auth guard
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-primary border-t-transparent" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">
            家庭资产总览
          </h1>
          <p className="text-sm text-muted-foreground">
            一眼看清家里的投资状况
          </p>
        </div>
        <MarketStatusBar onRefreshComplete={fetchData} />
      </div>

      <DeviationAlert />

      {summary && <SummaryCards data={summary} />}

      <NetValueChart />

      <div className="grid gap-6 lg:grid-cols-3">
        <div className="lg:col-span-1">
          <AllocationChart data={allocation} />
        </div>
        <div className="lg:col-span-2">
          <div className="space-y-3">
            <h2 className="text-lg font-medium">持仓明细</h2>
            <HoldingsTable holdings={holdings} onRefresh={fetchData} />
          </div>
        </div>
      </div>
    </div>
  );
}
