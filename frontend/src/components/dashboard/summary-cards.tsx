"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { formatCurrency, formatPercent, profitColor } from "@/lib/format";
import type { DashboardSummary } from "@/types";

export function SummaryCards({ data }: { data: DashboardSummary }) {
  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-medium text-muted-foreground">
            总市值
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-2xl font-semibold tabular-nums">
            {formatCurrency(data.total_market_value)}
          </p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-medium text-muted-foreground">
            总成本
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-2xl font-semibold tabular-nums">
            {formatCurrency(data.total_cost)}
          </p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-medium text-muted-foreground">
            总盈亏
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className={`text-2xl font-semibold tabular-nums ${profitColor(data.total_profit_loss)}`}>
            {formatCurrency(data.total_profit_loss)}
          </p>
          <p className={`text-sm ${profitColor(data.total_profit_loss_pct)}`}>
            {formatPercent(data.total_profit_loss_pct)}
          </p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-medium text-muted-foreground">
            持仓数量
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-2xl font-semibold tabular-nums">
            {data.holdings_count}
          </p>
          <p className="text-sm text-muted-foreground">只标的</p>
        </CardContent>
      </Card>
    </div>
  );
}
