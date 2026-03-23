"use client";

import { useState } from "react";
import { toast } from "sonner";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { api } from "@/lib/api";
import type { Holding, TransactionType } from "@/types";

const TRANSACTION_TYPES: TransactionType[] = [
  "买入",
  "卖出",
  "现金分红",
  "红利再投资",
];

export function AddTransactionForm({
  holdings,
  onSuccess,
}: {
  holdings: Holding[];
  onSuccess: () => void;
}) {
  const [holdingId, setHoldingId] = useState("");
  const [type, setType] = useState<TransactionType>("买入");
  const [quantity, setQuantity] = useState("");
  const [price, setPrice] = useState("");
  const [fee, setFee] = useState("");
  const [date, setDate] = useState(new Date().toISOString().split("T")[0]);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!holdingId) {
      toast.error("请选择持仓标的");
      return;
    }
    setLoading(true);
    try {
      await api.transactions.create({
        holding_id: holdingId,
        type,
        quantity: parseFloat(quantity),
        price: parseFloat(price),
        fee: fee ? parseFloat(fee) : undefined,
        date,
      });
      toast.success("交易记录已添加");
      setQuantity("");
      setPrice("");
      setFee("");
      onSuccess();
    } catch (err: any) {
      toast.error(err.message || "添加失败");
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">记录交易</CardTitle>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label>持仓标的</Label>
              <Select value={holdingId} onValueChange={(v) => setHoldingId(v ?? "")}>
                <SelectTrigger>
                  <SelectValue placeholder="选择标的" />
                </SelectTrigger>
                <SelectContent>
                  {holdings.map((h) => (
                    <SelectItem key={h.id} value={h.id}>
                      {h.name}（{h.symbol}）
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label>交易类型</Label>
              <Select
                value={type}
                onValueChange={(v) => setType(v as TransactionType)}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {TRANSACTION_TYPES.map((t) => (
                    <SelectItem key={t} value={t}>
                      {t}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          <div className="grid grid-cols-3 gap-4">
            <div className="space-y-2">
              <Label htmlFor="tx-quantity">数量</Label>
              <Input
                id="tx-quantity"
                type="number"
                step="0.0001"
                min="0"
                value={quantity}
                onChange={(e) => setQuantity(e.target.value)}
                required
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="tx-price">价格</Label>
              <Input
                id="tx-price"
                type="number"
                step="0.0001"
                min="0"
                value={price}
                onChange={(e) => setPrice(e.target.value)}
                required
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="tx-fee">手续费（可选）</Label>
              <Input
                id="tx-fee"
                type="number"
                step="0.01"
                min="0"
                value={fee}
                onChange={(e) => setFee(e.target.value)}
              />
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="tx-date">交易日期</Label>
            <Input
              id="tx-date"
              type="date"
              value={date}
              onChange={(e) => setDate(e.target.value)}
              required
            />
          </div>

          <Button type="submit" disabled={loading || !holdingId}>
            {loading ? "提交中..." : "记录交易"}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}
