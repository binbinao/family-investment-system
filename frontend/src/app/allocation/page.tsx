"use client";

import { useCallback, useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { api } from "@/lib/api";
import { toast } from "sonner";
import type { AllocationTarget, DeviationResult } from "@/types";
import { formatCurrency } from "@/lib/format";
import { RebalanceCard } from "@/components/dashboard/rebalance-card";

const ASSET_TYPES = ["股票", "基金", "债券", "现金", "其他"];

export default function AllocationPage() {
  const [targets, setTargets] = useState<Record<string, string>>({});
  const [deviation, setDeviation] = useState<DeviationResult | null>(null);
  const [saving, setSaving] = useState(false);

  const fetchData = useCallback(async () => {
    try {
      const [t, d] = await Promise.all([
        api.allocation.targets(),
        api.allocation.deviation(),
      ]);
      const map: Record<string, string> = {};
      for (const at of ASSET_TYPES) {
        const found = t.find((x: AllocationTarget) => x.asset_type === at);
        map[at] = found ? String(found.target_ratio) : "";
      }
      setTargets(map);
      setDeviation(d);
    } catch {
      // handled by auth guard
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const handleSave = async () => {
    const items = ASSET_TYPES.filter((at) => targets[at] && Number(targets[at]) > 0).map(
      (at) => ({
        asset_type: at,
        target_ratio: Number(targets[at]),
      }),
    );

    const total = items.reduce((s, i) => s + i.target_ratio, 0);
    if (Math.abs(total - 100) > 0.01) {
      toast.error(`目标比例合计应为 100%，当前为 ${total.toFixed(1)}%`);
      return;
    }

    setSaving(true);
    try {
      await api.allocation.setTargets(items);
      toast.success("目标配置已保存");
      await fetchData();
    } catch {
      toast.error("保存失败");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">资产配置目标</h1>
        <p className="text-sm text-muted-foreground">
          设定各类资产的目标占比，系统将在偏离超 10% 时提醒
        </p>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="text-base">目标比例设定</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {ASSET_TYPES.map((at) => (
              <div key={at} className="flex items-center gap-3">
                <Label className="w-16 text-right">{at}</Label>
                <Input
                  type="number"
                  min="0"
                  max="100"
                  step="1"
                  placeholder="0"
                  value={targets[at] || ""}
                  onChange={(e) =>
                    setTargets((prev) => ({
                      ...prev,
                      [at]: e.target.value,
                    }))
                  }
                  className="w-24"
                />
                <span className="text-sm text-muted-foreground">%</span>
              </div>
            ))}
            <div className="pt-2 text-sm text-muted-foreground">
              合计：
              {ASSET_TYPES.reduce(
                (s, at) => s + (Number(targets[at]) || 0),
                0,
              ).toFixed(1)}
              %
            </div>
            <Button onClick={handleSave} disabled={saving}>
              {saving ? "保存中..." : "保存目标"}
            </Button>
          </CardContent>
        </Card>

        {deviation && deviation.has_targets && (
          <Card>
            <CardHeader>
              <CardTitle className="text-base">当前偏离情况</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {deviation.deviations.map((d) => (
                  <div
                    key={d.asset_type}
                    className={`rounded-md p-3 ${d.is_alert ? "bg-yellow-50" : "bg-muted/50"}`}
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-medium">{d.asset_type}</span>
                      <span
                        className={
                          d.is_alert
                            ? "font-medium text-yellow-700"
                            : "text-muted-foreground"
                        }
                      >
                        {d.actual_pct}% / 目标 {d.target_pct}%
                      </span>
                    </div>
                    {d.adjust_direction && (
                      <p className="mt-1 text-sm text-muted-foreground">
                        建议{d.adjust_direction}约{" "}
                        {formatCurrency(d.adjust_amount)}
                      </p>
                    )}
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}
      </div>

      {/* Tax-aware rebalance card */}
      <RebalanceCard />
    </div>
  );
}
