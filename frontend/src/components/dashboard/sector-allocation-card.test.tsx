import { render, screen } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { SectorAllocationCard } from "@/components/dashboard/sector-allocation-card";

vi.mock("@/lib/api", () => ({
  api: {
    dashboard: {
      sectorAllocation: vi.fn(),
    },
  },
}));

import { api } from "@/lib/api";

const mockSectorData = [
  { sector: "食品饮料", market_value: 50000, percentage: 40.0, holdings_count: 3 },
  { sector: "银行", market_value: 30000, percentage: 24.0, holdings_count: 2 },
  { sector: "电子", market_value: 20000, percentage: 16.0, holdings_count: 1 },
  { sector: "未分类", market_value: 25000, percentage: 20.0, holdings_count: 2 },
];

describe("SectorAllocationCard", () => {
  it("renders sector allocation data", async () => {
    vi.mocked(api.dashboard.sectorAllocation).mockResolvedValue(mockSectorData);

    render(<SectorAllocationCard />);

    const title = await screen.findByText("行业分布");
    expect(title).toBeInTheDocument();
    expect(screen.getByText("食品饮料")).toBeInTheDocument();
    expect(screen.getByText("银行")).toBeInTheDocument();
  });

  it("shows concentration badge when > 30%", async () => {
    vi.mocked(api.dashboard.sectorAllocation).mockResolvedValue(mockSectorData);

    render(<SectorAllocationCard />);

    // 食品饮料 40% > 30% triggers "集中" badge
    const badge = await screen.findByText("集中");
    expect(badge).toBeInTheDocument();
  });

  it("hides badge when no sector exceeds 30%", async () => {
    const safeData = [
      { sector: "银行", market_value: 20000, percentage: 25.0, holdings_count: 1 },
      { sector: "电子", market_value: 20000, percentage: 25.0, holdings_count: 1 },
      { sector: "食品饮料", market_value: 20000, percentage: 25.0, holdings_count: 1 },
      { sector: "医药生物", market_value: 20000, percentage: 25.0, holdings_count: 1 },
    ];
    vi.mocked(api.dashboard.sectorAllocation).mockResolvedValue(safeData);

    render(<SectorAllocationCard />);

    const title = await screen.findByText("行业分布");
    expect(title).toBeInTheDocument();
    expect(screen.queryByText("集中")).not.toBeInTheDocument();
  });
});
