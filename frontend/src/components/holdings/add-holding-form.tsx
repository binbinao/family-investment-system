"use client";

import { useState } from "react";
import { toast } from "sonner";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";
import {
  holdingFormCopy,
  holdingPanelDescription,
} from "@/lib/asset-type-meta";
import { AssetTypeToggle } from "@/components/trade/asset-type-toggle";
import type { AssetType } from "@/types";

export function AddHoldingForm({ onSuccess }: { onSuccess: () => void }) {
  const [symbol, setSymbol] = useState("");
  const [name, setName] = useState("");
  const [assetType, setAssetType] = useState<AssetType>("股票");
  const [sector, setSector] = useState("");
  const [quantity, setQuantity] = useState("");
  const [costPrice, setCostPrice] = useState("");
  const [latestPrice, setLatestPrice] = useState("");
  const [purchaseDate, setPurchaseDate] = useState("");
  const [account, setAccount] = useState("");
  const [loading, setLoading] = useState(false);

  const copy = holdingFormCopy(assetType);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      const q = parseFloat(quantity);
      const isCash = copy.isCashSemantics;
      const cost = isCash ? 1 : parseFloat(costPrice);
      const latest = isCash
        ? 1
        : latestPrice
          ? parseFloat(latestPrice)
          : undefined;
      await api.holdings.create({
        symbol,
        name,
        asset_type: assetType,
        sector: sector || undefined,
        quantity: q,
        cost_price: cost,
        latest_price: latest,
        purchase_date: purchaseDate || undefined,
        cost_method: "fifo",
        account: account || undefined,
      });
      toast.success(`已添加「${name}」`);
      setSymbol("");
      setName("");
      setSector("");
      setQuantity("");
      setCostPrice("");
      setLatestPrice("");
      setPurchaseDate("");
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
      <CardHeader className="pb-3">
        <CardTitle className="text-base">添加持仓</CardTitle>
        <p className="text-sm text-muted-foreground">
          先选择资产类型，再填写下方对应字段。
        </p>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-6">
          <AssetTypeToggle value={assetType} onChange={setAssetType} />

          <div
            key={assetType}
            className="space-y-4 rounded-xl border border-border/80 bg-muted/15 p-4 ring-1 ring-foreground/5"
          >
            <div>
              <p className="text-xs font-medium text-muted-foreground">
                扩展信息 · {assetType}
              </p>
              <p className="mt-1 text-sm text-muted-foreground">
                {holdingPanelDescription(assetType)}
              </p>
            </div>

            <div className="grid gap-4 sm:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="symbol">{copy.symbolLabel}</Label>
                <Input
                  id="symbol"
                  value={symbol}
                  onChange={(e) => setSymbol(e.target.value)}
                  placeholder={copy.symbolPlaceholder}
                  required
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="name">{copy.nameLabel}</Label>
                <Input
                  id="name"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder={copy.namePlaceholder}
                  required
                />
              </div>
            </div>

            {assetType === "股票" && (
              <div className="grid gap-4 sm:grid-cols-2">
                <div className="space-y-2">
                  <Label htmlFor="sector">行业（可选）</Label>
                  <Input
                    id="sector"
                    value={sector}
                    onChange={(e) => setSector(e.target.value)}
                    placeholder="如：食品饮料、电子、银行"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="purchaseDate">买入日期（可选）</Label>
                  <Input
                    id="purchaseDate"
                    type="date"
                    value={purchaseDate}
                    onChange={(e) => setPurchaseDate(e.target.value)}
                  />
                </div>
              </div>
            )}

            <div
              className={
                copy.showCostAndLatest
                  ? "grid gap-4 sm:grid-cols-3"
                  : "grid gap-4 sm:grid-cols-2"
              }
            >
              <div className="space-y-2 sm:col-span-1">
                <Label htmlFor="quantity">{copy.quantityLabel}</Label>
                <Input
                  id="quantity"
                  type="number"
                  step="0.0001"
                  min="0"
                  value={quantity}
                  onChange={(e) => setQuantity(e.target.value)}
                  placeholder={copy.quantityPlaceholder}
                  required
                />
              </div>
              {copy.showCostAndLatest ? (
                <div className="space-y-2">
                  <Label htmlFor="costPrice">{copy.costPriceLabel}</Label>
                  <Input
                    id="costPrice"
                    type="number"
                    step="0.0001"
                    min="0"
                    value={costPrice}
                    onChange={(e) => setCostPrice(e.target.value)}
                    placeholder={copy.costPlaceholder}
                    required
                  />
                </div>
              ) : null}
            </div>

            {copy.showCostAndLatest ? (
              <div className="grid gap-4 sm:grid-cols-2">
                <div className="space-y-2">
                  <Label htmlFor="latestPrice">{copy.latestPriceLabel}</Label>
                  <Input
                    id="latestPrice"
                    type="number"
                    step="0.0001"
                    min="0"
                    value={latestPrice}
                    onChange={(e) => setLatestPrice(e.target.value)}
                    placeholder={copy.latestPlaceholder}
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
            ) : (
              <div className="space-y-2">
                <Label htmlFor="account-cash">账户（可选）</Label>
                <Input
                  id="account-cash"
                  value={account}
                  onChange={(e) => setAccount(e.target.value)}
                  placeholder="如：张三-工行活期"
                />
              </div>
            )}
          </div>

          <Button type="submit" disabled={loading}>
            {loading ? "添加中..." : "添加持仓"}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}
