"use client";

import { useCallback, useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";
import { toast } from "sonner";

const SETTING_GROUPS = [
  {
    title: "Server酱推送",
    desc: "配置后晨报自动推送到微信",
    fields: [
      { key: "serverchan_key", label: "Server酱 Key", placeholder: "SCT..." },
    ],
  },
  {
    title: "Bark 推送",
    desc: "配置后晨报推送到 Bark App",
    fields: [
      { key: "bark_url", label: "Bark 服务地址", placeholder: "https://api.day.app/your-key" },
    ],
  },
  {
    title: "邮件推送",
    desc: "配置后晨报完整版发送到邮箱",
    fields: [
      { key: "smtp_host", label: "SMTP 服务器", placeholder: "smtp.qq.com" },
      { key: "smtp_port", label: "SMTP 端口", placeholder: "465" },
      { key: "smtp_user", label: "发件邮箱", placeholder: "your@qq.com" },
      { key: "smtp_pass", label: "邮箱密码/授权码", placeholder: "授权码" },
      { key: "email_to", label: "收件邮箱", placeholder: "family@example.com" },
    ],
  },
];

export default function SettingsPage() {
  const [values, setValues] = useState<Record<string, string>>({});
  const [saving, setSaving] = useState(false);

  const fetchSettings = useCallback(async () => {
    try {
      const data = await api.settings.get();
      setValues(data);
    } catch {
      // ignore
    }
  }, []);

  useEffect(() => {
    fetchSettings();
  }, [fetchSettings]);

  const handleSave = async () => {
    setSaving(true);
    try {
      const items = Object.entries(values)
        .filter(([, v]) => v)
        .map(([key, value]) => ({ key, value }));
      await api.settings.update(items);
      toast.success("设置已保存");
    } catch {
      toast.error("保存失败");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">系统设置</h1>
        <p className="text-sm text-muted-foreground">
          配置推送通知和系统参数
        </p>
      </div>

      {SETTING_GROUPS.map((group) => (
        <Card key={group.title}>
          <CardHeader>
            <CardTitle className="text-base">{group.title}</CardTitle>
            <p className="text-sm text-muted-foreground">{group.desc}</p>
          </CardHeader>
          <CardContent className="space-y-3">
            {group.fields.map((field) => (
              <div key={field.key} className="flex items-center gap-3">
                <Label className="w-28 shrink-0 text-right text-sm">
                  {field.label}
                </Label>
                <Input
                  type={field.key.includes("pass") ? "password" : "text"}
                  placeholder={field.placeholder}
                  value={values[field.key] || ""}
                  onChange={(e) =>
                    setValues((prev) => ({
                      ...prev,
                      [field.key]: e.target.value,
                    }))
                  }
                />
              </div>
            ))}
          </CardContent>
        </Card>
      ))}

      <Button onClick={handleSave} disabled={saving}>
        {saving ? "保存中..." : "保存设置"}
      </Button>
    </div>
  );
}
