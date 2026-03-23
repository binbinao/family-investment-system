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
