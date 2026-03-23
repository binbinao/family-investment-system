"use client";

import { useEffect, useState } from "react";
import { AlertTriangle } from "lucide-react";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { api } from "@/lib/api";
import { formatCurrency } from "@/lib/format";
import type { DeviationResult } from "@/types";

export function DeviationAlert() {
  const [result, setResult] = useState<DeviationResult | null>(null);
  const [expanded, setExpanded] = useState(false);

  useEffect(() => {
    api.allocation
      .deviation()
      .then(setResult)
      .catch(() => {});
  }, []);

  if (!result || !result.has_targets || !result.has_alert) return null;

  const alertItems = result.deviations.filter((d) => d.is_alert);

  return (
    <Alert
      variant="destructive"
      className="cursor-pointer border-yellow-400 bg-yellow-50 text-yellow-800"
      onClick={() => setExpanded(!expanded)}
    >
      <AlertTriangle className="h-4 w-4 !text-yellow-600" />
      <AlertTitle className="text-yellow-800">
        配置偏离提醒
      </AlertTitle>
      <AlertDescription className="text-yellow-700">
        <p className="mb-1">
          以下资产类别偏离目标配置超过 10%，点击查看调仓建议
        </p>
        {expanded && (
          <div className="mt-3 space-y-2 text-sm">
            {alertItems.map((d) => (
              <div
                key={d.asset_type}
                className="rounded-md bg-white/60 p-2"
              >
                <div className="font-medium">
                  {d.asset_type}：目标 {d.target_pct}% → 实际{" "}
                  {d.actual_pct}%（偏离 {d.deviation > 0 ? "+" : ""}
                  {d.deviation}%）
                </div>
                {d.adjust_direction && (
                  <div className="mt-1 text-yellow-600">
                    建议{d.adjust_direction} {d.asset_type} 约{" "}
                    {formatCurrency(d.adjust_amount)}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </AlertDescription>
    </Alert>
  );
}
