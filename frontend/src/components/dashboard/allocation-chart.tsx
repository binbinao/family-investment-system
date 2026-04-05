"use client";

import { useMemo } from "react";
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend } from "recharts";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { formatCurrency } from "@/lib/format";
import type { AllocationItem } from "@/types";

const COLORS = [
  "hsl(210, 70%, 50%)",
  "hsl(150, 60%, 45%)",
  "hsl(30, 80%, 55%)",
  "hsl(340, 65%, 50%)",
  "hsl(270, 50%, 55%)",
];

/** FastAPI / Pydantic serializes Decimal as JSON string; Recharts needs numbers for angles. */
function coerceNumber(value: number | string): number {
  if (typeof value === "number" && Number.isFinite(value)) return value;
  const n = parseFloat(String(value));
  return Number.isFinite(n) ? n : 0;
}

export function AllocationChart({ data }: { data: AllocationItem[] }) {
  const chartData = useMemo(
    () =>
      data.map((d) => ({
        ...d,
        market_value: coerceNumber(d.market_value as number | string),
        percentage: coerceNumber(d.percentage as number | string),
      })),
    [data],
  );

  if (chartData.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-base">资产配置</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">暂无持仓数据</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="overflow-visible">
      <CardHeader>
        <CardTitle className="text-base">资产配置</CardTitle>
      </CardHeader>
      <CardContent className="min-w-0">
        <div className="h-[280px] w-full min-w-0">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={chartData}
                cx="50%"
                cy="50%"
                innerRadius={60}
                outerRadius={100}
                dataKey="market_value"
                nameKey="asset_type"
                stroke="none"
              >
                {chartData.map((_, index) => (
                  <Cell key={index} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip
                formatter={(value) => formatCurrency(Number(value))}
                contentStyle={{
                  borderRadius: "8px",
                  border: "1px solid hsl(var(--border))",
                  boxShadow: "0 2px 8px rgba(0,0,0,0.08)",
                }}
              />
              <Legend
                formatter={(value) => {
                  const item = chartData.find((d) => d.asset_type === value);
                  return `${value} ${item ? item.percentage.toFixed(1) : 0}%`;
                }}
              />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </CardContent>
    </Card>
  );
}
