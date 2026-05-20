"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ErrorBoundary } from "@/components/ui/error-boundary";
import type { CorrelationMatrixData, CorrelationPair } from "@/types";

/** Color mapping for correlation values: green=low, yellow=moderate, red=high */
function corrColor(value: number): string {
  const abs = Math.abs(value);
  if (abs > 0.7) return "bg-red-500/70";
  if (abs > 0.4) return "bg-yellow-500/60";
  return "bg-green-500/50";
}

function corrTextColor(value: number): string {
  const abs = Math.abs(value);
  if (abs > 0.7) return "text-red-900";
  if (abs > 0.4) return "text-yellow-900";
  return "text-green-900";
}

function HeatmapGrid({ data }: { data: CorrelationMatrixData }) {
  const { symbols, symbol_names, matrix } = data;
  const n = symbols.length;

  // Show at most 10x10, otherwise truncate
  const maxShow = Math.min(n, 10);
  const showSymbols = symbols.slice(0, maxShow);
  const showNames = symbol_names.slice(0, maxShow);

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-xs">
        <thead>
          <tr>
            <th className="p-1 text-left font-medium text-muted-foreground" />
            {showNames.map((name, j) => (
              <th
                key={j}
                className="p-1 text-center font-medium text-muted-foreground"
                style={{ writingMode: "vertical-lr", maxWidth: 40 }}
                title={`${showSymbols[j]} ${name}`}
              >
                {name.length > 3 ? name.slice(0, 3) : name}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {showSymbols.map((sym, i) => (
            <tr key={sym}>
              <td
                className="p-1 text-right font-medium text-muted-foreground whitespace-nowrap"
                title={`${sym} ${showNames[i]}`}
              >
                {showNames[i].length > 4
                  ? showNames[i].slice(0, 4)
                  : showNames[i]}
              </td>
              {showSymbols.map((_, j) => {
                const val = matrix[i]?.[j] ?? 0;
                return (
                  <td key={j} className="p-0.5">
                    <div
                      className={`flex h-8 w-8 items-center justify-center rounded ${corrColor(val)} ${corrTextColor(val)} font-medium`}
                      title={`${showNames[i]} ↔ ${showNames[j]}: ${val.toFixed(2)}`}
                    >
                      {i === j ? "1" : val.toFixed(2)}
                    </div>
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function AlertPairs({ pairs }: { pairs: CorrelationPair[] }) {
  const alertPairs = pairs.filter((p) => p.is_alert);
  if (alertPairs.length === 0) {
    return (
      <p className="text-sm text-green-600">
        ✓ 未发现高相关持仓对（相关系数 &gt; 0.7），组合分散度良好
      </p>
    );
  }

  return (
    <div className="space-y-2">
      <p className="text-sm font-medium text-red-600">
        ⚠ 发现 {alertPairs.length} 对高相关持仓，风险集中
      </p>
      <div className="space-y-1">
        {alertPairs.slice(0, 5).map((p) => (
          <div
            key={`${p.symbol_a}-${p.symbol_b}`}
            className="flex items-center justify-between rounded bg-red-50 px-2 py-1 text-sm"
          >
            <span>
              {p.name_a} ↔ {p.name_b}
            </span>
            <span className="font-mono text-red-700">
              {p.correlation.toFixed(2)}
            </span>
          </div>
        ))}
        {alertPairs.length > 5 && (
          <p className="text-xs text-muted-foreground">
            还有 {alertPairs.length - 5} 对...
          </p>
        )}
      </div>
    </div>
  );
}

function DiversificationBadge({
  score,
}: {
  score: CorrelationMatrixData["diversification_score"];
}) {
  const colorMap: Record<string, string> = {
    优秀: "bg-green-100 text-green-800",
    良好: "bg-blue-100 text-blue-800",
    一般: "bg-yellow-100 text-yellow-800",
    较差: "bg-red-100 text-red-800",
  };

  return (
    <div className="flex items-center gap-2">
      <span className="text-2xl font-bold">{score.score.toFixed(0)}</span>
      <span className="text-sm text-muted-foreground">/ 100</span>
      <span
        className={`rounded px-2 py-0.5 text-xs font-medium ${colorMap[score.label] || "bg-gray-100"}`}
      >
        {score.label}
      </span>
    </div>
  );
}

function RiskContributionChart({
  contributions,
}: {
  contributions: CorrelationMatrixData["risk_contributions"];
}) {
  if (!contributions || contributions.length === 0) return null;

  const maxRc = Math.max(...contributions.map((c) => c.risk_contribution), 0.01);

  return (
    <div className="space-y-1.5">
      {contributions.slice(0, 8).map((c) => {
        const widthPct = (Math.abs(c.risk_contribution) / maxRc) * 100;
        const isHigh = Math.abs(c.risk_contribution) > 0.3;
        return (
          <div key={c.symbol} className="space-y-0.5">
            <div className="flex items-center justify-between text-xs">
              <span className="truncate" title={c.name}>
                {c.name}
              </span>
              <span className={isHigh ? "font-medium text-red-600" : "text-muted-foreground"}>
                {(c.risk_contribution * 100).toFixed(1)}%
              </span>
            </div>
            <div className="h-1.5 w-full rounded-full bg-muted">
              <div
                className={`h-1.5 rounded-full ${isHigh ? "bg-red-500" : "bg-blue-400"} transition-all`}
                style={{ width: `${widthPct}%` }}
              />
            </div>
          </div>
        );
      })}
    </div>
  );
}

function CorrelationMatrixContent() {
  const [data, setData] = useState<CorrelationMatrixData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.dashboard
      .correlationMatrix()
      .then(setData)
      .catch(() => setData(null))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-6">
        <div className="h-6 w-6 animate-spin rounded-full border-2 border-primary border-t-transparent" />
      </div>
    );
  }

  if (!data) {
    return (
      <p className="py-4 text-center text-sm text-muted-foreground">
        数据不足，至少需要 5 个交易日的快照数据
      </p>
    );
  }

  return (
    <div className="space-y-4">
      {/* Diversification Score */}
      <div className="rounded-lg bg-muted/50 p-3">
        <p className="mb-1 text-xs font-medium text-muted-foreground">
          有效分散度评分
        </p>
        <DiversificationBadge score={data.diversification_score} />
      </div>

      {/* Heatmap */}
      {data.symbols.length >= 2 && (
        <div>
          <p className="mb-2 text-xs font-medium text-muted-foreground">
            相关性热力图
          </p>
          <HeatmapGrid data={data} />
          <div className="mt-2 flex items-center gap-3 text-xs text-muted-foreground">
            <span className="flex items-center gap-1">
              <span className="inline-block h-3 w-3 rounded bg-green-500/50" />
              低相关
            </span>
            <span className="flex items-center gap-1">
              <span className="inline-block h-3 w-3 rounded bg-yellow-500/60" />
              中等相关
            </span>
            <span className="flex items-center gap-1">
              <span className="inline-block h-3 w-3 rounded bg-red-500/70" />
              高相关
            </span>
          </div>
        </div>
      )}

      {/* Alert pairs */}
      <AlertPairs pairs={data.pairs} />

      {/* Risk contributions */}
      {data.risk_contributions && data.risk_contributions.length > 0 && (
        <div>
          <p className="mb-2 text-xs font-medium text-muted-foreground">
            风险贡献
          </p>
          <RiskContributionChart contributions={data.risk_contributions} />
        </div>
      )}

      <p className="text-xs text-muted-foreground">
        基于近 {data.period_days} 个交易日数据计算
      </p>
    </div>
  );
}

export function CorrelationMatrixCard() {
  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="text-base">持仓相关性</CardTitle>
        <p className="text-sm text-muted-foreground">
          检查持仓间的隐藏相关性，评估组合分散度
        </p>
      </CardHeader>
      <CardContent>
        <ErrorBoundary>
          <CorrelationMatrixContent />
        </ErrorBoundary>
      </CardContent>
    </Card>
  );
}
