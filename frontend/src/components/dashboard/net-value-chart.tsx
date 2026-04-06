"use client";

import { useEffect, useState } from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { api } from "@/lib/api";
import { formatCurrency } from "@/lib/format";
import type { SnapshotChartPoint } from "@/types";

function coercePoint(p: SnapshotChartPoint): SnapshotChartPoint {
  return {
    ...p,
    total_market_value:
      typeof p.total_market_value === "string"
        ? parseFloat(p.total_market_value)
        : Number(p.total_market_value),
    total_cost:
      typeof p.total_cost === "string"
        ? parseFloat(p.total_cost)
        : Number(p.total_cost),
    total_profit_loss:
      typeof p.total_profit_loss === "string"
        ? parseFloat(p.total_profit_loss)
        : Number(p.total_profit_loss),
  };
}

export function NetValueChart() {
  const [data, setData] = useState<SnapshotChartPoint[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.snapshots
      .chart30d()
      .then((rows) => setData(rows.map(coercePoint)))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const hasEstimated = data.some((p) => p.estimated);

  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-base">资产走势</CardTitle>
        </CardHeader>
        <CardContent className="flex h-[250px] items-center justify-center">
          <div className="h-6 w-6 animate-spin rounded-full border-2 border-primary border-t-transparent" />
        </CardContent>
      </Card>
    );
  }

  if (data.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-base">资产走势</CardTitle>
        </CardHeader>
        <CardContent className="flex h-[250px] items-center justify-center text-sm text-muted-foreground">
          暂无持仓，无法绘制近 30 日走势
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="overflow-visible">
      <CardHeader className="pb-2">
        <CardTitle className="text-base">资产走势</CardTitle>
        <p className="text-xs text-muted-foreground">
          近 30 个自然日
          {hasEstimated
            ? "：有日终快照的日期为真实数据，其余按当前持仓从总成本向今日市值平滑估算（仅供参考）"
            : "，数据来自系统保存的日终快照"}
        </p>
      </CardHeader>
      <CardContent className="min-w-0">
        {hasEstimated ? (
          <p className="mb-2 text-xs text-amber-700/90 dark:text-amber-500/90">
            图中含部分模拟点位，与真实历史可能有偏差
          </p>
        ) : null}
        <div className="h-[250px] w-full min-w-0">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={data}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis
                dataKey="date"
                tick={{ fontSize: 12 }}
                tickFormatter={(v: string) => v.slice(5)}
              />
              <YAxis
                tick={{ fontSize: 12 }}
                tickFormatter={(v: number) => `${(v / 10000).toFixed(0)}万`}
              />
              <Tooltip
                formatter={(value, name) => [
                  formatCurrency(Number(value)),
                  name === "总市值" ? "总市值" : "总成本",
                ]}
                labelFormatter={(label) => `日期: ${label}`}
              />
              <Line
                type="monotone"
                dataKey="total_market_value"
                stroke="#2563eb"
                strokeWidth={2}
                dot={false}
                name="总市值"
              />
              <Line
                type="monotone"
                dataKey="total_cost"
                stroke="#9ca3af"
                strokeWidth={1}
                strokeDasharray="4 4"
                dot={false}
                name="总成本"
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </CardContent>
    </Card>
  );
}
