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
import type { AssetType } from "@/types";

const ASSET_TYPES: AssetType[] = ["股票", "基金", "债券", "现金", "其他"];

export function AddHoldingForm({ onSuccess }: { onSuccess: () => void }) {
  const [symbol, setSymbol] = useState("");
  const [name, setName] = useState("");
  const [assetType, setAssetType] = useState<AssetType>("股票");
  const [quantity, setQuantity] = useState("");
  const [costPrice, setCostPrice] = useState("");
  const [latestPrice, setLatestPrice] = useState("");
  const [account, setAccount] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      await api.holdings.create({
        symbol,
        name,
        asset_type: assetType,
        quantity: parseFloat(quantity),
        cost_price: parseFloat(costPrice),
        latest_price: latestPrice ? parseFloat(latestPrice) : undefined,
        account: account || undefined,
      });
      toast.success(`已添加「${name}」`);
      setSymbol("");
      setName("");
      setQuantity("");
      setCostPrice("");
      setLatestPrice("");
      setAccount("");
      onSuccess();
    } catch {
      toast.error("添加失败，请检查输入");
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">添加持仓</CardTitle>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="symbol">标的代码</Label>
              <Input
                id="symbol"
                value={symbol}
                onChange={(e) => setSymbol(e.target.value)}
                placeholder="如 600519"
                required
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="name">标的名称</Label>
              <Input
                id="name"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="如 贵州茅台"
                required
              />
            </div>
          </div>

          <div className="grid grid-cols-3 gap-4">
            <div className="space-y-2">
              <Label>资产类型</Label>
              <Select
                value={assetType}
                onValueChange={(v) => setAssetType(v as AssetType)}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {ASSET_TYPES.map((type) => (
                    <SelectItem key={type} value={type}>
                      {type}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label htmlFor="quantity">数量</Label>
              <Input
                id="quantity"
                type="number"
                step="0.0001"
                min="0"
                value={quantity}
                onChange={(e) => setQuantity(e.target.value)}
                placeholder="持有数量"
                required
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="costPrice">成本价</Label>
              <Input
                id="costPrice"
                type="number"
                step="0.0001"
                min="0"
                value={costPrice}
                onChange={(e) => setCostPrice(e.target.value)}
                placeholder="每股/每份成本"
                required
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="latestPrice">最新价格（可选）</Label>
              <Input
                id="latestPrice"
                type="number"
                step="0.0001"
                min="0"
                value={latestPrice}
                onChange={(e) => setLatestPrice(e.target.value)}
                placeholder="当前市价"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="account">账户（可选）</Label>
              <Input
                id="account"
                value={account}
                onChange={(e) => setAccount(e.target.value)}
                placeholder="如：张三-华泰"
              />
            </div>
          </div>

          <Button type="submit" disabled={loading}>
            {loading ? "添加中..." : "添加持仓"}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}
