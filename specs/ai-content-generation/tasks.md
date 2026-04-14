# 任务清单：AI 内容生成与管理平台

**输入**：`specs/ai-content-generation/plan.md` + `specs/ai-content-generation/prd.md`
**创建日期**：2026-04-14
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

- [ ] T001 初始化后端项目目录结构（FastAPI + Celery + 质量评分微服务）（路径：`backend/`, `quality_scorer/`）— 2 SP
- [ ] T002 初始化前端项目（React 18 + TypeScript，Vite）（路径：`frontend/`）— 2 SP
- [ ] T003 [P] 配置后端依赖（requirements.txt / pyproject.toml，含 FastAPI、Celery、SQLAlchemy、Pydantic 等）（路径：`backend/requirements.txt`）— 1 SP
- [ ] T004 [P] 配置前端依赖（package.json，含 React、TypeScript、axios、react-query 等）（路径：`frontend/package.json`）— 1 SP
- [ ] T005 [P] 配置代码风格工具（后端：ruff/black；前端：eslint/prettier）（路径：`backend/.ruff.toml`, `frontend/.eslintrc`）— 1 SP
- [ ] T006 [P] 配置 CI 基础检查（lint + test）（路径：`.github/workflows/ci.yml`）— 1 SP
- [ ] T007 初始化数据库 Schema 及迁移框架（Alembic），建立 Content / ContentGenerationTask / ReviewRecord / QualityScore / BatchGenerationJob 五张表（路径：`backend/alembic/`）— 3 SP
- [ ] T008 [P] 配置本地开发 Docker Compose（PostgreSQL 15 + Redis 7 + FastAPI + Celery + 质量评分服务）（路径：`docker-compose.yml`）— 2 SP

> 阶段一小计：8 个任务，13 SP

---

## 阶段二：基础模块（阻塞所有用户故事）

> ⚠️ 关键前置，优先完成。

- [ ] T009 实现 JWT 鉴权中间件（从账号权限系统 JWT Claims 提取角色，按角色返回 403）（路径：`backend/middleware/auth.py`）— 2 SP
- [ ] T010 [P] 实现数据库 ORM 模型类（5 个实体，含状态枚举定义）（路径：`backend/models/`）— 2 SP
- [ ] T011 [P] 实现 LLM Gateway 封装（统一调用 OpenAI-compatible API，支持超时控制 60s、指数退避重试最多 3 次、模型切换）（路径：`backend/services/llm_gateway.py`）— 3 SP
- [ ] T012 [P] 实现内容状态机服务（强制校验状态流转合法性，非法操作返回 409，含 SELECT FOR UPDATE 行级锁）（路径：`backend/services/content_state_machine.py`）— 2 SP
- [ ] T013 [P] 实现通知服务客户端（HTTP 调用内部通知服务，异步不阻断主流程）（路径：`backend/services/notification_client.py`）— 2 SP
- [ ] T014 [P] 实现隐私过滤器（正则过滤手机号/身份证/邮箱等常见隐私模式，用于 LLM 输出后置检查，满足 AC-18）（路径：`backend/utils/privacy_filter.py`）— 1 SP
- [ ] T015 [P] 编写基础模块单元测试（状态机、隐私过滤器、LLM Gateway mock 测试）（路径：`tests/unit/test_base_modules.py`）— 2 SP

> 阶段二小计：7 个任务，14 SP

---

## 阶段三：用户故事 US-01/02/03 — 多类型内容生成（优先级：P1）🎯 MVP

**目标**：创作者可通过统一生成接口提交文章/图文/短视频脚本生成请求，60 秒内异步返回结果，含超时处理和重试入口。
**独立测试标准**：提交各类型生成请求，轮询任务状态，验证字数/结构/时长等 AC 约束；无需依赖审核或发布流程。

### 实现任务

- [ ] T016 [US1][US2][US3] 实现内容生成 Celery Worker 任务（含 60s soft_time_limit 超时标记、LLM Gateway 调用、生成结果写库、调用质量评分服务降级处理）（路径：`backend/tasks/generation_tasks.py`）— 3 SP
- [ ] T017 [P][US1] 实现文章生成 Prompt 模板（含字数 ≥500 约束、标题+正文结构指令、隐私禁止指令；满足 AC-01/18）（路径：`backend/prompts/article_prompt.py`）— 2 SP
- [ ] T018 [P][US2] 实现图文生成 Prompt 模板（100-300 字正文、至少 1 条配图描述、默认风格逻辑；满足 AC-04/05）（路径：`backend/prompts/image_text_prompt.py`）— 2 SP
- [ ] T019 [P][US3] 实现短视频脚本生成 Prompt 模板及结构化解析（开场/分镜/CTA 三段结构，时长分配与误差校验 ≤10s；满足 AC-06/07）（路径：`backend/prompts/video_script_prompt.py`）— 3 SP
- [ ] T020 [US1][US2][US3] 实现 `POST /api/v1/contents/generate` 接口（参数校验：topic 非空 AC-02、target_duration 枚举校验 AC-07；限流 10次/分钟；触发 Celery 任务返回 202）（路径：`backend/api/v1/contents/generate.py`）— 3 SP
- [ ] T021 [P][US1][US2][US3] 实现 `GET /api/v1/contents/tasks/{task_id}` 任务状态查询接口（含 COMPLETED/TIMEOUT/FAILED 状态响应、质量评分 null 兜底；满足 AC-03/11）（路径：`backend/api/v1/contents/tasks.py`）— 2 SP
- [ ] T022 [P][US1][US2][US3] 实现前端内容生成表单组件（文章/图文/脚本三类型切换，主题/关键词/风格/时长输入，输入校验 AC-02/07）（路径：`frontend/src/components/ContentGenerate/`）— 3 SP
- [ ] T023 [P][US1][US2][US3] 实现前端任务轮询 Hook（每 3s 轮询任务状态，展示进度动画；超时时展示重试入口 AC-03）（路径：`frontend/src/hooks/useTaskPolling.ts`）— 2 SP
- [ ] T024 [P][US1][US2][US3] 编写生成接口单元测试（覆盖正常/输入缺失/超时/评分不可用场景，mock LLM Gateway）（路径：`tests/unit/test_generation_api.py`）— 2 SP

> 阶段三小计：9 个任务，22 SP

---

## 阶段四：用户故事 US-04 — 内容审核（优先级：P1）🎯 MVP

**目标**：审核员可查看待审核队列、执行通过/驳回操作，驳回时原创建人收到含原因通知。
**独立测试标准**：预置"待审核"状态内容，使用审核员账号执行操作，验证状态流转、记录写入和通知触发；无需依赖生成流程实时触发。

### 实现任务

- [ ] T025 [US4] 实现 `GET /api/v1/review/queue` 审核队列接口（分页返回 PENDING_REVIEW 内容；队列为空时返回空数组，满足 AC-09 场景 3）（路径：`backend/api/v1/review/queue.py`）— 2 SP
- [ ] T026 [P][US4] 实现 `POST /api/v1/review/{content_id}/action` 审核操作接口（APPROVE/REJECT，驳回原因 min_length=5 AC-09；写 ReviewRecord；状态机流转；审核时间戳精确到秒 AC-08）（路径：`backend/api/v1/review/action.py`）— 3 SP
- [ ] T027 [P][US4] 实现审核服务层（封装审核业务逻辑：行级锁防并发冲突、驳回后调用通知服务客户端、ReviewRecord 写入）（路径：`backend/services/review_service.py`）— 2 SP
- [ ] T028 [P][US4] 实现前端审核队列页面（列表展示、内容详情预览、通过/驳回操作面板、驳回原因输入框）（路径：`frontend/src/pages/ReviewQueue/`）— 2 SP
- [ ] T029 [P][US4] 编写审核流程单元测试（覆盖通过/驳回/原因过短/并发冲突/队列为空场景）（路径：`tests/unit/test_review_api.py`）— 2 SP

> 阶段四小计：5 个任务，11 SP

---

## 阶段五：用户故事 US-06 — 内容发布管理（优先级：P1）🎯 MVP

**目标**：运营管理员可对已审核内容立即发布或定时排期发布，定时发布误差 ≤5 分钟；非已审核内容被拒绝操作。
**独立测试标准**：预置"已审核"状态内容，使用管理员账号测试立即/定时发布；验证状态流转、时间戳及权限拦截；无需依赖生成流程。

### 实现任务

- [ ] T030 [US6] 实现 `POST /api/v1/contents/{content_id}/publish` 立即发布接口（前置状态校验 APPROVED only，同步写 published_at；满足 AC-12/14）（路径：`backend/api/v1/contents/publish.py`）— 2 SP
- [ ] T031 [P][US6] 实现 `POST /api/v1/contents/{content_id}/schedule` 定时排期接口（前置状态校验、scheduled_at 不得早于当前时间、状态变 SCHEDULED；满足 AC-13/14）（路径：`backend/api/v1/contents/schedule.py`）— 2 SP
- [ ] T032 [P][US6] 实现 `GET /api/v1/contents` 内容列表接口（支持 status 过滤分页，creator 只查自己，operator 查所有）（路径：`backend/api/v1/contents/list.py`）— 2 SP
- [ ] T033 [P][US6] 实现 Celery Beat 定时发布任务（每分钟扫描 scheduled_at ≤ now 且状态为 SCHEDULED 的内容，触发发布状态更新；满足 AC-13）（路径：`backend/tasks/scheduled_publish.py`）— 3 SP
- [ ] T034 [P][US6] 实现 FastAPI 补偿轮询服务（每分钟扫描 scheduled_at ≤ now+5min 的 SCHEDULED 内容，作为 Celery Beat 单点故障兜底）（路径：`backend/services/publish_compensation.py`）— 2 SP
- [ ] T035 [P][US6] 实现前端发布管理页面（已审核内容列表、立即发布/定时排期操作、发布状态展示）（路径：`frontend/src/pages/PublishManager/`）— 2 SP
- [ ] T036 [P][US6] 编写发布管理单元测试（覆盖立即发布/定时发布/非法状态拒绝/时间校验场景）（路径：`tests/unit/test_publish_api.py`）— 2 SP

> 阶段五小计：7 个任务，15 SP

---

## 阶段六：用户故事 US-05 — 质量评分查看（优先级：P2）

**目标**：内容生成成功后展示 0-100 整数评分及 ≥2 条评分维度说明；评分服务不可用时显示"暂无评分"不影响其他操作。
**独立测试标准**：生成任意类型内容后，在结果页校验评分字段及说明条目数量；评分服务 mock 为不可用时，验证降级展示。

### 实现任务

- [ ] T037 [US5] 实现质量评分微服务（接收内容文本，返回 0-100 分及 ≥2 条维度说明；独立 FastAPI 服务；满足 AC-10）（路径：`quality_scorer/main.py`, `quality_scorer/scorer.py`）— 3 SP
- [ ] T038 [P][US5] 实现评分服务集成调用与降级处理（Celery Worker 生成完成后异步调用，try/except 捕获失败，失败时 quality_score 写 null；满足 AC-10/11）（路径：`backend/services/quality_score_service.py`）— 2 SP
- [ ] T039 [P][US5] 实现前端质量评分展示组件（整数分值显示、维度列表；评分 null 时显示"暂无评分"；满足 AC-11）（路径：`frontend/src/components/QualityScore/`）— 1 SP
- [ ] T040 [P][US5] 编写质量评分单元测试（覆盖正常评分/服务不可用降级场景）（路径：`tests/unit/test_quality_score.py`）— 2 SP

> 阶段六小计：4 个任务，8 SP

---

## 阶段七：用户故事 US-07 — 内容草稿管理（优先级：P2）

**目标**：创作者可保存生成内容为草稿、查看草稿列表、编辑草稿、提交审核；退出登录重新登录后草稿仍可访问。
**独立测试标准**：保存一条草稿，退出并重新登录，验证草稿可访问和编辑；提交审核后验证状态流转。

### 实现任务

- [ ] T041 [US7] 实现 `PUT /api/v1/contents/{content_id}/draft` 保存/编辑草稿接口（校验内容归属、状态须为 DRAFT/REJECTED；满足 AC-15）（路径：`backend/api/v1/contents/draft.py`）— 2 SP
- [ ] T042 [P][US7] 实现 `POST /api/v1/contents/{content_id}/submit-review` 提交审核接口（状态须为 DRAFT，变更为 PENDING_REVIEW 并进入审核队列；满足 AC-16）（路径：`backend/api/v1/contents/submit_review.py`）— 2 SP
- [ ] T043 [P][US7] 实现前端草稿列表页面及编辑器（草稿列表、内容编辑、提交审核入口）（路径：`frontend/src/pages/DraftManager/`）— 2 SP
- [ ] T044 [P][US7] 编写草稿管理单元测试（覆盖保存/编辑/提交审核/权限校验场景）（路径：`tests/unit/test_draft_api.py`）— 2 SP

> 阶段七小计：4 个任务，8 SP

---

## 阶段八：用户故事 US-08 — 批量内容生成（优先级：P3）

**目标**：运营管理员可一次提交最多 20 个主题批量生成，展示任务进度，生成完成后在草稿列表可查看。
**独立测试标准**：上传 5 条主题列表，验证批量任务状态和草稿条数是否匹配；验证 21 条时被拒绝（AC-17）。

### 实现任务

- [ ] T045 [US8] 实现 `POST /api/v1/contents/batch-generate` 批量生成接口（topics 数组长度 1-20 校验 AC-17，创建 BatchGenerationJob，异步触发批量 Celery 任务）（路径：`backend/api/v1/contents/batch_generate.py`）— 2 SP
- [ ] T046 [P][US8] 实现批量生成 Celery 任务（遍历 topics 依次调用 LLM Gateway，更新 BatchGenerationJob 进度 completed_count/failed_count）（路径：`backend/tasks/batch_generation_tasks.py`）— 3 SP
- [ ] T047 [P][US8] 实现 `GET /api/v1/contents/batch-jobs/{batch_job_id}` 批量任务状态查询接口（返回进度及状态）（路径：`backend/api/v1/contents/batch_jobs.py`）— 1 SP
- [ ] T048 [P][US8] 实现前端批量生成页面（主题列表上传、进度展示）（路径：`frontend/src/pages/BatchGenerate/`）— 2 SP
- [ ] T049 [P][US8] 编写批量生成单元测试（覆盖正常批量/超出 20 条/部分失败场景）（路径：`tests/unit/test_batch_generate_api.py`）— 2 SP

> 阶段八小计：5 个任务，10 SP

---

## 最终阶段：收尾与横向关注点

- [ ] T050 [P] 编写集成测试（全状态流转 E2E：生成→草稿→审核→发布；覆盖立即发布和定时发布场景）（路径：`tests/integration/test_content_lifecycle.py`）— 3 SP
- [ ] T051 [P] 性能压测（LLM 并发生成场景，验证 Celery Worker 并发控制、Redis 队列告警阈值）（路径：`tests/performance/`）— 2 SP
- [ ] T052 [P] 安全审计（隐私过滤正则验证 AC-18、依赖漏洞扫描、JWT 中间件穿透测试）（路径：`tests/security/`）— 2 SP
- [ ] T053 [P] 更新 API 文档和 README（所有 11 个接口示例、本地开发启动说明）（路径：`docs/api.md`, `README.md`）— 1 SP

> 最终阶段小计：4 个任务，8 SP

---

## 依赖关系与执行顺序

```
阶段一（环境搭建）
    ↓
阶段二（基础模块）← 阻塞所有用户故事
    ↓
阶段三（US-01/02/03 P1）────┐
阶段四（US-04 P1）──────────┤
阶段五（US-06 P1）──────────┤ （阶段二完成后可并行推进）
阶段六（US-05 P2）──────────┤
阶段七（US-07 P2）──────────┤
阶段八（US-08 P3）──────────┘
    ↓
最终阶段（收尾）
```

**关键路径**：T001 → T007 → T010 → T016 → T020 → T025 → T026 → T030 → T050

---

## 工作量估算

| 阶段 | 任务数 | SP |
|---|---|---|
| 阶段一：环境搭建 | 8 | 13 |
| 阶段二：基础模块 | 7 | 14 |
| 阶段三：US-01/02/03 内容生成（P1）| 9 | 22 |
| 阶段四：US-04 内容审核（P1）| 5 | 11 |
| 阶段五：US-06 发布管理（P1）| 7 | 15 |
| 阶段六：US-05 质量评分（P2）| 4 | 8 |
| 阶段七：US-07 草稿管理（P2）| 4 | 8 |
| 阶段八：US-08 批量生成（P3）| 5 | 10 |
| 最终阶段：收尾 | 4 | 8 |
| **合计** | **53** | **109** |

---

## MVP 范围建议

> 最小可交付版本应包含（仅 P1 用户故事）：

- ✅ 阶段一：环境搭建（必须）
- ✅ 阶段二：基础模块（必须）
- ✅ 阶段三：US-01/02/03 多类型内容生成（P1，核心价值）
- ✅ 阶段四：US-04 内容审核（P1，核心闭环）
- ✅ 阶段五：US-06 内容发布管理（P1，核心闭环）
- ⏸️ 阶段六：US-05 质量评分（P2，可推迟到 Sprint 2）
- ⏸️ 阶段七：US-07 草稿管理（P2，可推迟到 Sprint 2）
- ⏸️ 阶段八：US-08 批量生成（P3，可推迟到 Sprint 3）

**MVP 合计**：36 个任务，75 SP
