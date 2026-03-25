"use client";

import { useCallback, useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";
import { formatDate } from "@/lib/format";
import type { DailyReportItem } from "@/types";
import ReactMarkdown from "react-markdown";
import { toast } from "sonner";
import { RefreshCw } from "lucide-react";

export default function ReportsPage() {
  const [reports, setReports] = useState<DailyReportItem[]>([]);
  const [selected, setSelected] = useState<DailyReportItem | null>(null);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);

  const fetchReports = useCallback(async () => {
    try {
      const data = await api.reports.list(30);
      setReports(data);
      if (data.length > 0 && !selected) {
        setSelected(data[0]);
      }
    } catch {
      // ignore
    } finally {
      setLoading(false);
    }
  }, [selected]);

  useEffect(() => {
    fetchReports();
  }, [fetchReports]);

  const handleGenerate = async () => {
    setGenerating(true);
    try {
      const result = await api.reports.generate();
      if (result.success) {
        toast.success("晨报生成成功");
        await fetchReports();
      } else {
        toast.error(result.message || "生成失败");
      }
    } catch {
      toast.error("生成失败");
    } finally {
      setGenerating(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-primary border-t-transparent" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">AI 晨报</h1>
          <p className="text-sm text-muted-foreground">
            每日与持仓相关的市场摘要
          </p>
        </div>
        <Button onClick={handleGenerate} disabled={generating} variant="outline">
          <RefreshCw className={`mr-1 h-4 w-4 ${generating ? "animate-spin" : ""}`} />
          {generating ? "生成中..." : "手动生成"}
        </Button>
      </div>

      <div className="grid gap-6 lg:grid-cols-4">
        <div className="space-y-2 lg:col-span-1">
          {reports.length === 0 ? (
            <p className="text-sm text-muted-foreground py-4">暂无晨报</p>
          ) : (
            reports.map((r) => (
              <Card
                key={r.date}
                className={`cursor-pointer transition-colors ${
                  selected?.date === r.date ? "border-primary" : "hover:bg-accent/50"
                }`}
                onClick={() => setSelected(r)}
              >
                <CardContent className="p-3">
                  <div className="text-xs text-muted-foreground">
                    {formatDate(r.date)}
                  </div>
                  <p className="mt-1 text-sm line-clamp-2">{r.summary}</p>
                </CardContent>
              </Card>
            ))
          )}
        </div>

        <div className="lg:col-span-3">
          {selected ? (
            <Card>
              <CardHeader>
                <CardTitle className="text-base">
                  {formatDate(selected.date)} 晨报
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="prose prose-sm max-w-none dark:prose-invert">
                  <ReactMarkdown>{selected.content_markdown}</ReactMarkdown>
                </div>
              </CardContent>
            </Card>
          ) : (
            <div className="flex items-center justify-center py-20 text-sm text-muted-foreground">
              选择左侧晨报查看详情
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
