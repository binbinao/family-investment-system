"use client";

import { useState } from "react";
import { toast } from "sonner";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";
import type { Holding } from "@/types";

export function UpdatePriceDialog({
  open,
  onOpenChange,
  holding,
  onSuccess,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  holding: Holding;
  onSuccess: () => void;
}) {
  const [price, setPrice] = useState(
    holding.latest_price?.toString() || ""
  );
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const value = parseFloat(price);
    if (isNaN(value) || value < 0) {
      toast.error("请输入有效的价格");
      return;
    }
    setLoading(true);
    try {
      await api.holdings.updatePrice(holding.id, value);
      toast.success(`已更新「${holding.name}」最新价格`);
      onOpenChange(false);
      onSuccess();
    } catch {
      toast.error("更新失败");
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>
            更新价格 - {holding.name}（{holding.symbol}）
          </DialogTitle>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="price">最新价格</Label>
            <Input
              id="price"
              type="number"
              step="0.0001"
              min="0"
              value={price}
              onChange={(e) => setPrice(e.target.value)}
              placeholder="请输入最新价格"
              autoFocus
              required
            />
          </div>
          <div className="flex justify-end gap-2">
            <Button
              type="button"
              variant="outline"
              onClick={() => onOpenChange(false)}
            >
              取消
            </Button>
            <Button type="submit" disabled={loading}>
              {loading ? "更新中..." : "确认"}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
}
