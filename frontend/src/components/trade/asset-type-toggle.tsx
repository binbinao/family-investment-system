"use client";

import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { cn } from "@/lib/utils";
import type { AssetType } from "@/types";

export const ASSET_TYPES: AssetType[] = [
  "股票",
  "基金",
  "债券",
  "现金",
  "其他",
];

type AssetTypeToggleProps = {
  value: AssetType;
  onChange: (next: AssetType) => void;
  id?: string;
  className?: string;
};

export function AssetTypeToggle({
  value,
  onChange,
  id = "asset-type",
  className,
}: AssetTypeToggleProps) {
  return (
    <div className={cn("space-y-2", className)}>
      <Label id={`${id}-label`} className="text-sm font-medium">
        资产类型
      </Label>
      <div
        role="radiogroup"
        aria-labelledby={`${id}-label`}
        className="flex flex-wrap gap-2"
      >
        {ASSET_TYPES.map((t) => {
          const selected = value === t;
          return (
            <Button
              key={t}
              type="button"
              role="radio"
              aria-checked={selected}
              variant={selected ? "default" : "outline"}
              size="sm"
              className="min-w-[4.25rem] px-3"
              onClick={() => onChange(t)}
            >
              {t}
            </Button>
          );
        })}
      </div>
    </div>
  );
}
