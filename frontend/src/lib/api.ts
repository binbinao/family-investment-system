import type {
  User,
  Holding,
  HoldingCreate,
  HoldingUpdate,
  Transaction,
  TransactionCreate,
  DashboardSummary,
  AllocationItem,
  LoginRequest,
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
};

export { ApiError };
