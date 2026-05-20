import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { RebalanceCard } from "./rebalance-card";

// Mock the API module
const mockDeviation = vi.fn().mockResolvedValue({ has_targets: false, deviations: [] });
const mockRebalance = vi.fn().mockResolvedValue({
  has_targets: false,
  deviation_threshold: 10,
  suggestions: [],
  total_cost: 0,
  total_net_benefit: 0,
});
vi.mock("@/lib/api", () => ({
  api: {
    allocation: {
      deviation: () => mockDeviation(),
    },
    dashboard: {
      rebalance: () => mockRebalance(),
    },
  },
}));

describe("RebalanceCard", () => {
  it("renders the card title", () => {
    render(<RebalanceCard />);
    expect(screen.getByText("智能再平衡")).toBeInTheDocument();
  });

  it("shows prompt to set targets when no targets", async () => {
    render(<RebalanceCard />);
    const msg = await screen.findByText("请先设置资产配置目标");
    expect(msg).toBeInTheDocument();
  });
});
