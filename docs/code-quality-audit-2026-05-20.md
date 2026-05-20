# 齐家项目 · 代码质量审计与提升方案

> 审计日期：2026-05-20 | 审计范围：前后端全量代码 | 发现问题：25 项

---

## 一、审计总结

### 评分卡

| 维度 | 评分 | 说明 |
|------|------|------|
| 编码规范 | A- | SQLAlchemy 2.0 Mapped 风格统一，Pydantic v2 严格校验，async-first 架构 |
| 架构设计 | B+ | 清晰的 routes/services/models/schemas 分层，但 Service 层偶有层违规 |
| 类型安全 | B | strict 模式已开，但有 unsafe cast 和类型不准确 |
| 安全 | C | Holding 无 user_id 隔离，Cookie 缺 secure flag，无登录限流 |
| 性能 | C+ | Dashboard 三次全表扫描，market 服务 N+1，同步 requests |
| 测试 | D | 仅 4 个前端测试 + 12 个后端测试，market/ai 服务零覆盖 |
| 可访问性 | D+ | 无 aria-label，无键盘导航，无焦点管理，无 aria-live |

### 问题分布

| 优先级 | 数量 | 关键问题 |
|--------|------|----------|
| Critical | 3 | 数据隔离缺失、.env 泄露、Dashboard 无用户过滤 |
| High | 6 | Cookie 安全、无登录限流、N+1 查询、同步 HTTP、deprecated API、三重全表扫描 |
| Medium | 9 | Service 层违规、缺索引、缺连接池配置、事务类型静默失败、输入校验不足 |
| Low | 7 | 缺 docstring、缺 `__repr__`、logger 格式不一致、测试模式过时 |

---

## 二、Critical 问题详情

### C1. Holding 模型缺 user_id — 数据隔离完全失效

**文件**: `backend/app/models/holding.py`
**现象**: `Holding` 模型没有 `user_id` 外键，`list_holdings()` 返回全部持仓
**影响**: 任何认证用户可以查看/修改/删除其他用户的持仓数据
**修复**:
```python
# 1. 模型加字段
class Holding(Base):
    user_id = mapped_column(UUID, ForeignKey("users.id"), nullable=False)
    
# 2. 所有查询加过滤
async def list_holdings(db: AsyncSession, user_id: UUID):
    result = await db.execute(select(Holding).where(Holding.user_id == user_id))
```
**需同步修改**: `dashboard.py`, `transaction.py`, `ai.py`, `snapshot.py`, `daily_report.py`, `allocation.py` 中所有 `select(Holding)` 查询

### C2. .env 文件提交到仓库

**文件**: `backend/.env`
**现象**: 含数据库凭据和 SECRET_KEY 的 .env 文件已提交到 Git
**修复**:
1. `echo "backend/.env" >> .gitignore`
2. `git rm --cached backend/.env`
3. 创建 `backend/.env.example` 含占位符值
4. 轮换所有已泄露的密钥

### C3. Dashboard 查询无用户过滤

**文件**: `backend/app/services/dashboard.py` (lines 21, 52, 96, 150)
**现象**: `get_summary()`, `get_allocation()`, `get_sector_allocation()` 全部加载所有持仓
**修复**: 所有查询加 `where(Holding.user_id == user_id)` 过滤（与 C1 联动）

---

## 三、High 问题详情

### H1. Cookie 缺 secure=True

**文件**: `backend/app/api/v1/auth.py` line 31
**修复**: `response.set_cookie(..., secure=True, samesite="lax")`
**注意**: 需配合 HTTPS 部署；开发环境可通过配置开关

### H2. 无登录限流

**修复方案**: 
```python
# 方案 A：简单内存计数
from collections import defaultdict
from time import time
_login_attempts = defaultdict(list)

# 方案 B：Redis 滑动窗口（推荐，已有 Redis）
async def check_login_rate(redis: Redis, ip: str):
    key = f"login_attempts:{ip}"
    count = await redis.incr(key)
    if count == 1:
        await redis.expire(key, 300)  # 5分钟窗口
    if count > 5:
        raise HTTPException(429, "登录尝试过于频繁，请5分钟后再试")
```

### H3. Dashboard 三次全表扫描

**文件**: `backend/app/services/dashboard.py`
**现象**: `get_summary()`, `get_allocation()`, `get_sector_allocation()` 各独立执行 `select(Holding)`
**修复**: 合并为单一 `get_dashboard_data()` 方法，一次查询后分别聚合

### H4. Market 服务 N+1 串行查询

**文件**: `backend/app/services/market.py` lines 800-810
**现象**: `refresh_all_prices` 逐个串行刷新，每次独立查 PriceCache
**修复**: 批量查询 PriceCache + 并发更新

### H5. 同步 requests 阻塞事件循环

**文件**: `backend/app/services/market.py`
**现象**: 800+ 行代码全部使用 `requests.get()`，仅在 `update_holding_price` 用 `asyncio.to_thread()`
**修复**: 替换为 `httpx.AsyncClient`，原生 async HTTP

### H6. datetime.utcnow 已弃用

**文件**: `backend/app/models/user.py` line 21, `transaction.py` line 32, `holding.py` lines 44, 47-48
**修复**: `default=datetime.utcnow` → `default=lambda: datetime.now(timezone.utc)`

---

## 四、Medium 问题详情

| # | 问题 | 文件 | 修复方案 |
|---|------|------|----------|
| M1 | Service 层抛 HTTPException | `services/transaction.py:33-36` | 定义领域异常 `class HoldingNotFoundError(Exception)` |
| M2 | 事务类型无 else 分支 | `services/transaction.py:40-65` | 加 `else: raise ValueError(f"未知交易类型: {data.type}")` |
| M3 | 无 holding_id 归属校验 | `services/transaction.py:25-29` | 创建交易前校验 `holding.user_id == current_user.id` |
| M4 | 无 relationship() 定义 | `app/models/` | 加 `relationship()` + cascade 配置 |
| M5 | 缺数据库索引 | `alembic/versions/` | 新迁移加索引：holding_id, user_id, date, symbol |
| M6 | 无连接池配置 | `app/core/database.py:8` | 加 `pool_size=10, max_overflow=20, pool_recycle=3600` |
| M7 | 登录字段无 max_length | `app/schemas/auth.py:7-8` | `username: str = Field(max_length=50)` |
| M8 | pytest-asyncio 过时模式 | `tests/conftest.py:24-27` | 移除 `event_loop` fixture，用 `loop_scope="session"` |
| M9 | 测试 drop/create 替代事务回滚 | `tests/conftest.py:40-46` | 改用 session 级事务 + rollback 模式 |

---

## 五、前端问题汇总

| 优先级 | 问题 | 文件 | 修复方案 |
|--------|------|------|----------|
| High | AI 页 387 行单体组件 | `src/app/ai/page.tsx` | 拆分 `useChatStream` hook + `ChatMessageList` 组件 |
| High | 9 个 useState 管理表单 | `src/components/holdings/add-holding-form.tsx` | 引入 `react-hook-form` |
| Medium | api-cache.ts 写而不用 | `src/lib/api-cache.ts` | 集成到 API 层或删除 |
| Medium | 请求无超时 | `src/lib/api.ts` | 加 `AbortController` + 10s 默认超时 |
| Medium | 暗色模式硬编码颜色 | `net-value-chart.tsx`, `deviation-alert.tsx` | 用 CSS 变量替换 hex |
| Medium | Zod 运行时校验缺失 | `src/types/index.ts` | 加 Zod schema 校验 API 响应 |
| Low | 无虚拟列表 | `src/app/ai/page.tsx:306` | 长对话用 `react-virtuoso` |
| Low | recharts/react-markdown 无懒加载 | — | 用 `next/dynamic` 按需加载 |
| D+ | 无障碍严重缺失 | 多处 | 见下方专项方案 |

### 可访问性专项

| 缺陷 | 位置 | 修复 |
|------|------|------|
| 图标按钮无 aria-label | AI 页发送/取消按钮, Header 汉堡按钮 | 加 `aria-label="发送消息"` 等 |
| DeviationAlert 无键盘交互 | `deviation-alert.tsx:29` | 加 `role="button"`, `tabIndex={0}`, `onKeyDown` |
| AI 消息无 aria-live | `ai/page.tsx:306` | 包裹 `<div aria-live="polite">` |
| 对话框关闭无焦点返回 | 所有 Dialog | 加 `onCloseAutoFocus` 返回触发元素 |

---

## 六、四阶段提升路线图

### Phase 1 · 安全止血（1周）

**目标**: 消除所有 Critical + High 安全问题

| 任务 | 预估 | 负责人 |
|------|------|--------|
| Holding 加 user_id + 数据隔离 | 1天 | 后端 |
| .env 移出版本控制 + 密钥轮换 | 0.5天 | DevOps |
| Cookie secure flag + CSRF Token | 0.5天 | 后端 |
| 登录限流（Redis 滑动窗口） | 1天 | 后端 |
| SECRET_KEY 启动校验 | 0.5天 | 后端 |
| holding_id 归属校验 | 0.5天 | 后端 |

**交付物**: 
- 所有 API 端点强制用户数据隔离
- Git 历史无泄露密钥
- 登录接口限流保护

### Phase 2 · 性能攻坚（1周）

**目标**: Dashboard 响应 <200ms，消除 N+1

| 任务 | 预估 | 负责人 |
|------|------|--------|
| Dashboard 三合一查询重构 | 1天 | 后端 |
| Market 批量刷新 + 并发 | 1.5天 | 后端 |
| requests → httpx 迁移 | 2天 | 后端 |
| 数据库索引迁移 | 0.5天 | 后端 |
| 连接池配置 | 0.5天 | 后端 |
| datetime.utcnow 清理 | 0.5天 | 后端 |

**交付物**:
- Dashboard API 延迟降至 <200ms
- 行情批量刷新吞吐量提升 5x+
- 连接池防止连接泄漏

### Phase 3 · 质量筑基（2周）

**目标**: 测试覆盖核心路径 >60%，规范落地

| 任务 | 预估 | 负责人 |
|------|------|--------|
| ruff + pre-commit 配置 | 0.5天 | 全栈 |
| GitHub Actions CI 流水线 | 1天 | DevOps |
| 后端 market 服务测试 | 2天 | 后端 |
| 后端 ai 服务测试 | 1.5天 | 后端 |
| 前端 login + form 测试 | 1.5天 | 前端 |
| Service 层领域异常重构 | 1天 | 后端 |
| API 请求超时 + 重试 | 1天 | 前端 |
| 测试基础设施升级（事务回滚模式） | 1天 | 后端 |

**交付物**:
- CI 流水线：lint → test → build
- 核心路径测试覆盖率 >60%
- 所有 Service 异常均为领域异常

### Phase 4 · 体验升级（2周）

**目标**: WCAG AA 可访问性，前端架构成熟

| 任务 | 预估 | 负责人 |
|------|------|--------|
| 可访问性修复（aria + 键盘 + 焦点） | 2天 | 前端 |
| AI 页拆分重构 | 2天 | 前端 |
| react-hook-form 引入 | 1.5天 | 前端 |
| api-cache 集成 | 1天 | 前端 |
| Zod 运行时校验 | 1天 | 前端 |
| 暗色模式修复 | 1天 | 前端 |
| 重型依赖懒加载 | 0.5天 | 前端 |
| 长消息虚拟列表 | 1天 | 前端 |

**交付物**:
- WCAG AA 合规
- AI 页面可维护性显著提升
- 前端数据流清晰可测

---

## 七、团队技术能力提升建议

### 7.1 代码审查清单

每次 PR 必须过以下检查点：

**后端**:
- [ ] 查询是否有 user_id 过滤（数据隔离）
- [ ] 是否有 N+1 查询模式
- [ ] Service 层是否只抛领域异常
- [ ] 新字段是否有 Pydantic 校验（max_length, gt, regex）
- [ ] 新表/新字段是否有对应的 Alembic 迁移
- [ ] 新端点是否有对应的测试

**前端**:
- [ ] 所有交互元素是否有键盘支持
- [ ] 图标按钮是否有 aria-label
- [ ] API 调用是否有错误处理（非静默 catch）
- [ ] 新组件是否有 TypeScript 类型
- [ ] 是否有不必要的重渲染（缺 memo/callback）

### 7.2 推荐学习资源

| 主题 | 资源 | 团队适用角色 |
|------|------|-------------|
| SQLAlchemy 2.0 最佳实践 | 官方文档 ORM 部分 | 后端 |
| FastAPI 安全实践 | fastapi.tiangolo.com/tutorial/security | 后端 |
| React 性能优化 | react.dev/learn/render-and-commit | 前端 |
| Web 可访问性 | web.dev/learn/accessibility | 前端 |
| 异步 Python | aio-libs.org (aiohttp/httpx) | 后端 |
| 数据库索引设计 | use-the-index-luke.com | 全栈 |

### 7.3 工程化规范建议

1. **分支策略**: 当前单线 main 可接受，建议加 `dev` 分支 + PR 审查
2. **提交规范**: 引入 Conventional Commits（feat/fix/refactor/chore）
3. **代码格式化**: 后端 ruff format，前端 prettier，pre-commit hook 自动化
4. **API 版本管理**: 当前 `/api/v1/` 已做，继续坚持
5. **监控告警**: 加 Sentry 异常追踪 + Prometheus 指标采集

---

## 八、现有亮点（值得保持）

| 亮点 | 体现 |
|------|------|
| SQLAlchemy 2.0 Mapped 风格 | 所有模型统一使用现代 ORM API |
| Async-first 架构 | FastAPI + asyncpg + SQLAlchemy async 全链路异步 |
| Pydantic v2 严格校验 | regex + gt + max_length 多层防线 |
| 行情三源容灾 | Tencent → Sina → EastMoney 降级链 |
| 操作审计日志 | 每个变更操作记录 OperationLog |
| ErrorBoundary 故障隔离 | Dashboard 每个卡片独立容错 |
| Session 认证 | httponly + samesite + Redis TTL + 64字节熵 |
| Redis 多角色 | Session + 行情缓存 + 定时任务调度 |
