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
import type { SnapshotPoint } from "@/types";

export function NetValueChart() {
  const [data, setData] = useState<SnapshotPoint[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.snapshots
      .list()
      .then(setData)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

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
          暂无快照数据，系统将每个交易日自动生成
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">资产走势</CardTitle>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={250}>
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
              formatter={(value) => [
                formatCurrency(Number(value)),
                "总市值",
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
      </CardContent>
    </Card>
  );
}
