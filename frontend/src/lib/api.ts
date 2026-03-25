import type {
  User,
  Holding,
  HoldingCreate,
  HoldingUpdate,
  Transaction,
  TransactionCreate,
  DashboardSummary,
  AllocationItem,
  AllocationTarget,
  AIConversation,
  DailyReportItem,
  DeviationResult,
  ImportResult,
  LoginRequest,
  MarketStatus,
  MemoItem,
  OperationLogItem,
  SnapshotPoint,
} from "@/types";

const API_BASE =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    ...options,
  });

  if (!res.ok) {
    const text = await res.text();
    throw new ApiError(res.status, text);
  }

  return res.json();
}

export const api = {
  auth: {
    login: (data: LoginRequest) =>
      request<User>("/auth/login", {
        method: "POST",
        body: JSON.stringify(data),
      }),
    logout: () =>
      request<void>("/auth/logout", { method: "POST" }),
    me: () => request<User>("/auth/me"),
  },

  holdings: {
    list: () => request<Holding[]>("/holdings"),
    create: (data: HoldingCreate) =>
      request<Holding>("/holdings", {
        method: "POST",
        body: JSON.stringify(data),
      }),
    update: (id: string, data: HoldingUpdate) =>
      request<Holding>(`/holdings/${id}`, {
        method: "PUT",
        body: JSON.stringify(data),
      }),
    delete: (id: string) =>
      request<void>(`/holdings/${id}`, { method: "DELETE" }),
    updatePrice: (id: string, latest_price: number) =>
      request<Holding>(`/holdings/${id}/price`, {
        method: "PATCH",
        body: JSON.stringify({ latest_price }),
      }),
  },

  transactions: {
    list: (holdingId?: string) => {
      const params = holdingId ? `?holding_id=${holdingId}` : "";
      return request<Transaction[]>(`/transactions${params}`);
    },
    create: (data: TransactionCreate) =>
      request<Transaction>("/transactions", {
        method: "POST",
        body: JSON.stringify(data),
      }),
  },

  dashboard: {
    summary: () => request<DashboardSummary>("/dashboard/summary"),
    allocation: () => request<AllocationItem[]>("/dashboard/allocation"),
  },

  market: {
    refresh: () =>
      request<{ total: number; success: number; failed: number; skipped: number }>(
        "/market/refresh",
        { method: "POST" },
      ),
    status: () => request<MarketStatus[]>("/market/status"),
  },

  snapshots: {
    list: (startDate?: string, endDate?: string) => {
      const params = new URLSearchParams();
      if (startDate) params.set("start_date", startDate);
      if (endDate) params.set("end_date", endDate);
      const qs = params.toString();
      return request<SnapshotPoint[]>(`/snapshots${qs ? `?${qs}` : ""}`);
    },
  },

  allocation: {
    targets: () => request<AllocationTarget[]>("/allocation/targets"),
    setTargets: (targets: AllocationTarget[]) =>
      request<AllocationTarget[]>("/allocation/targets", {
        method: "PUT",
        body: JSON.stringify({ targets }),
      }),
    deviation: () => request<DeviationResult>("/allocation/deviation"),
  },

  ai: {
    history: (limit = 50) =>
      request<AIConversation[]>(`/ai/history?limit=${limit}`),
    chatUrl: `${API_BASE}/ai/chat`,
  },

  import: {
    holdings: (file: File) => {
      const formData = new FormData();
      formData.append("file", file);
      return fetch(`${API_BASE}/import/holdings`, {
        method: "POST",
        credentials: "include",
        body: formData,
      }).then(async (res) => {
        if (!res.ok) throw new ApiError(res.status, await res.text());
        return res.json() as Promise<ImportResult>;
      });
    },
    transactions: (file: File) => {
      const formData = new FormData();
      formData.append("file", file);
      return fetch(`${API_BASE}/import/transactions`, {
        method: "POST",
        credentials: "include",
        body: formData,
      }).then(async (res) => {
        if (!res.ok) throw new ApiError(res.status, await res.text());
        return res.json() as Promise<ImportResult>;
      });
    },
    templateUrl: (type: "holdings" | "transactions") =>
      `${API_BASE}/import/template/${type}`,
  },

  reports: {
    latest: () => request<DailyReportItem>("/reports/latest"),
    list: (limit = 30) =>
      request<DailyReportItem[]>(`/reports?limit=${limit}`),
    generate: () =>
      request<{ success: boolean; date?: string; summary?: string; message?: string }>(
        "/reports/generate",
        { method: "POST" },
      ),
  },

  memos: {
    list: (symbol?: string, limit = 50) => {
      const params = new URLSearchParams();
      if (symbol) params.set("symbol", symbol);
      params.set("limit", String(limit));
      return request<MemoItem[]>(`/memos?${params}`);
    },
    create: (content: string) =>
      request<MemoItem>("/memos", {
        method: "POST",
        body: JSON.stringify({ content }),
      }),
    delete: (id: string) =>
      request<void>(`/memos/${id}`, { method: "DELETE" }),
  },

  logs: {
    list: (limit = 100) =>
      request<OperationLogItem[]>(`/logs?limit=${limit}`),
  },

  settings: {
    get: () => request<Record<string, string>>("/settings"),
    update: (settings: { key: string; value: string }[]) =>
      request<{ success: boolean }>("/settings", {
        method: "PUT",
        body: JSON.stringify({ settings }),
      }),
  },
};

export { ApiError };
