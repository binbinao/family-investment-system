# 齐家 · 家庭投资助手 — 项目记忆

## 项目概况
- **定位**：三口之家投资记账本 + AI 分析助手
- **仓库**：`/Users/duobinji/Documents/GitHub/family-investment-system`
- **分支**：仅 `main`，单线开发
- **最新版本**：v1.1+（新增风险指标、行业分析、CI/CD）
- **状态**：4个Phase完成 + P0风险量化实现 + CI/CD流水线

## 技术栈
| 层 | 技术 | 版本 |
|----|------|------|
| 前端 | Next.js / React / TypeScript | 16.2.1 / 19.2.4 / 5 |
| UI | Tailwind CSS 4 + shadcn/ui | — |
| 后端 | FastAPI (Python 3.11+) | 0.115.0 |
| ORM | SQLAlchemy 2.0 + Alembic | 2.0.35 |
| 数据库 | PostgreSQL 16 | — |
| 缓存 | Redis 7 | — |
| AI | DeepSeek API | v3.1-terminus |
| 行情 | AKShare（开源爬虫） | — |
| 部署 | Docker Compose (5 services: nginx/frontend/backend/db/redis) | — |

## 架构要点
- 后端 async-first：FastAPI + asyncpg + SQLAlchemy async
- Redis 多角色：Session(7d TTL) + 行情缓存(5min/24h) + APScheduler
- AI 双模式：quick(单次SSE) / deep(4步串行SSE)
- 行情降级：3次失败→显示缓存价+警告，支持手动输入
- 单家庭设计：非多租户，Docker单机部署
- Nginx反向代理：/api→backend:8000, /→frontend:3000, SSE 300s超时

## 页面清单
| 页面 | 路径 | 核心功能 |
|------|------|----------|
| 首页总览 | `/` | 资产总览、净值曲线、配置偏离提醒 |
| 记账 | `/trade` | 添加持仓、记录交易、Excel批量导入 |
| AI对话 | `/ai` | 快问/深聊，SSE流式输出 |
| 晨报 | `/reports` | 每日AI晨报列表+详情 |
| 备忘录 | `/memos` | 家庭投资备忘，#代码关联标的 |
| 配置目标 | `/allocation` | 资产配置目标比例设定 |
| 历史记录 | `/history` | 交易历史查询 |
| 设置 | `/settings` | 推送通知配置 |

## 后端结构（72个py文件）
- `app/models/`：11个ORM模型（user, holding, transaction, price_cache, snapshot, allocation_target, ai_conversation, daily_report, memo, operation_log, setting）
- `app/services/`：~15个业务服务（ai, market, holding, transaction, dashboard, allocation, snapshot, daily_report, excel_import, auth, notification, memo等）
- `app/api/v1/`：13个路由器，40+端点
- `alembic/versions/`：4个迁移文件

## 前端结构
- `src/app/`：8个页面路由
- `src/components/`：dashboard/holdings/trade/transactions/import/ui/layout
- `src/lib/api.ts`：按功能组织的API客户端
- `src/types/index.ts`：17个TypeScript接口

## 开发阶段
- Phase 1 ✅ 功能：认证、持仓CRUD、交易记录、基础Dashboard
- Phase 2 ✅ 好用：行情自动更新、Excel导入、快照、配置目标
- Phase 3 ✅ 聪明：AI快问/深聊、对话历史、持仓上下文注入
- Phase 4 ✅ 完整：晨报、推送通知、备忘录、操作审计、移动适配

## 已知限制
- 仅Web端，无原生App
- 行情仅覆盖A股+公募基金（AKShare范围）
- 单实例，无多家庭支持
- 仅DeepSeek模型，无多模型切换
- SSE而非WebSocket

## 部署
- `docker compose up` 一键启动
- 端口通过 `NGINX_HOST_PORT` 控制（默认80，当前配置8888）
- 入口脚本自动执行：alembic迁移 → 初始化用户 → 启动uvicorn
- 备份脚本：`scripts/backup.sh`（PostgreSQL日备+30天清理）

## CI/CD
- `.github/workflows/ci.yml`：push/PR自动触发
- 6个job：Backend Lint → Backend Tests | Frontend Lint+TSC → Frontend Tests + Build | Docker Build
- 后端：ruff --exit-zero + pytest (PostgreSQL+Redis services)
- 前端：tsc --noEmit + eslint(非阻塞) + vitest + next build
- vitest 单元测试：4文件13用例（api-cache/error-boundary/risk-metrics/sector-allocation）
- 后端测试：test_dashboard_risk_sector.py（风险指标+行业分配）

## 已实现的Issue增强
- #13: Holding模型 sector/purchase_date/cost_method 字段
- #14: Snapshot模型 daily_return 字段（自动计算日收益率）
- #2: 风险指标计算（最大回撤/夏普/波动率/VaR）+ 前端RiskMetricsCard
- #4: 行业集中度分析 + 前端SectorAllocationCard（>30%预警）
- #12: ErrorBoundary + API缓存工具

## 待实现Issues
- #3 P0: 持仓相关性矩阵
- #1 P0: 税后最优再平衡
- #5 P1: 税务计算支持
- #6 P1: AI分析深度提升
- #7 P1: 高级可视化
- #8-#11 P2: 多模型AI/移动端/海外市场/自动交易
