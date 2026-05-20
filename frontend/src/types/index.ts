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
  sector: string | null;
  quantity: number;
  cost_price: number;
  latest_price: number | null;
  latest_price_updated_at: string | null;
  purchase_date: string | null;
  cost_method: "fifo" | "average";
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
  sector?: string;
  quantity: number;
  cost_price: number;
  latest_price?: number;
  purchase_date?: string;
  cost_method?: "fifo" | "average";
  account?: string;
}

export interface HoldingUpdate {
  name?: string;
  quantity?: number;
  cost_price?: number;
  sector?: string;
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

/** GET /snapshots/chart：可能含 estimated 缺失日模拟点 */
export interface SnapshotChartPoint extends SnapshotPoint {
  estimated?: boolean;
  daily_return?: number | null;
}

export interface RiskMetrics {
  max_drawdown: number;       // 最大回撤 (%)
  annualized_volatility: number; // 年化波动率 (%)
  sharpe_ratio: number;        // 夏普比率
  var_95: number;              // VaR 95% (%)
  period_days: number;         // 计算周期(天)
}

export interface SectorAllocation {
  sector: string;
  market_value: number;
  percentage: number;
  holdings_count: number;
}

// ---------------------------------------------------------------------------
// Correlation Matrix (#3)
// ---------------------------------------------------------------------------

export interface CorrelationPair {
  symbol_a: string;
  name_a: string;
  symbol_b: string;
  name_b: string;
  correlation: number;
  is_alert: boolean;
}

export interface DiversificationScore {
  score: number;
  label: string;
  avg_correlation: number;
}

export interface RiskContribution {
  symbol: string;
  name: string;
  weight: number;
  risk_contribution: number;
}

export interface CorrelationMatrixData {
  symbols: string[];
  symbol_names: string[];
  matrix: number[][];
  pairs: CorrelationPair[];
  diversification_score: DiversificationScore;
  risk_contributions: RiskContribution[];
  period_days: number;
}

// ---------------------------------------------------------------------------
// Tax-Aware Rebalance (#1)
// ---------------------------------------------------------------------------

export interface TradeCostDetail {
  stamp_tax: number;
  commission: number;
  redemption_fee: number;
  dividend_tax: number;
  total_cost: number;
}

export interface RebalanceSuggestion {
  asset_type: string;
  action: string;
  adjust_amount: number;
  cost_detail: TradeCostDetail;
  net_benefit: number;
  is_recommended: boolean;
}

export interface RebalanceResult {
  has_targets: boolean;
  deviation_threshold: number;
  suggestions: RebalanceSuggestion[];
  total_cost: number;
  total_net_benefit: number;
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

export interface DailyReportItem {
  id?: string;
  date: string;
  summary: string;
  content_markdown: string;
  created_at?: string;
  has_report?: boolean;
}

export interface MemoItem {
  id: string;
  content: string;
  related_symbols: string | null;
  user_id: string;
  created_at: string;
}

export interface OperationLogItem {
  id: string;
  user_id: string;
  action: string;
  detail: string;
  created_at: string;
}
