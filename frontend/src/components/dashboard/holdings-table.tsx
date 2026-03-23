"use client";

import { useState } from "react";
import { toast } from "sonner";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { formatCurrency, formatPercent, formatNumber, profitColor } from "@/lib/format";
import { UpdatePriceDialog } from "@/components/holdings/update-price-dialog";
import { EditHoldingDialog } from "@/components/holdings/edit-holding-dialog";
import { api } from "@/lib/api";
import type { Holding } from "@/types";

export function HoldingsTable({
  holdings,
  onRefresh,
}: {
  holdings: Holding[];
  onRefresh: () => void;
}) {
  const [priceDialogOpen, setPriceDialogOpen] = useState(false);
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [selectedHolding, setSelectedHolding] = useState<Holding | null>(null);

  const handleDelete = async (holding: Holding) => {
    if (!confirm(`确定要删除「${holding.name}」吗？`)) return;
    try {
      await api.holdings.delete(holding.id);
      toast.success(`已删除「${holding.name}」`);
      onRefresh();
    } catch {
      toast.error("删除失败");
    }
  };

  if (holdings.length === 0) {
    return (
      <div className="rounded-lg border border-dashed p-8 text-center">
        <p className="text-muted-foreground">暂无持仓，去记账页添加吧</p>
      </div>
    );
  }

  return (
    <>
      <div className="rounded-lg border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>标的</TableHead>
              <TableHead>类型</TableHead>
              <TableHead className="text-right">数量</TableHead>
              <TableHead className="text-right">成本价</TableHead>
              <TableHead className="text-right">最新价</TableHead>
              <TableHead className="text-right">市值</TableHead>
              <TableHead className="text-right">盈亏</TableHead>
              <TableHead className="text-right">操作</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {holdings.map((h) => (
              <TableRow key={h.id}>
                <TableCell>
                  <div>
                    <p className="font-medium">{h.name}</p>
                    <p className="text-xs text-muted-foreground">{h.symbol}</p>
                  </div>
                </TableCell>
                <TableCell>
                  <Badge variant="secondary">{h.asset_type}</Badge>
                </TableCell>
                <TableCell className="text-right tabular-nums">
                  {formatNumber(h.quantity)}
                </TableCell>
                <TableCell className="text-right tabular-nums">
                  {formatCurrency(h.cost_price)}
                </TableCell>
                <TableCell className="text-right tabular-nums">
                  {h.latest_price != null
                    ? formatCurrency(h.latest_price)
                    : "--"}
                </TableCell>
                <TableCell className="text-right tabular-nums">
                  {formatCurrency(h.market_value)}
                </TableCell>
                <TableCell className="text-right">
                  <div>
                    <p className={`tabular-nums font-medium ${profitColor(h.profit_loss)}`}>
                      {formatCurrency(h.profit_loss)}
                    </p>
                    <p className={`text-xs tabular-nums ${profitColor(h.profit_loss_pct)}`}>
                      {formatPercent(h.profit_loss_pct)}
                    </p>
                  </div>
                </TableCell>
                <TableCell className="text-right">
                  <div className="flex justify-end gap-1">
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => {
                        setSelectedHolding(h);
                        setPriceDialogOpen(true);
                      }}
                    >
                      报价
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => {
                        setSelectedHolding(h);
                        setEditDialogOpen(true);
                      }}
                    >
                      编辑
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      className="text-destructive hover:text-destructive"
                      onClick={() => handleDelete(h)}
                    >
                      删除
                    </Button>
                  </div>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>

      {selectedHolding && (
        <>
          <UpdatePriceDialog
            open={priceDialogOpen}
            onOpenChange={setPriceDialogOpen}
            holding={selectedHolding}
            onSuccess={onRefresh}
          />
          <EditHoldingDialog
            open={editDialogOpen}
            onOpenChange={setEditDialogOpen}
            holding={selectedHolding}
            onSuccess={onRefresh}
          />
        </>
      )}
    </>
  );
}
