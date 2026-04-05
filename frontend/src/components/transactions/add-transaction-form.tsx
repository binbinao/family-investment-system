"use client";

import { useEffect, useMemo, useState } from "react";
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
import {
  holdingPanelDescription,
  transactionFormCopy,
  transactionTypesForAsset,
} from "@/lib/asset-type-meta";
import { AssetTypeToggle } from "@/components/trade/asset-type-toggle";
import type { AssetType, Holding, TransactionType } from "@/types";

export function AddTransactionForm({
  holdings,
  onSuccess,
}: {
  holdings: Holding[];
  onSuccess: () => void;
}) {
  const [assetFilter, setAssetFilter] = useState<AssetType>("股票");
  const [holdingId, setHoldingId] = useState("");
  const [type, setType] = useState<TransactionType>("买入");
  const [quantity, setQuantity] = useState("");
  const [price, setPrice] = useState("");
  const [fee, setFee] = useState("");
  const [date, setDate] = useState(new Date().toISOString().split("T")[0]);
  const [loading, setLoading] = useState(false);

  const filteredHoldings = useMemo(
    () => holdings.filter((h) => h.asset_type === assetFilter),
    [holdings, assetFilter],
  );

  const selected = useMemo(
    () => holdings.find((h) => h.id === holdingId),
    [holdings, holdingId],
  );

  useEffect(() => {
    if (holdingId && !filteredHoldings.some((h) => h.id === holdingId)) {
      setHoldingId("");
    }
  }, [filteredHoldings, holdingId]);

  const typesForSelect =
    holdingId && selected
      ? transactionTypesForAsset(selected.asset_type)
      : transactionTypesForAsset(assetFilter);

  useEffect(() => {
    const allowed =
      holdingId && selected
        ? transactionTypesForAsset(selected.asset_type)
        : transactionTypesForAsset(assetFilter);
    setType((prev) => (allowed.includes(prev) ? prev : allowed[0]));
  }, [selected, assetFilter, holdingId]);

  const copy = selected
    ? transactionFormCopy(selected.asset_type, type)
    : transactionFormCopy(assetFilter, type);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!holdingId) {
      toast.error("请选择持仓标的");
      return;
    }
    let q: number;
    let p: number;
    if (copy.singleDividendAmount) {
      q = 1;
      p = parseFloat(price);
    } else if (copy.hidePriceUseOne) {
      q = parseFloat(quantity);
      p = 1;
    } else {
      q = parseFloat(quantity);
      p = parseFloat(price);
    }
    if (Number.isNaN(q) || q <= 0 || Number.isNaN(p) || p < 0) {
      toast.error("请填写有效的金额与数量");
      return;
    }
    setLoading(true);
    try {
      await api.transactions.create({
        holding_id: holdingId,
        type,
        quantity: q,
        price: p,
        fee: fee ? parseFloat(fee) : undefined,
        date,
      });
      toast.success("交易记录已添加");
      setQuantity("");
      setPrice("");
      setFee("");
      onSuccess();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "添加失败";
      toast.error(msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="text-base">记录交易</CardTitle>
        <p className="text-sm text-muted-foreground">
          先选资产类型以筛选标的，再按类型展示对应交易字段。
        </p>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-6">
          <AssetTypeToggle value={assetFilter} onChange={setAssetFilter} />

          <div
            key={assetFilter}
            className="space-y-4 rounded-xl border border-border/80 bg-muted/15 p-4 ring-1 ring-foreground/5"
          >
            <div>
              <p className="text-xs font-medium text-muted-foreground">
                扩展信息 · {assetFilter}
              </p>
              <p className="mt-1 text-sm text-muted-foreground">
                {holdingPanelDescription(assetFilter)}
              </p>
            </div>

            <div className="grid gap-4 sm:grid-cols-2">
              <div className="space-y-2 sm:col-span-2">
                <Label>持仓标的</Label>
                <Select
                  value={holdingId ? holdingId : undefined}
                  onValueChange={(v) => setHoldingId(v ?? "")}
                  disabled={filteredHoldings.length === 0}
                >
                  <SelectTrigger className="w-full">
                    <SelectValue
                      placeholder={
                        filteredHoldings.length === 0
                          ? `暂无「${assetFilter}」类持仓`
                          : "选择标的"
                      }
                    />
                  </SelectTrigger>
                  <SelectContent>
                    {filteredHoldings.map((h) => (
                      <SelectItem key={h.id} value={h.id}>
                        {h.name}（{h.symbol}）
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                {filteredHoldings.length === 0 && holdings.length > 0 ? (
                  <p className="text-xs text-muted-foreground">
                    当前账户下没有此类持仓，请先在「添加持仓」中录入，或切换资产类型。
                  </p>
                ) : null}
                {holdings.length === 0 ? (
                  <p className="text-xs text-muted-foreground">
                    暂无持仓，请先在「添加持仓」中添加。
                  </p>
                ) : null}
              </div>

              <div className="space-y-2 sm:col-span-2">
                <Label>交易类型</Label>
                <Select
                  value={type}
                  onValueChange={(v) => setType(v as TransactionType)}
                  disabled={filteredHoldings.length === 0}
                >
                  <SelectTrigger className="w-full">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {typesForSelect.map((t) => (
                      <SelectItem key={t} value={t}>
                        {t}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>

            {holdingId && selected ? (
              <>
                {copy.hint ? (
                  <p className="text-sm text-muted-foreground">{copy.hint}</p>
                ) : null}

                {copy.singleDividendAmount ? (
                  <div className="space-y-2">
                    <Label htmlFor="tx-dividend-amount">{copy.priceLabel}</Label>
                    <Input
                      id="tx-dividend-amount"
                      type="number"
                      step="0.01"
                      min="0"
                      value={price}
                      onChange={(e) => setPrice(e.target.value)}
                      placeholder={copy.pricePlaceholder}
                      required
                    />
                  </div>
                ) : copy.hidePriceUseOne ? (
                  <div className="space-y-2">
                    <Label htmlFor="tx-quantity">{copy.quantityLabel}</Label>
                    <Input
                      id="tx-quantity"
                      type="number"
                      step="0.01"
                      min="0"
                      value={quantity}
                      onChange={(e) => setQuantity(e.target.value)}
                      placeholder={copy.quantityPlaceholder}
                      required
                    />
                  </div>
                ) : (
                  <div className="grid gap-4 sm:grid-cols-3">
                    <div className="space-y-2">
                      <Label htmlFor="tx-quantity">{copy.quantityLabel}</Label>
                      <Input
                        id="tx-quantity"
                        type="number"
                        step="0.0001"
                        min="0"
                        value={quantity}
                        onChange={(e) => setQuantity(e.target.value)}
                        placeholder={copy.quantityPlaceholder}
                        required
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="tx-price">{copy.priceLabel}</Label>
                      <Input
                        id="tx-price"
                        type="number"
                        step="0.0001"
                        min="0"
                        value={price}
                        onChange={(e) => setPrice(e.target.value)}
                        placeholder={copy.pricePlaceholder}
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
                )}

                {copy.singleDividendAmount || copy.hidePriceUseOne ? (
                  <div className="space-y-2">
                    <Label htmlFor="tx-fee-only">手续费（可选）</Label>
                    <Input
                      id="tx-fee-only"
                      type="number"
                      step="0.01"
                      min="0"
                      value={fee}
                      onChange={(e) => setFee(e.target.value)}
                    />
                  </div>
                ) : null}

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
              </>
            ) : (
              <p className="text-sm text-muted-foreground">
                请选择一条持仓后，将显示与「{assetFilter}」匹配的数量、价格等输入项。
              </p>
            )}
          </div>

          <Button
            type="submit"
            disabled={loading || !holdingId || filteredHoldings.length === 0}
          >
            {loading ? "提交中..." : "记录交易"}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}
