import type { AssetType, TransactionType } from "@/types";

/** 添加持仓：按资产类型的文案与是否展示成本/现价（现金固定按「元」记账：数量=余额，成本与计价均为 1） */
export type HoldingFormCopy = {
  symbolLabel: string;
  symbolPlaceholder: string;
  nameLabel: string;
  namePlaceholder: string;
  quantityLabel: string;
  quantityPlaceholder: string;
  costPriceLabel: string;
  costPlaceholder: string;
  latestPriceLabel: string;
  latestPlaceholder: string;
  showCostAndLatest: boolean;
  /** true：提交时 cost_price=1、latest_price=1（市值=余额） */
  isCashSemantics: boolean;
};

/** 记账页：选中类型后，扩展区顶部的一句说明 */
export function holdingPanelDescription(assetType: AssetType): string {
  switch (assetType) {
    case "股票":
      return "维护代码、名称、持股数量与每股成本；现价选填，便于总市值与盈亏。";
    case "基金":
      return "维护基金代码、名称、持有份额与成本净值；最新净值选填。";
    case "债券":
      return "维护债券代码、简称、持仓张数与成本净价；估值净价选填。";
    case "现金":
      return "现金按「元」入账：余额写入下方「数量」；系统内部以单价 1 元存储。";
    case "其他":
    default:
      return "自定义代码与名称，按你的习惯填写数量、单位成本与估价。";
  }
}

export function holdingFormCopy(assetType: AssetType): HoldingFormCopy {
  switch (assetType) {
    case "股票":
      return {
        symbolLabel: "标的代码",
        symbolPlaceholder: "如 600519、AAPL",
        nameLabel: "标的名称",
        namePlaceholder: "如 贵州茅台",
        quantityLabel: "持股数量（股）",
        quantityPlaceholder: "股数",
        costPriceLabel: "成本价（元/股）",
        costPlaceholder: "每股成本",
        latestPriceLabel: "现价（元/股，可选）",
        latestPlaceholder: "最新市价",
        showCostAndLatest: true,
        isCashSemantics: false,
      };
    case "基金":
      return {
        symbolLabel: "基金代码",
        symbolPlaceholder: "如 161725、000001",
        nameLabel: "基金名称",
        namePlaceholder: "如 招商中证白酒",
        quantityLabel: "持有份额",
        quantityPlaceholder: "份",
        costPriceLabel: "成本净值（元/份）",
        costPlaceholder: "建仓/申购对应的单位净值",
        latestPriceLabel: "最新净值（元/份，可选）",
        latestPlaceholder: "当前单位净值",
        showCostAndLatest: true,
        isCashSemantics: false,
      };
    case "债券":
      return {
        symbolLabel: "债券代码",
        symbolPlaceholder: "如 019666、127018",
        nameLabel: "债券简称",
        namePlaceholder: "如 23 国债 01",
        quantityLabel: "持仓张数",
        quantityPlaceholder: "张（常见 1 张对应面值 100 元，以券商为准）",
        costPriceLabel: "成本净价（元）",
        costPlaceholder: "建仓时每张净价（或按你习惯的百元报价换算）",
        latestPriceLabel: "估值净价（元，可选）",
        latestPlaceholder: "当前净价或估价",
        showCostAndLatest: true,
        isCashSemantics: false,
      };
    case "现金":
      return {
        symbolLabel: "标识代码",
        symbolPlaceholder: "如 CNY、活期-工行",
        nameLabel: "名称",
        namePlaceholder: "如 活期存款、货币基金",
        quantityLabel: "余额（元）",
        quantityPlaceholder: "当前账面余额",
        costPriceLabel: "",
        costPlaceholder: "",
        latestPriceLabel: "",
        latestPlaceholder: "",
        showCostAndLatest: false,
        isCashSemantics: true,
      };
    case "其他":
    default:
      return {
        symbolLabel: "代码/编号",
        symbolPlaceholder: "自定义唯一标识",
        nameLabel: "资产名称",
        namePlaceholder: "名称",
        quantityLabel: "数量",
        quantityPlaceholder: "持仓数量",
        costPriceLabel: "单位成本",
        costPlaceholder: "每单位成本",
        latestPriceLabel: "最新单价（可选）",
        latestPlaceholder: "估价单价",
        showCostAndLatest: true,
        isCashSemantics: false,
      };
  }
}

export function transactionTypesForAsset(assetType: AssetType): TransactionType[] {
  if (assetType === "现金") {
    return ["买入", "卖出"];
  }
  return ["买入", "卖出", "现金分红", "红利再投资"];
}

export type TransactionFormCopy = {
  quantityLabel: string;
  priceLabel: string;
  quantityPlaceholder: string;
  pricePlaceholder: string;
  /** 仅展示一个金额框，提交时 quantity=1、price=金额 */
  singleDividendAmount: boolean;
  /** 买入/卖出时成交价固定为 1，只让用户填金额（数量） */
  hidePriceUseOne: boolean;
  hint?: string;
};

export function transactionFormCopy(
  assetType: AssetType,
  txType: TransactionType
): TransactionFormCopy {
  if (txType === "现金分红") {
    return {
      quantityLabel: "数量",
      priceLabel: "分红金额（元）",
      quantityPlaceholder: "1",
      pricePlaceholder: "本次到账分红总额",
      singleDividendAmount: true,
      hidePriceUseOne: false,
      hint: "系统按「数量×价格」记录分红；此处只需填写总额，将自动按 1×总额 提交。",
    };
  }

  if (assetType === "现金") {
    const isBuy = txType === "买入";
    return {
      quantityLabel: isBuy ? "存入金额（元）" : "取出金额（元）",
      priceLabel: "单价",
      quantityPlaceholder: "金额",
      pricePlaceholder: "1",
      singleDividendAmount: false,
      hidePriceUseOne: true,
      hint: "现金按「元」记账：内部以单价 1、数量=金额 存储，与总资产汇总一致。",
    };
  }

  switch (assetType) {
    case "基金":
      if (txType === "红利再投资") {
        return {
          quantityLabel: "再投资份额",
          priceLabel: "确认净值（元/份）",
          quantityPlaceholder: "新增份额",
          pricePlaceholder: "确认日净值",
          singleDividendAmount: false,
          hidePriceUseOne: false,
        };
      }
      return {
        quantityLabel: "份额",
        priceLabel: "净值（元/份）",
        quantityPlaceholder: "份",
        pricePlaceholder: "成交净值",
        singleDividendAmount: false,
        hidePriceUseOne: false,
      };
    case "债券":
      return {
        quantityLabel: "张数",
        priceLabel: "净价（元）",
        quantityPlaceholder: "张",
        pricePlaceholder: "成交净价",
        singleDividendAmount: false,
        hidePriceUseOne: false,
      };
    case "股票":
      if (txType === "红利再投资") {
        return {
          quantityLabel: "再投资股数",
          priceLabel: "折算价（元/股）",
          quantityPlaceholder: "股",
          pricePlaceholder: "再投资价格",
          singleDividendAmount: false,
          hidePriceUseOne: false,
        };
      }
      return {
        quantityLabel: "股数",
        priceLabel: "成交价（元/股）",
        quantityPlaceholder: "股",
        pricePlaceholder: "每股成交价",
        singleDividendAmount: false,
        hidePriceUseOne: false,
      };
    case "其他":
    default:
      return {
        quantityLabel: "数量",
        priceLabel: "单价",
        quantityPlaceholder: "",
        pricePlaceholder: "",
        singleDividendAmount: false,
        hidePriceUseOne: false,
      };
  }
}
