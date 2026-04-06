"use client";

import { useEffect, useState } from "react";
import { RefreshCw, AlertTriangle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";
import { formatDateTime } from "@/lib/format";
import type { MarketStatus } from "@/types";
import { toast } from "sonner";

export function MarketStatusBar({
  onRefreshComplete,
}: {
  /** 行情写入后端成功后刷新总览/持仓等数据 */
  onRefreshComplete?: () => void;
}) {
  const [statuses, setStatuses] = useState<MarketStatus[]>([]);
  const [refreshing, setRefreshing] = useState(false);

  const fetchStatus = () => {
    api.market.status().then(setStatuses).catch(() => {});
  };

  useEffect(() => {
    fetchStatus();
  }, []);

  const handleRefresh = async () => {
    setRefreshing(true);
    try {
      const result = await api.market.refresh();
      toast.success(
        `行情刷新完成：成功 ${result.success}，失败 ${result.failed}，跳过 ${result.skipped}`,
      );
      fetchStatus();
      onRefreshComplete?.();
    } catch {
      toast.error("行情刷新失败");
    } finally {
      setRefreshing(false);
    }
  };

  const hasStale = statuses.some((s) => s.is_stale);
  const latestUpdate = statuses.length > 0 ? statuses[0].updated_at : null;

  return (
    <div className="flex items-center gap-3 text-sm text-muted-foreground">
      {hasStale && (
        <div className="flex items-center gap-1 text-yellow-600">
          <AlertTriangle className="h-4 w-4" />
          <span>行情更新中断，显示的是历史数据</span>
        </div>
      )}
      {latestUpdate && (
        <span>最近更新：{formatDateTime(latestUpdate)}</span>
      )}
      <Button
        variant="ghost"
        size="sm"
        onClick={handleRefresh}
        disabled={refreshing}
      >
        <RefreshCw
          className={`mr-1 h-4 w-4 ${refreshing ? "animate-spin" : ""}`}
        />
        刷新行情
      </Button>
    </div>
  );
}
