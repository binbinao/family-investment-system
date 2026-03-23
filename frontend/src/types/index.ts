export interface User {
  id: string;
  username: string;
  display_name: string | null;
}

export interface Holding {
  id: string;
  symbol: string;
  name: string;
  asset_type: AssetType;
  quantity: number;
  cost_price: number;
  latest_price: number | null;
  latest_price_updated_at: string | null;
  account: string | null;
  market_value: number | null;
  profit_loss: number | null;
  profit_loss_pct: number | null;
  created_at: string;
  updated_at: string;
}

export type AssetType = "股票" | "基金" | "债券" | "现金" | "其他";

export type TransactionType = "买入" | "卖出" | "现金分红" | "红利再投资";

export interface Transaction {
  id: string;
  holding_id: string;
  symbol: string;
  type: TransactionType;
  quantity: number;
  price: number;
  fee: number;
  realized_pnl: number | null;
  date: string;
  user_id: string;
  created_at: string;
}

export interface DashboardSummary {
  total_market_value: number;
  total_cost: number;
  total_profit_loss: number;
  total_profit_loss_pct: number;
  holdings_count: number;
}

export interface AllocationItem {
  asset_type: string;
  market_value: number;
  percentage: number;
}

export interface HoldingCreate {
  symbol: string;
  name: string;
  asset_type: AssetType;
  quantity: number;
  cost_price: number;
  latest_price?: number;
  account?: string;
}

export interface HoldingUpdate {
  name?: string;
  quantity?: number;
  cost_price?: number;
  account?: string;
}

export interface TransactionCreate {
  holding_id: string;
  type: TransactionType;
  quantity: number;
  price: number;
  fee?: number;
  date: string;
}

export interface LoginRequest {
  username: string;
  password: string;
}

export interface SnapshotPoint {
  date: string;
  total_market_value: number;
  total_cost: number;
  total_profit_loss: number;
}

export interface AllocationTarget {
  asset_type: string;
  target_ratio: number;
}

export interface DeviationItem {
  asset_type: string;
  target_pct: number;
  actual_pct: number;
  deviation: number;
  is_alert: boolean;
  adjust_direction: string;
  adjust_amount: number;
}

export interface DeviationResult {
  has_targets: boolean;
  has_alert?: boolean;
  deviations: DeviationItem[];
}

export interface MarketStatus {
  symbol: string;
  name: string;
  latest_price: number;
  price_change: number | null;
  price_change_pct: number | null;
  updated_at: string;
  source: string;
  fail_count: number;
  is_stale: boolean;
}

export interface ImportResult {
  success: { row: number; symbol: string; name?: string; type?: string }[];
  errors: { row: number; error: string }[];
}

export interface AIConversation {
  id: string;
  mode: "quick" | "deep";
  question: string;
  answer: string | null;
  created_at: string;
}

export interface ChatMessage {
  role: "user" | "assistant" | "system";
  content: string;
  mode?: "quick" | "deep";
  progress?: string;
  isStreaming?: boolean;
}
