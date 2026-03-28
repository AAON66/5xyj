---
phase: 3
reviewers: [codex]
reviewed_at: 2026-03-28T14:52:00Z
plans_reviewed: [03-01-PLAN.md, 03-02-PLAN.md]
---

# Cross-AI Plan Review — Phase 3

## Codex Review (GPT-5.4)

### Plan 03-01 Review

#### Summary
这份计划的方向基本正确，先补后端基础设施，再把限流、审计、脱敏和端点接入收口，符合该阶段"后端先封口"的主线。但它现在仍偏"组件清单"，离"证明 Phase 3 目标已达成"的执行计划还有距离，尤其是 PII 端点覆盖边界、审计日志内容约束、角色差异化脱敏、`auth_enabled=false` 分支，以及限流实现细节都还不够明确。`CORS fix` 混在安全加固波次里也有轻微跑题风险。

#### Strengths
- 先做 `AuditLog` 模型、审计服务、脱敏工具，再接入业务端点，依赖顺序合理。
- 明确把测试放进每个任务里，而不是最后补。
- 登录限流被单独列出来，符合 D-04，不会遗漏。
- 将审计接入 auth、aggregate、users、export，已经覆盖了大部分高价值操作面。
- 把 ID masking 放在 API 响应层处理，和 D-12 一致，避免污染数据库存储。

#### Concerns
- **HIGH**: 没有显式列出"PII 端点清单"和验收方式。SEC-01 要求的是"every endpoint returning PII"，但计划只写了"remaining endpoints"，容易漏掉预览、查询详情、员工自助查询、导出前预览、审计日志自身等返回敏感字段的接口。
- **HIGH**: 脱敏规则只提了"ID masking in API responses"，没有明确实现"admin/HR 全量、employee 脱敏、export 全量"这三个分支。SEC-04 的关键不是单纯加个 util，而是把角色语义正确落到所有 schema/serializer。
- **HIGH**: 审计日志内容范围未定义。若直接记录请求体/变更前后对象，极易把密码、token、完整身份证号、导出参数中的敏感字段再次写入日志，形成二次泄露面。
- **HIGH**: `auth_enabled=false` 的开发模式绕过规则没有出现在任务或测试里。这个分支是锁定决策，必须验证，否则很容易破坏本地开发流。
- **MEDIUM**: 登录限流只写"add rate limiting"，没说明 key 维度、失败/成功重置策略、锁定反馈、并发行为。D-04 要的是"同一用户名 5 次失败/15 分钟锁定"，实现细节不能模糊。
- **MEDIUM**: 计划没有提数据库迁移/Alembic。新增 `AuditLog` 模型如果不带迁移步骤，落地不完整。
- **MEDIUM**: 审计日志"只读、不可删除和修改"只在需求里出现，计划任务没有单独约束，容易只做到"前端不展示删除按钮"，而不是后端真正禁止写操作。
- **MEDIUM**: `CORS fix` 和安全主线关联弱，混入 Wave 1 会分散验证焦点。如果只是为前端联调兜底，应标记为附带修复而非核心交付。
- **LOW**: 审计事件没有明确是否记录失败事件。阶段目标至少要记录登录、导出、修改；通常失败登录和被限流事件也应记，否则溯源价值不足。

#### Suggestions
- 先补一张"PII response endpoint inventory"，逐个标注：是否要求认证、允许角色、返回的身份证号是 full 还是 masked、export/download 是否例外返回 full
- 将 Task 3 拆成两项，避免把"审计接入"与"响应脱敏"混在同一个收尾任务里
- 为审计日志定义最小安全 schema，避免原样存请求体
- 明确"只读"落实点：后端无 update/delete endpoint、ORM/service 层无修改入口、测试验证 admin 也不能改删
- 把 `auth_enabled=false` 作为独立测试组加入
- 给登录限流写清楚规则（key=username、仅失败计数、成功重置、锁定窗口15分钟）
- 增加针对导出链路的脱敏测试
- 明确需包含 Alembic migration 和回归测试

#### Risk Assessment
**MEDIUM-HIGH**。主骨架对，但几个核心安全边界仍未具体化。

---

### Plan 03-02 Review

#### Summary
这份计划作为 Wave 2 是合理的，审计日志页面依赖后端接口先稳定，顺序没问题。但它过于轻，基本只覆盖了 SEC-03 的展示层，第二个任务"Human verification checkpoint"又太泛，缺少可执行性和可交付物定义。

#### Strengths
- 明确依赖 03-01，避免前端先做假接口
- 审计日志页包含筛选和分页，符合 D-06 的基本需求
- 指定 admin-only access，和权限模型一致
- 将人工验证放到单独任务，有助于阶段验收

#### Concerns
- **HIGH**: "Human verification checkpoint for all Phase 3 features" 不是可执行任务，没有明确步骤、负责人、输入数据、验收记录和失败处理方式
- **MEDIUM**: 审计日志页没说明是否为服务端分页、排序、默认时间范围、时区处理
- **MEDIUM**: 没写前端权限防护的验证方式
- **MEDIUM**: 没有前端自动化测试或至少集成测试项
- **LOW**: 如果审计日志条目里包含敏感元数据，页面展示也需定义脱敏/截断策略

#### Suggestions
- 将第二个任务改成明确的验收矩阵
- 给审计日志页面补上非功能约束（服务端分页、默认倒序、时区统一）
- 增加前端测试（路由守卫、筛选参数、分页切换）
- 明确人工验证产物（checklist、截图或录屏）

#### Risk Assessment
**MEDIUM**。顺序正确，但计划偏薄，第二个任务不够工程化。

---

## Consensus Summary

> 仅有一个外部评审者 (Codex)，以下为其核心观点总结。

### Agreed Strengths
- 依赖顺序合理：先建基础设施（模型/服务/工具），再接入业务端点，最后前端页面
- TDD 方法论贯穿任务，测试与实现并行
- 审计接入覆盖了主要高价值操作面
- ID masking 放在 API 响应层，符合 D-12 约束

### Key Concerns (优先级排序)

1. **PII 端点清单缺失** (HIGH) — SEC-01 要求保护"所有含 PII 端点"，但计划未显式列出完整端点清单
2. **角色化脱敏分支不够明确** (HIGH) — admin/HR 全量 vs employee 脱敏 vs export 全量，三个分支需在计划中更具体
3. **审计日志二次泄露风险** (HIGH) — detail 字段存储策略需定义安全边界，避免存入密码/token/完整身份证号
4. **auth_enabled=false 开发模式测试缺失** (HIGH) — 锁定决策 D-02，必须有测试验证
5. **数据库迁移步骤缺失** (MEDIUM) — AuditLog 模型需要 Alembic 迁移
6. **人工验证任务过于笼统** (HIGH) — 需要具体的验收矩阵和步骤

### Divergent Views
- N/A（仅一个评审者）

---

*Review conducted: 2026-03-28*
*Reviewer: Codex (GPT-5.4)*
