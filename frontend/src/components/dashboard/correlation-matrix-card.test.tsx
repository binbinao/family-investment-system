import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { CorrelationMatrixCard } from "./correlation-matrix-card";

// Mock the API module
const mockCorrelationMatrix = vi.fn().mockResolvedValue(null);
vi.mock("@/lib/api", () => ({
  api: {
    dashboard: {
      correlationMatrix: () => mockCorrelationMatrix(),
    },
  },
}));

describe("CorrelationMatrixCard", () => {
  it("renders the card title", () => {
    render(<CorrelationMatrixCard />);
    expect(screen.getByText("持仓相关性")).toBeInTheDocument();
  });

  it("shows insufficient data message when API returns null", async () => {
    render(<CorrelationMatrixCard />);
    const msg = await screen.findByText(
      "数据不足，至少需要 5 个交易日的快照数据",
    );
    expect(msg).toBeInTheDocument();
  });
});
