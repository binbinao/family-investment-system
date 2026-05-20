"use client";

import { useCallback, useEffect, useState } from "react";
import { api } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ErrorBoundary } from "@/components/ui/error-boundary";
import { formatCurrency } from "@/lib/format";
import type { RebalanceResult, RebalanceSuggestion, TradeCostDetail } from "@/types";

function CostBreakdown({ detail }: { detail: TradeCostDetail }) {
  const items = [
    { label: "印花税", value: detail.stamp_tax },
    { label: "佣金", value: detail.commission },
    { label: "赎回费", value: detail.redemption_fee },
    { label: "红利税影响", value: detail.dividend_tax },
  ].filter((i) => i.value > 0);

  if (items.length === 0) return null;

  return (
    <div className="mt-1 space-y-0.5 text-xs text-muted-foreground">
      {items.map((i) => (
        <div key={i.label} className="flex justify-between">
          <span>{i.label}</span>
          <span>{formatCurrency(i.value)}</span>
        </div>
      ))}
      <div className="flex justify-between border-t pt-0.5 font-medium text-foreground">
        <span>成本合计</span>
        <span>{formatCurrency(detail.total_cost)}</span>
      </div>
    </div>
  );
}

function SuggestionRow({ s }: { s: RebalanceSuggestion }) {
  const actionColor =
    s.action === "买入"
      ? "text-red-600"
      : s.action === "卖出"
        ? "text-green-600"
        : "text-muted-foreground";

  const actionBg =
    s.action === "买入"
      ? "bg-red-50"
      : s.action === "卖出"
        ? "bg-green-50"
        : "bg-muted/50";

  return (
    <div
      className={`rounded-lg p-3 ${actionBg} ${!s.is_recommended && s.action !== "持有" ? "opacity-60" : ""}`}
    >
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="font-medium">{s.asset_type}</span>
          <span className={`text-sm font-medium ${actionColor}`}>
            {s.action}
          </span>
          {!s.is_recommended && s.action !== "持有" && (
            <span className="rounded bg-gray-100 px-1.5 py-0.5 text-xs text-gray-500">
              成本过高
            </span>
          )}
        </div>
        {s.adjust_amount > 0 && (
          <span className="font-medium">{formatCurrency(s.adjust_amount)}</span>
        )}
      </div>
      {s.action !== "持有" && s.adjust_amount > 0 && (
        <div className="mt-2">
          <CostBreakdown detail={s.cost_detail} />
          <div className="mt-1 flex items-center justify-between text-sm">
            <span>税后净收益</span>
            <span
              className={
                s.net_benefit > 0 ? "font-medium text-red-600" : "text-green-600"
              }
            >
              {s.net_benefit > 0 ? "+" : ""}
              {formatCurrency(s.net_benefit)}
            </span>
          </div>
        </div>
      )}
    </div>
  );
}

function RebalanceContent() {
  const [result, setResult] = useState<RebalanceResult | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchData = useCallback(async () => {
    try {
      const data = await api.allocation.deviation();
      // Fetch rebalance using the same threshold
      const rebalance = await api.dashboard.rebalance(
        data.has_targets ? 10 : 10,
      );
      setResult(rebalance);
    } catch {
      setResult(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-6">
        <div className="h-6 w-6 animate-spin rounded-full border-2 border-primary border-t-transparent" />
      </div>
    );
  }

  if (!result || !result.has_targets) {
    return (
      <p className="py-4 text-center text-sm text-muted-foreground">
        请先设置资产配置目标
      </p>
    );
  }

  const activeSuggestions = result.suggestions.filter(
    (s) => s.action !== "持有",
  );
  const recommendedActions = activeSuggestions.filter((s) => s.is_recommended);
  const notRecommended = activeSuggestions.filter((s) => !s.is_recommended);

  return (
    <div className="space-y-4">
      {activeSuggestions.length === 0 ? (
        <p className="py-2 text-center text-sm text-green-600">
          ✓ 当前配置在阈值内，无需再平衡
        </p>
      ) : (
        <>
          {/* Summary */}
          <div className="rounded-lg bg-muted/50 p-3">
            <div className="flex items-center justify-between text-sm">
              <span>需要调仓的资产类别</span>
              <span className="font-medium">{activeSuggestions.length}</span>
            </div>
            <div className="flex items-center justify-between text-sm">
              <span>总交易成本</span>
              <span className="font-medium text-yellow-600">
                {formatCurrency(result.total_cost)}
              </span>
            </div>
            <div className="flex items-center justify-between text-sm">
              <span>总税后净收益</span>
              <span
                className={
                  result.total_net_benefit > 0
                    ? "font-medium text-red-600"
                    : "text-green-600"
                }
              >
                {result.total_net_benefit > 0 ? "+" : ""}
                {formatCurrency(result.total_net_benefit)}
              </span>
            </div>
          </div>

          {/* Recommended suggestions */}
          {recommendedActions.length > 0 && (
            <div className="space-y-2">
              <p className="text-xs font-medium text-muted-foreground">
                建议调仓（税后净收益 &gt; 0）
              </p>
              {recommendedActions.map((s) => (
                <SuggestionRow key={s.asset_type} s={s} />
              ))}
            </div>
          )}

          {/* Not recommended (cost too high) */}
          {notRecommended.length > 0 && (
            <div className="space-y-2">
              <p className="text-xs font-medium text-muted-foreground">
                不建议调仓（交易成本过高）
              </p>
              {notRecommended.map((s) => (
                <SuggestionRow key={s.asset_type} s={s} />
              ))}
            </div>
          )}

          {/* Hold items */}
          {result.suggestions.some((s) => s.action === "持有") && (
            <div className="space-y-1">
              <p className="text-xs font-medium text-muted-foreground">
                配置正常
              </p>
              <div className="flex flex-wrap gap-1">
                {result.suggestions
                  .filter((s) => s.action === "持有")
                  .map((s) => (
                    <span
                      key={s.asset_type}
                      className="rounded bg-muted px-2 py-0.5 text-xs"
                    >
                      {s.asset_type}
                    </span>
                  ))}
              </div>
            </div>
          )}
        </>
      )}

      <p className="text-xs text-muted-foreground">
        偏离阈值：{result.deviation_threshold}% · 费率：印花税0.05% + 佣金0.025%
      </p>
    </div>
  );
}

export function RebalanceCard() {
  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="text-base">智能再平衡</CardTitle>
        <p className="text-sm text-muted-foreground">
          扣除交易成本后，净收益为正才建议调仓
        </p>
      </CardHeader>
      <CardContent>
        <ErrorBoundary>
          <RebalanceContent />
        </ErrorBoundary>
      </CardContent>
    </Card>
  );
}
