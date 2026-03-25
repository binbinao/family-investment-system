"use client";

import { useCallback, useEffect, useState } from "react";
import { Plus, Trash2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";
import { Input } from "@/components/ui/input";
import { api } from "@/lib/api";
import { formatDateTime } from "@/lib/format";
import type { MemoItem } from "@/types";
import { toast } from "sonner";

export default function MemosPage() {
  const [memos, setMemos] = useState<MemoItem[]>([]);
  const [newContent, setNewContent] = useState("");
  const [filterSymbol, setFilterSymbol] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const fetchMemos = useCallback(async () => {
    try {
      const data = await api.memos.list(filterSymbol || undefined);
      setMemos(data);
    } catch {
      // ignore
    }
  }, [filterSymbol]);

  useEffect(() => {
    fetchMemos();
  }, [fetchMemos]);

  const handleCreate = async () => {
    if (!newContent.trim()) return;
    setSubmitting(true);
    try {
      await api.memos.create(newContent.trim());
      setNewContent("");
      toast.success("备忘录已添加");
      await fetchMemos();
    } catch {
      toast.error("添加失败");
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = async (id: string) => {
    try {
      await api.memos.delete(id);
      toast.success("已删除");
      await fetchMemos();
    } catch {
      toast.error("删除失败");
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">家庭备忘录</h1>
        <p className="text-sm text-muted-foreground">
          共享投资备忘，用 #代码 关联标的（如 #600519）
        </p>
      </div>

      <Card>
        <CardContent className="space-y-3 p-4">
          <Textarea
            value={newContent}
            onChange={(e) => setNewContent(e.target.value)}
            placeholder="写下投资备忘...&#10;用 #600519 这样的格式关联标的代码"
            rows={3}
          />
          <Button
            onClick={handleCreate}
            disabled={!newContent.trim() || submitting}
            size="sm"
          >
            <Plus className="mr-1 h-4 w-4" />
            {submitting ? "添加中..." : "添加备忘"}
          </Button>
        </CardContent>
      </Card>

      <div className="flex items-center gap-2">
        <Input
          placeholder="按标的代码过滤（如 600519）"
          value={filterSymbol}
          onChange={(e) => setFilterSymbol(e.target.value)}
          className="max-w-xs"
        />
      </div>

      <div className="space-y-3">
        {memos.length === 0 ? (
          <p className="text-sm text-muted-foreground py-4">暂无备忘录</p>
        ) : (
          memos.map((m) => (
            <Card key={m.id}>
              <CardContent className="p-4">
                <div className="flex items-start justify-between gap-2">
                  <div className="flex-1">
                    <p className="whitespace-pre-wrap text-sm">{m.content}</p>
                    <div className="mt-2 flex items-center gap-3 text-xs text-muted-foreground">
                      <span>{formatDateTime(m.created_at)}</span>
                      {m.related_symbols && (
                        <span className="rounded bg-muted px-1.5 py-0.5">
                          关联: {m.related_symbols}
                        </span>
                      )}
                    </div>
                  </div>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="shrink-0 text-muted-foreground hover:text-destructive"
                    onClick={() => handleDelete(m.id)}
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))
        )}
      </div>
    </div>
  );
}
