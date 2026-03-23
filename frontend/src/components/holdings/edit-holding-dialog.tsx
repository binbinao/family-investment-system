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

export function EditHoldingDialog({
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
  const [name, setName] = useState(holding.name);
  const [quantity, setQuantity] = useState(holding.quantity.toString());
  const [costPrice, setCostPrice] = useState(holding.cost_price.toString());
  const [account, setAccount] = useState(holding.account || "");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      await api.holdings.update(holding.id, {
        name: name !== holding.name ? name : undefined,
        quantity:
          quantity !== holding.quantity.toString()
            ? parseFloat(quantity)
            : undefined,
        cost_price:
          costPrice !== holding.cost_price.toString()
            ? parseFloat(costPrice)
            : undefined,
        account: account !== (holding.account || "") ? account : undefined,
      });
      toast.success(`已更新「${name}」`);
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
          <DialogTitle>编辑持仓 - {holding.symbol}</DialogTitle>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="edit-name">名称</Label>
            <Input
              id="edit-name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              required
            />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="edit-quantity">数量</Label>
              <Input
                id="edit-quantity"
                type="number"
                step="0.0001"
                min="0"
                value={quantity}
                onChange={(e) => setQuantity(e.target.value)}
                required
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="edit-cost">成本价</Label>
              <Input
                id="edit-cost"
                type="number"
                step="0.0001"
                min="0"
                value={costPrice}
                onChange={(e) => setCostPrice(e.target.value)}
                required
              />
            </div>
          </div>
          <div className="space-y-2">
            <Label htmlFor="edit-account">账户（可选）</Label>
            <Input
              id="edit-account"
              value={account}
              onChange={(e) => setAccount(e.target.value)}
              placeholder="如：张三-华泰"
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
              {loading ? "保存中..." : "保存"}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
}
