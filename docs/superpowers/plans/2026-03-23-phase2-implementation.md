# Phase 2 实施计划 — "好用"

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 落实 Phase 2 设计：行情自动更新（AKShare + Redis + price_cache）、Excel 导入、每日快照与净值曲线、配置偏离提醒与目标配置页；并完成与设计文档一致的验收与自动化测试补全。

**Architecture:** 在 Phase 1 的 FastAPI + Next.js 骨架上扩展：`app/services/market.py` 拉取行情并写 Redis/`price_cache`；`APScheduler` 定时刷新与快照；`openpyxl` 处理导入；`snapshots` / `allocation_targets` 支撑曲线与偏离计算；首页与 `/allocation`、记账页 Tab 消费新 API。

**Tech Stack:** AKShare、APScheduler、openpyxl、python-multipart、Redis、SQLAlchemy/Alembic、Recharts（前端已用）

**Spec:** `docs/superpowers/specs/2026-03-23-phase2-design.md`

**现状说明（2026-04-06 代码审计）：** 路由与模型已存在（`market`、`import`、`snapshots`、`allocation`）、`scheduler.py` 已注册行情/快照任务、首页含 `NetValueChart`、`DeviationAlert`、`MarketStatusBar`、记账页含 Excel Tab、`/allocation` 页面已存在。本计划以 **验收设计完成标准**、**补测试**、**修正与设计不一致处** 为主，而非从零实现。

**执行前（Superpowers）：** 若使用 `executing-plans`，建议先按 **superpowers:using-git-worktrees** 在独立分支/worktree 上执行；完成后用 **superpowers:finishing-a-development-branch** 收尾。

---

## 文件结构总览（Phase 2 相关）

```
backend/app/
├── models/
│   ├── price_cache.py
│   ├── snapshot.py
│   └── allocation_target.py
├── services/
│   ├── market.py
│   ├── excel_import.py
│   ├── snapshot.py
│   └── allocation.py
├── api/v1/
│   ├── market.py
│   ├── imports.py
│   ├── snapshots.py
│   └── allocation.py
└── core/
    └── scheduler.py

frontend/src/
├── app/
│   ├── page.tsx                    # 净值曲线、偏离提醒、行情状态
│   ├── trade/page.tsx              # Excel 导入 Tab
│   └── allocation/page.tsx         # 目标配置
└── components/
    ├── dashboard/
    │   ├── net-value-chart.tsx
    │   ├── deviation-alert.tsx
    │   └── market-status-bar.tsx
    └── import/
        └── excel-import.tsx
```

---

### Task 1: 对照 Spec 做完成标准验收（手工 + API）

**Files:**
- 参考：`docs/superpowers/specs/2026-03-23-phase2-design.md` §1、§2、§4、§5

- [ ] **Step 1: 启动栈并登录**

确保 PostgreSQL/Redis 可用，`docker compose up` 或本地 `uvicorn` + `pnpm dev`。使用已有账号登录前端。

- [ ] **Step 2: 行情 API 与降级表现**

调用（需 Cookie 会话，或用浏览器 Network 复现）：

```bash
# 在已登录会话下（示例：从浏览器复制 Cookie）
curl -s -b "session=..." http://localhost:8000/api/v1/market/status | jq .
curl -s -X POST -b "session=..." http://localhost:8000/api/v1/market/refresh | jq .
```

确认：有最后更新时间；连续失败时有 `fail_count` 与设计描述一致；首页 `MarketStatusBar` 与 status 对齐。

- [ ] **Step 3: Excel 模板与导入**

浏览器打开：`GET /api/v1/import/template/holdings`、`/api/v1/import/template/transactions`（需与前端 `ExcelImport` 行为一致）。

上传合法/非法行，确认：成功行写入、错误行带原因（见 `excel_import` 返回结构）。

- [ ] **Step 4: 快照与净值曲线**

```bash
curl -s -b "session=..." "http://localhost:8000/api/v1/snapshots" | jq .
curl -s -b "session=..." "http://localhost:8000/api/v1/snapshots/chart" | jq .
```

首页 `NetValueChart` 能展示时间序列（含空数据时的空态）。

- [ ] **Step 5: 配置目标与偏离**

在 `/allocation` 设定目标比例，使某类资产实际占比与目标差 **> 10%**，确认首页黄色提醒与展开后的调仓建议。

```bash
curl -s -b "session=..." http://localhost:8000/api/v1/allocation/targets | jq .
curl -s -b "session=..." http://localhost:8000/api/v1/allocation/deviation | jq .
```

- [ ] **Step 6: Commit（仅文档/验收笔记时）**

若补充了 `docs/` 下验收记录：

```bash
git add docs/
git commit -m "docs: phase2 acceptance notes"
```

---

### Task 2: 定时任务与设计 §2.1 时段对齐

**Files:**
- Modify: `backend/app/core/scheduler.py`

- [ ] **Step 1: 核对 A 股交易时段**

设计：股票 9:30–11:30、13:00–15:00 每 5 分钟。当前 `CronTrigger(hour="9-11,13-14", minute="*/5")` 覆盖 9:00–11:59、13:00–14:59，**未覆盖 15:00 整点及 9:30 前是否应跳过**（按产品决定是否收紧）。

- [ ] **Step 2: 写失败测试或注释说明**

若改为 `hour=9 minute=30-55` 等组合，或增加 `hour=15 minute=0` 的 job，先记录期望行为再改代码。

- [ ] **Step 3: 运行后端测试**

```bash
cd backend && pytest tests/ -q --tb=short
```

Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add backend/app/core/scheduler.py
git commit -m "fix(scheduler): align stock quote cron with market hours"
```

---

### Task 3: 后端 API 自动化测试（allocation / snapshots）

**Files:**
- Create: `backend/tests/test_allocation.py`
- Create: `backend/tests/test_snapshots.py`

- [ ] **Step 1: 为偏离逻辑写 API 测试**

```python
# tests/test_allocation.py
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_deviation_alert_over_10_percent(authenticated_client: AsyncClient):
    await authenticated_client.put(
        "/api/v1/allocation/targets",
        json={"targets": [{"asset_type": "股票", "target_ratio": 50}]},
    )
    await authenticated_client.post(
        "/api/v1/holdings",
        json={
            "symbol": "600519",
            "name": "贵州茅台",
            "asset_type": "股票",
            "quantity": 100,
            "cost_price": 100,
            "latest_price": 100,
        },
    )
    r = await authenticated_client.get("/api/v1/allocation/deviation")
    assert r.status_code == 200
    data = r.json()
    assert data.get("has_targets") is True
    # 仅一类资产时实际占比 100%，目标 50% → 偏离超过 10%
    assert data.get("has_alert") is True
```

- [ ] **Step 2: 运行测试至通过**

```bash
cd backend && pytest tests/test_allocation.py -v
```

Expected: PASS

- [ ] **Step 3: 快照列表与日期筛选**

在 `test_snapshots.py` 中调用 `GET /api/v1/snapshots?start_date=...&end_date=...`，空库期望 200 与 `[]`（或与当前服务行为一致）。

```bash
pytest tests/test_snapshots.py -v
```

- [ ] **Step 4: Commit**

```bash
git add backend/tests/test_allocation.py backend/tests/test_snapshots.py
git commit -m "test: add allocation deviation and snapshots API tests"
```

---

### Task 4: 行情与导入服务单元测试（Mock 外部依赖）

**Files:**
- Create: `backend/tests/test_market_service.py`（或 `test_excel_import.py`）

- [ ] **Step 1: Mock AKShare/HTTP，断言 Redis 或 DB 写入路径**

对 `refresh_all_prices` 或缓存读取使用 `unittest.mock.patch`，避免真实网络。

- [ ] **Step 2: Excel 行校验**

构造内存中的 xlsx（可用 `openpyxl` 写 `BytesIO`），调用 `import_holdings` / `import_transactions`，断言部分成功、部分错误行带 `reason`。

- [ ] **Step 3: 运行**

```bash
cd backend && pytest tests/test_market_service.py tests/test_excel_import.py -v
```

- [ ] **Step 4: Commit**

```bash
git add backend/tests/
git commit -m "test: mock market and excel import flows"
```

---

### Task 5: 设计文档与实现不一致项清零（若有）

**Files:**
- Modify: `docs/superpowers/specs/2026-03-23-phase2-design.md` 或实现代码（二选一，以 Spec 已确认为准）

- [ ] **Step 1: 列出差异表**

例如：API 额外字段、`/snapshots/chart` 是否写入设计文档等。

- [ ] **Step 2: 小步修正 + 测试**

- [ ] **Step 3: Commit**

```bash
git commit -m "docs: align phase2 spec with implemented APIs"
```

---

### Task 6: 收尾（Superpowers）

- [ ] **Step 1: 全量测试**

```bash
cd backend && pytest -q
cd frontend && pnpm lint && pnpm build
```

- [ ] **Step 2: 使用 finishing-a-development-branch**

按 **superpowers:finishing-a-development-branch** 汇总变更、准备 PR/合并选项。

---

## Remember

- 设计已 **已确认**，除非验收发现硬伤，避免扩大 Scope（YAGNI）。
- 优先用测试锁定 §2.4 偏离 10%、§2.1 TTL/降级、§2.2 导入行级错误行为。
- 阻塞时停止执行，回传问题而非猜测（executing-plans）。
