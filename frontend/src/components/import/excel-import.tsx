"use client";

import { useRef, useState } from "react";
import { Download, Upload, FileSpreadsheet } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { api } from "@/lib/api";
import { toast } from "sonner";
import type { ImportResult } from "@/types";

interface ExcelImportProps {
  type: "holdings" | "transactions";
  onSuccess?: () => void;
}

export function ExcelImport({ type, onSuccess }: ExcelImportProps) {
  const [result, setResult] = useState<ImportResult | null>(null);
  const [uploading, setUploading] = useState(false);
  const fileRef = useRef<HTMLInputElement>(null);

  const label = type === "holdings" ? "持仓" : "交易";

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setUploading(true);
    setResult(null);

    try {
      const importFn =
        type === "holdings" ? api.import.holdings : api.import.transactions;
      const res = await importFn(file);
      setResult(res);

      if (res.errors.length === 0) {
        toast.success(`成功导入 ${res.success.length} 条${label}记录`);
      } else {
        toast.warning(
          `导入完成：成功 ${res.success.length} 条，失败 ${res.errors.length} 条`,
        );
      }

      onSuccess?.();
    } catch {
      toast.error("导入失败，请检查文件格式");
    } finally {
      setUploading(false);
      if (fileRef.current) fileRef.current.value = "";
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-base">
          <FileSpreadsheet className="h-5 w-5" />
          Excel 导入{label}
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <p className="text-sm text-muted-foreground">
          模板含「填写说明」工作表：按股票 / 基金 / 债券 / 现金等含义填列；现金持仓「单位成本」可留空（按
          1 处理）。首行须为表头，勿删列名。
        </p>
        <div className="flex items-center gap-3">
          <a
            href={api.import.templateUrl(type)}
            download
            className="inline-flex"
          >
            <Button variant="outline" size="sm">
              <Download className="mr-1 h-4 w-4" />
              下载{label}模板
            </Button>
          </a>

          <div className="relative">
            <input
              ref={fileRef}
              type="file"
              accept=".xlsx,.xls"
              onChange={handleUpload}
              className="absolute inset-0 cursor-pointer opacity-0"
              disabled={uploading}
            />
            <Button size="sm" disabled={uploading}>
              <Upload className="mr-1 h-4 w-4" />
              {uploading ? "导入中..." : `上传${label}文件`}
            </Button>
          </div>
        </div>

        {result && (
          <div className="space-y-2 text-sm">
            {result.success.length > 0 && (
              <div className="rounded-md bg-green-50 p-3 text-green-700">
                成功导入 {result.success.length} 条记录
              </div>
            )}
            {result.errors.length > 0 && (
              <div className="rounded-md bg-red-50 p-3 text-red-700">
                <p className="mb-1 font-medium">
                  {result.errors.length} 条记录导入失败：
                </p>
                <ul className="list-inside list-disc space-y-0.5">
                  {result.errors.map((err) => (
                    <li key={err.row}>
                      第 {err.row} 行：{err.error}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
