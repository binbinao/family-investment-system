"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ErrorBoundary } from "@/components/ui/error-boundary";
import type { RiskMetrics } from "@/types";

function SharpeBadge({ value }: { value: number }) {
  if (value >= 1) return <span className="text-green-600 font-semibold">优</span>;
  if (value >= 0.5) return <span className="text-yellow-600 font-semibold">中</span>;
  return <span className="text-red-600 font-semibold">差</span>;
}

function MetricCard({
  label,
  value,
  unit,
  hint,
  color,
}: {
  label: string;
  value: string;
  unit: string;
  hint?: string;
  color?: string;
}) {
  return (
    <div className="flex flex-col items-center gap-1 rounded-lg border border-border/60 bg-muted/10 p-4">
      <span className="text-xs text-muted-foreground">{label}</span>
      <span className={`text-xl font-bold ${color || ""}`}>{value}</span>
      <span className="text-xs text-muted-foreground">{unit}</span>
      {hint && <span className="text-xs text-muted-foreground/60">{hint}</span>}
    </div>
  );
}

function RiskMetricsContent() {
  const [metrics, setMetrics] = useState<RiskMetrics | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.dashboard
      .riskMetrics()
      .then(setMetrics)
      .catch(() => setMetrics(null))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-8">
        <div className="h-6 w-6 animate-spin rounded-full border-2 border-primary border-t-transparent" />
      </div>
    );
  }

  if (!metrics) {
    return (
      <div className="flex flex-col items-center justify-center py-8 text-center">
        <p className="text-sm text-muted-foreground">
          数据不足，需至少5个交易日快照
        </p>
        <p className="text-xs text-muted-foreground/60 mt-1">
          持续使用系统后，风险指标将自动计算
        </p>
      </div>
    );
  }

  const ddColor = metrics.max_drawdown > 20 ? "text-red-600" : metrics.max_drawdown > 10 ? "text-yellow-600" : "text-green-600";
  const volColor = metrics.annualized_volatility > 25 ? "text-red-600" : metrics.annualized_volatility > 15 ? "text-yellow-600" : "text-green-600";
  const varColor = metrics.var_95 > 3 ? "text-red-600" : metrics.var_95 > 1.5 ? "text-yellow-600" : "text-green-600";

  return (
    <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
      <MetricCard
        label="最大回撤"
        value={`-${metrics.max_drawdown.toFixed(1)}`}
        unit="%"
        hint="从峰值到谷值"
        color={ddColor}
      />
      <MetricCard
        label="年化波动率"
        value={metrics.annualized_volatility.toFixed(1)}
        unit="%"
        hint="收益波动幅度"
        color={volColor}
      />
      <MetricCard
        label="夏普比率"
        value={metrics.sharpe_ratio.toFixed(2)}
        unit=""
        hint={
          metrics.sharpe_ratio >= 1
            ? "超额收益显著"
            : metrics.sharpe_ratio >= 0.5
              ? "收益风险比尚可"
              : "风险补偿不足"
        }
        color=""
      />
      <MetricCard
        label="VaR (95%)"
        value={`-${metrics.var_95.toFixed(2)}`}
        unit="%/日"
        hint="95%概率最坏日亏损"
        color={varColor}
      />
    </div>
  );
}

export function RiskMetricsCard() {
  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="text-base flex items-center gap-2">
          风险概览
          <SharpeBadge value={0} />
        </CardTitle>
        <p className="text-sm text-muted-foreground">
          衡量投资组合的风险水平
        </p>
      </CardHeader>
      <CardContent>
        <ErrorBoundary>
          <RiskMetricsContent />
        </ErrorBoundary>
      </CardContent>
    </Card>
  );
}
