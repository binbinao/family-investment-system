# 齐家 · Phase 2 设计文档 — "好用"

**版本**：v1.0
**日期**：2026-03-23
**状态**：已确认

---

## 1. 目标

行情自动更新，能看到资产走势，能批量导入历史数据，偏离目标配置时有提醒。

**完成标准**：持仓价格通过 AKShare 自动更新（股票每 5 分钟、基金每日 20:00），Excel 批量导入持仓和交易，首页显示净值曲线和配置偏离提醒。

---

## 2. 功能范围

### 2.1 行情自动更新

- AKShare 获取 A 股实时行情和基金净值
- Redis 缓存：股票 TTL 5min，基金 TTL 24h
- price_cache 表持久化备份
- 降级策略：失败时展示上次有效价格 + 标注更新时间；连续 3 次失败首页黄色提示；可手动输入兜底
- 定时任务（APScheduler）：
  - 股票行情：交易时段（9:30-11:30, 13:00-15:00）每 5 分钟
  - 基金净值：每日 20:00
  - 持仓快照：每日 15:30（收盘后）

### 2.2 Excel 导入

- 两种模板：持仓导入 + 交易导入
- 逐行校验，成功行导入，错误行返回原因
- 提供模板下载
- 后端：python-multipart + openpyxl 处理 Excel

### 2.3 每日持仓快照

- snapshots 表存储每日快照
- 每日收盘后自动生成
- 首页净值曲线（Recharts LineChart）
- API 返回时间序列数据

### 2.4 配置偏离提醒

- allocation_targets 表存储目标比例
- 设定/修改资产配置目标
- 实际占比偏离目标超 10% 时首页显示黄色提醒
- 点击提醒显示调仓建议

---

## 3. 新增数据库表

### price_cache

| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID (PK) | |
| symbol | VARCHAR(20) UNIQUE | 标的代码 |
| name | VARCHAR(100) | 标的名称 |
| latest_price | DECIMAL(18,4) | 最新价格 |
| price_change | DECIMAL(18,4) | 涨跌额 |
| price_change_pct | DECIMAL(10,4) | 涨跌幅 |
| updated_at | TIMESTAMP | 行情更新时间 |
| source | VARCHAR(20) | 数据来源（akshare/manual） |
| fail_count | INTEGER | 连续失败次数 |

### snapshots

| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID (PK) | |
| date | DATE UNIQUE | 快照日期 |
| total_market_value | DECIMAL(18,4) | 总市值 |
| total_cost | DECIMAL(18,4) | 总成本 |
| total_profit_loss | DECIMAL(18,4) | 总盈亏 |
| holdings_json | TEXT | 当日全部持仓 JSON |
| created_at | TIMESTAMP | |

### allocation_targets

| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID (PK) | |
| asset_type | VARCHAR(20) UNIQUE | 资产类型 |
| target_ratio | DECIMAL(5,2) | 目标比例（百分比） |
| updated_at | TIMESTAMP | |

---

## 4. 新增 API

### 行情

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /api/v1/market/refresh | 手动触发行情刷新 |
| GET | /api/v1/market/status | 行情更新状态（最后更新时间、失败计数） |

### Excel 导入

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/v1/import/template/{type} | 下载 Excel 模板（holdings/transactions） |
| POST | /api/v1/import/holdings | 导入持仓 Excel |
| POST | /api/v1/import/transactions | 导入交易 Excel |

### 快照

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/v1/snapshots | 历史快照列表（支持日期范围） |

### 配置目标

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/v1/allocation/targets | 获取目标配置 |
| PUT | /api/v1/allocation/targets | 更新目标配置 |
| GET | /api/v1/allocation/deviation | 获取偏离情况 |

---

## 5. 新增前端页面/组件

| 页面/组件 | 说明 |
|-----------|------|
| 净值曲线（首页） | Recharts LineChart，展示总市值走势 |
| 配置偏离提醒（首页） | 黄色 Alert，显示偏离情况 + 调仓建议 |
| 行情状态指示（首页） | 行情更新时间 + 异常提示 |
| Excel 导入（记账页） | 新增 Tab：上传 Excel + 结果反馈 |
| 配置目标页 | /allocation — 设定和修改目标比例 |

---

## 6. 新增依赖

### 后端
- akshare — A 股行情和基金净值
- apscheduler — 定时任务
- openpyxl — Excel 读写
- python-multipart — 文件上传

### 前端
- 无新增（Recharts 已安装）
