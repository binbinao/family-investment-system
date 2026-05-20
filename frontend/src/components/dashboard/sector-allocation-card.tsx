"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ErrorBoundary } from "@/components/ui/error-boundary";
import type { SectorAllocation } from "@/types";

function SectorBar({ sector, percentage, holdings_count }: SectorAllocation) {
  // 单一行业 > 30% 显示红色预警
  const isAlert = percentage > 30;
  const barColor = isAlert
    ? "bg-red-500"
    : percentage > 20
      ? "bg-yellow-500"
      : "bg-blue-500";

  return (
    <div className="space-y-1">
      <div className="flex items-center justify-between text-sm">
        <span className="flex items-center gap-1.5">
          {sector}
          {isAlert && (
            <span className="rounded bg-red-100 px-1.5 py-0.5 text-xs text-red-700">
              集中
            </span>
          )}
        </span>
        <span className="text-muted-foreground">
          {percentage.toFixed(1)}% · {holdings_count}只
        </span>
      </div>
      <div className="h-2 w-full rounded-full bg-muted">
        <div
          className={`h-2 rounded-full ${barColor} transition-all`}
          style={{ width: `${Math.min(percentage, 100)}%` }}
        />
      </div>
    </div>
  );
}

function SectorAllocationContent() {
  const [sectors, setSectors] = useState<SectorAllocation[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.dashboard
      .sectorAllocation()
      .then(setSectors)
      .catch(() => setSectors([]))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-6">
        <div className="h-6 w-6 animate-spin rounded-full border-2 border-primary border-t-transparent" />
      </div>
    );
  }

  if (sectors.length === 0) {
    return (
      <p className="py-4 text-center text-sm text-muted-foreground">
        暂无行业数据，请为持仓设置行业分类
      </p>
    );
  }

  return (
    <div className="space-y-3">
      {sectors.map((s) => (
        <SectorBar key={s.sector} {...s} />
      ))}
    </div>
  );
}

export function SectorAllocationCard() {
  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="text-base">行业分布</CardTitle>
        <p className="text-sm text-muted-foreground">
          按申万一级行业查看持仓集中度
        </p>
      </CardHeader>
      <CardContent>
        <ErrorBoundary>
          <SectorAllocationContent />
        </ErrorBoundary>
      </CardContent>
    </Card>
  );
}
