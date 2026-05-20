import { render, screen } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { RiskMetricsCard } from "@/components/dashboard/risk-metrics-card";

// Mock the API module
vi.mock("@/lib/api", () => ({
  api: {
    dashboard: {
      riskMetrics: vi.fn(),
    },
  },
}));

import { api } from "@/lib/api";

const mockRiskMetrics = {
  max_drawdown: 12.5,
  annualized_volatility: 18.3,
  sharpe_ratio: 0.85,
  var_95: 2.1,
  period_days: 60,
};

describe("RiskMetricsCard", () => {
  it("renders risk metrics when data is available", async () => {
    vi.mocked(api.dashboard.riskMetrics).mockResolvedValue(mockRiskMetrics);

    render(<RiskMetricsCard />);

    // Wait for async data - values are rendered as separate elements
    // MetricCard renders: label, value, unit in separate spans
    const maxDD = await screen.findByText("-12.5");
    expect(maxDD).toBeInTheDocument();
    expect(screen.getByText("18.3")).toBeInTheDocument();
    expect(screen.getByText("0.85")).toBeInTheDocument();
    expect(screen.getByText("-2.10")).toBeInTheDocument();
  });

  it("shows insufficient data message when no metrics", async () => {
    vi.mocked(api.dashboard.riskMetrics).mockResolvedValue(null);

    render(<RiskMetricsCard />);

    const msg = await screen.findByText(/数据不足/);
    expect(msg).toBeInTheDocument();
  });
});
