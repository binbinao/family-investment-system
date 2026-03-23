"use client";

import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { formatCurrency, formatDate, formatNumber, profitColor } from "@/lib/format";
import type { Transaction } from "@/types";

const TYPE_VARIANTS: Record<string, "default" | "secondary" | "destructive" | "outline"> = {
  "买入": "default",
  "卖出": "destructive",
  "现金分红": "secondary",
  "红利再投资": "outline",
};

export function TransactionList({
  transactions,
}: {
  transactions: Transaction[];
}) {
  if (transactions.length === 0) {
    return (
      <div className="rounded-lg border border-dashed p-8 text-center">
        <p className="text-muted-foreground">暂无交易记录</p>
      </div>
    );
  }

  return (
    <div className="rounded-lg border">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>日期</TableHead>
            <TableHead>标的</TableHead>
            <TableHead>类型</TableHead>
            <TableHead className="text-right">数量</TableHead>
            <TableHead className="text-right">价格</TableHead>
            <TableHead className="text-right">手续费</TableHead>
            <TableHead className="text-right">实现盈亏</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {transactions.map((t) => (
            <TableRow key={t.id}>
              <TableCell className="tabular-nums">
                {formatDate(t.date)}
              </TableCell>
              <TableCell className="font-medium">{t.symbol}</TableCell>
              <TableCell>
                <Badge variant={TYPE_VARIANTS[t.type] || "secondary"}>
                  {t.type}
                </Badge>
              </TableCell>
              <TableCell className="text-right tabular-nums">
                {formatNumber(t.quantity)}
              </TableCell>
              <TableCell className="text-right tabular-nums">
                {formatCurrency(t.price)}
              </TableCell>
              <TableCell className="text-right tabular-nums">
                {t.fee > 0 ? formatCurrency(t.fee) : "--"}
              </TableCell>
              <TableCell className={`text-right tabular-nums font-medium ${profitColor(t.realized_pnl)}`}>
                {t.realized_pnl != null
                  ? formatCurrency(t.realized_pnl)
                  : "--"}
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}
