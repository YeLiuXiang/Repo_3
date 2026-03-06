# 任务清单：国内主流社交媒体数据采集与分析平台

**输入**：`specs/social-media-collect-analyze/plan.md` + `specs/social-media-collect-analyze/prd.md`
**创建日期**：2026-03-06
**前置条件**：plan.md（必须）、prd.md（必须）

---

## 格式说明

```
- [ ] T001 [P?] [US?] 任务描述（含目标文件路径）
```

- `[P]`：可并行（不同文件，无依赖关系时标注）
- `[US1]`/`[US2]`：关联的用户故事编号
- 无标注：依赖前序任务，必须串行执行

**DoD（完成定义）标准**：代码已提 PR + 单元测试覆盖率 ≥ 80% + PR Review 通过 + 无阻断 Bug

---

## 阶段一：环境搭建（所有用户故事的前置）

> ⚠️ 此阶段完成前，不得开始任何用户故事任务。

- [ ] T001 初始化项目目录结构（pyproject.toml / requirements.txt、src/ 分层布局：api/services/models/collectors/utils/dashboard/workers，路径：项目根目录）
- [ ] T002 配置 Docker Compose 本地环境（PostgreSQL 16 + 应用服务 + Redis，路径：docker-compose.yml）
- [ ] T003 [P] 配置代码风格工具（ruff + black + pre-commit，路径：.ruff.toml / .pre-commit-config.yaml）
- [ ] T004 [P] 配置 CI 基础检查（lint + test，路径：.github/workflows/ci.yml）
- [ ] T005 初始化数据库迁移框架（Alembic 集成 SQLAlchemy，路径：alembic.ini / migrations/env.py）

---

## 阶段二：基础模块（阻塞所有用户故事）

> ⚠️ 关键前置，优先完成。

- [ ] T010 创建全部数据库 Schema 迁移脚本（User / CollectTask / PlatformResult / ContentItem / SentimentResult / TrendSummary 六张表，路径：migrations/versions/001_init_schema.py）
- [ ] T011 [P] 实现 JWT 工具函数（签发 / 验证 / 过期处理，密钥读自环境变量，路径：src/auth/jwt_utils.py）
- [ ] T012 [P] 实现 RBAC 权限中间件（role 枚举：admin/analyst/operator/readonly，readonly 对 POST/PATCH/DELETE 返回 403，路径：src/auth/rbac.py）
- [ ] T013 [P] 实现违禁关键词过滤工具（违禁词库 + 正则匹配，路径：src/utils/keyword_filter.py）
- [ ] T014 [P] 实现通用 HTTP 客户端封装（httpx 异步 + 随机请求间隔 2~8 秒 + 反爬降级标志，路径：src/utils/http_client.py）
- [ ] T015 编写基础模块单元测试（路径：tests/unit/test_foundation.py）

---

## 阶段三：用户故事 US-07 — 用户账号与权限管理（优先级：P3，作为全局前置依赖）

**目标**：管理员可为用户设置角色权限，只读用户无法执行写操作；所有后续接口依赖此认证体系。
**独立测试标准**：创建 admin / operator / readonly 三类账号，逐项验证 API 访问限制。

### 实现任务

- [ ] T020 [US7] 实现 User ORM 模型（bcrypt 密码哈希，role 枚举，路径：src/models/user.py）
- [ ] T021 [P] [US7] 实现用户登录接口（`POST /api/auth/login`，JWT 签发，限流 10 次/IP/min，路径：src/api/auth.py）
- [ ] T022 [P] [US7] 实现用户角色修改接口（`PATCH /api/admin/users/{user_id}/role`，仅 admin 可操作，审计日志，路径：src/api/admin.py）
- [ ] T023 [P] [US7] 编写 US-07 单元测试（路径：tests/unit/test_auth.py）

---

## 阶段四：用户故事 US-01 — 配置并执行关键词数据采集任务（优先级：P1）🎯 MVP

**目标**：用户提交关键词后，系统 60 秒内开始采集抖音/知乎/小红书，完成后展示条数；违禁词拒绝创建；单平台失败不中断整体任务。
**独立测试标准**：可在不依赖分析模块的情况下，单独创建任务、查看任务状态并下载原始采集结果来验证本故事。

### 实现任务

- [ ] T030 [US1] 实现 CollectTask + PlatformResult + ContentItem ORM 模型及任务状态枚举（路径：src/models/collect_task.py、src/models/platform_result.py、src/models/content_item.py）
- [ ] T031 [P] [US1] 实现抖音采集器（httpx 优先，遇 403/412/验证码页面降级 Playwright，路径：src/collectors/douyin.py）
- [ ] T032 [P] [US1] 实现知乎采集器（httpx 优先，降级策略同上，路径：src/collectors/zhihu.py）
- [ ] T033 [P] [US1] 实现小红书采集器（httpx 优先，降级策略同上，路径：src/collectors/xiaohongshu.py）
- [ ] T034 [US1] 实现 Playwright 降级引擎（实例池管理，预热超时处理，路径：src/collectors/playwright_engine.py）
- [ ] T035 [US1] 实现采集任务服务（任务状态机 pending→running→completed/failed、平台级故障隔离、total_count 汇总，路径：src/services/task_service.py）
- [ ] T036 [P] [US1] 实现创建采集任务接口（`POST /api/tasks`，违禁词过滤、权限校验，路径：src/api/tasks.py）
- [ ] T037 [P] [US1] 实现查询任务详情接口（`GET /api/tasks/{task_id}`，含 platform_results 列表，路径：src/api/tasks.py）
- [ ] T038 [US1] 编写 US-01 单元及集成测试（路径：tests/unit/test_collection.py）

---

## 阶段五：用户故事 US-02 — 查看内容热度趋势分析（优先级：P1）🎯 MVP

**目标**：用户在分析页选择关键词 + 时间范围，5 秒内展示多平台折线趋势图；数据不足时附提示。
**独立测试标准**：可通过导入预置数据集，在不执行新采集任务的情况下单独验证趋势图展示逻辑。

### 实现任务

- [ ] T040 [US2] 实现 TrendSummary ORM 模型（keyword/platform/date 联合唯一索引，路径：src/models/trend_summary.py）
- [ ] T041 [US2] 实现趋势聚合服务（pandas 按 keyword/platform/date 聚合 ContentItem，填充 TrendSummary，路径：src/services/trend_service.py）
- [ ] T042 [US2] 实现热度趋势查询接口（`GET /api/analysis/trend`，数据不足警告逻辑，路径：src/api/analysis.py）
- [ ] T043 [P] [US2] 编写 US-02 单元测试（路径：tests/unit/test_trend.py）

---

## 阶段六：用户故事 US-03 — 品牌关键词情感分析（优先级：P1）🎯 MVP

**目标**：用户对指定关键词发起情感分析，30 秒内返回正面/中性/负面占比及代表内容；数据不足 20 条时附置信度警示。
**独立测试标准**：可使用离线标注数据集验证情感分类准确率，无需依赖实时采集。

### 实现任务

- [ ] T048 [US3] 实现 SentimentResult ORM 模型（sentiment 枚举 + confidence 字段，路径：src/models/sentiment_result.py）
- [ ] T049 [US3] 实现情感分析服务（snownlp 批量处理，接口抽象支持后续升级 transformers，路径：src/services/sentiment_service.py）
- [ ] T050 [US3] 实现情感分析接口（`POST /api/analysis/sentiment`，低数据量警告，限流 5 次/用户/min，路径：src/api/analysis.py）
- [ ] T051 [P] [US3] 编写 US-03 单元测试（路径：tests/unit/test_sentiment.py）

---

## 阶段七：用户故事 US-05 — 采集任务定时调度（优先级：P2）

**目标**：用户为采集任务配置 cron 表达式后，系统在设定时间 ±5 分钟内自动触发；上一次任务未完成时跳过并记录日志。
**独立测试标准**：可通过设置最短间隔（如 1 分钟）的定时任务，在测试环境中验证调度逻辑。

### 实现任务

- [ ] T056 [US5] 实现 APScheduler 调度器集成（进程内启动、任务锁防并发重复执行，路径：src/services/scheduler_service.py）
- [ ] T057 [US5] 实现创建定时任务接口（`POST /api/tasks/scheduled`，cron 表达式验证，路径：src/api/tasks.py）
- [ ] T058 [P] [US5] 实现任务跳过逻辑（检测同关键词运行中任务，写入 skipped 状态及日志，路径：src/services/task_service.py）
- [ ] T059 [P] [US5] 编写 US-05 单元测试（路径：tests/unit/test_scheduler.py）

---

## 阶段八：用户故事 US-06 — 热门内容榜单浏览（优先级：P2）

**目标**：用户进入热门榜单页面，按互动量（点赞+评论+收藏）降序展示指定平台近 24 小时前 50 条内容。
**独立测试标准**：可通过导入预置数据集，单独验证榜单排序规则和展示字段的正确性。

### 实现任务

- [ ] T063 [US6] 实现榜单查询服务（按 interaction_total 降序，时间窗口过滤，路径：src/services/leaderboard_service.py）
- [ ] T064 [US6] 实现热门榜单接口（`GET /api/leaderboard`，platform/hours/limit 参数，路径：src/api/leaderboard.py）
- [ ] T065 [P] [US6] 编写 US-06 单元测试（路径：tests/unit/test_leaderboard.py）

---

## 阶段九：用户故事 US-04 — 多平台数据对比报告导出（优先级：P2）

**目标**：用户点击"导出报告"后 30 秒内获得包含趋势图、情感分布图和数据汇总表的 PDF 文件；无数据时阻止导出。
**独立测试标准**：可通过预置分析数据直接触发导出功能，验证文件格式与内容完整性。

### 实现任务

- [ ] T069 [US4] 实现 PDF 报告生成服务（WeasyPrint，图表预渲染缓存，超时上限 29 秒，路径：src/services/report_service.py）
- [ ] T070 [US4] 配置异步报告生成队列（Celery + Redis Worker，路径：src/workers/report_worker.py）
- [ ] T071 [US4] 实现报告导出接口（`POST /api/reports/export`，无数据时返回 422，路径：src/api/reports.py）
- [ ] T072 [P] [US4] 实现报告下载接口（`GET /api/reports/{report_id}/download`，文件流响应，路径：src/api/reports.py）
- [ ] T073 [P] [US4] 编写 US-04 单元测试（路径：tests/unit/test_report.py）

---

## 阶段十：Streamlit Dashboard 展示层（US-01/02/03/06 可视化前端）

**目标**：基于 Streamlit 构建交互式仪表盘，涵盖任务管理、趋势图、情感饼图、热门榜单四个页面。

- [ ] T080 [US1] [US2] [US3] [US6] 实现 Streamlit 应用入口及公共布局（JWT 登录态、导航栏，路径：src/dashboard/app.py）
- [ ] T081 [P] [US1] 实现采集任务管理页（任务创建表单、状态列表，路径：src/dashboard/pages/tasks.py）
- [ ] T082 [P] [US2] 实现热度趋势分析页（Plotly 折线图，平台筛选，路径：src/dashboard/pages/trend.py）
- [ ] T083 [P] [US3] 实现情感分析页（Plotly 饼图，代表内容展示，路径：src/dashboard/pages/sentiment.py）
- [ ] T084 [P] [US6] 实现热门榜单页（平台切换，互动数据表格，路径：src/dashboard/pages/leaderboard.py）

---

## 阶段十一：收尾与横向关注点

- [ ] T090 [P] 编写集成测试（全流程 E2E：采集→分析→导出，路径：tests/integration/）
- [ ] T091 [P] 更新 README 和 API 文档（接口说明、部署步骤，路径：README.md / docs/api.md）
- [ ] T092 [P] 安全扫描（依赖漏洞检查 pip-audit，JWT 密钥泄露检查，路径：.github/workflows/security.yml）
- [ ] T093 性能验证（趋势图 5 秒、情感分析 30 秒/100 条基准测试，路径：tests/perf/）

---

## 依赖关系与执行顺序

```
阶段一（环境搭建）
    ↓
阶段二（基础模块）  ← 阻塞所有用户故事
    ↓
阶段三（US-07 权限，全局前置）
    ↓
阶段四（US-01 采集）────┐
阶段五（US-02 趋势）────┤ （阶段三完成后可并行推进）
阶段六（US-03 情感）────┤
阶段七（US-05 定时）────┤ （依赖阶段四）
阶段八（US-06 榜单）────┤
阶段九（US-04 导出）────┘ （依赖阶段五、六）
    ↓
阶段十（Dashboard 展示层，依赖阶段四~九各 API）
    ↓
阶段十一（收尾）
```

**关键路径**：T001 → T005 → T010 → T020 → T030 → T035 → T041 → T049 → T069 → T090

---

## 工作量估算

| 阶段 | 任务数 | SP |
|---|---|---|
| 阶段一：环境搭建 | 5 | 8 |
| 阶段二：基础模块 | 6 | 13 |
| 阶段三：US-07 权限管理 | 4 | 7 |
| 阶段四：US-01 采集任务 | 9 | 22 |
| 阶段五：US-02 趋势分析 | 4 | 8 |
| 阶段六：US-03 情感分析 | 4 | 8 |
| 阶段七：US-05 定时调度 | 4 | 9 |
| 阶段八：US-06 热门榜单 | 3 | 5 |
| 阶段九：US-04 报告导出 | 5 | 11 |
| 阶段十：Dashboard 展示层 | 5 | 10 |
| 阶段十一：收尾 | 4 | 7 |
| **合计** | **53** | **108** |

| Sprint Point 参考 | 说明 |
|---|---|
| 1 SP | 简单配置修改，< 1小时 |
| 2 SP | 简单 CRUD + 测试，约半天 |
| 3 SP | 含业务逻辑的模块，约1天 |
| 5 SP | 多服务交互，约2-3天 |
| 8 SP | 新子系统，需拆分 |

**本功能总估算**：约 108 SP（约 7~8 个 Sprint，每 Sprint 14 SP / 两周）

---

## MVP 范围建议

> 最小可交付版本应包含（Sprint 1）：

- ✅ 阶段一（环境搭建，必须）
- ✅ 阶段二（基础模块，必须）
- ✅ 阶段三（US-07 权限，全局前置依赖）
- ✅ 阶段四（US-01 采集任务，P1 核心价值）
- ✅ 阶段五（US-02 趋势分析，P1 核心价值）
- ✅ 阶段六（US-03 情感分析，P1 核心价值）
- ⏸️ 阶段七（US-05 定时调度，P2，可推迟到 Sprint 2）
- ⏸️ 阶段八（US-06 热门榜单，P2，可推迟到 Sprint 2）
- ⏸️ 阶段九（US-04 报告导出，P2，可推迟到 Sprint 2）
- ⏸️ 阶段十（Dashboard 展示层，依赖所有 API，Sprint 2 完成）
- ⏸️ 阶段十一（收尾，Sprint 3）

🎯 **MVP 任务数**：T001~T051，共 35 个任务，约 66 SP
