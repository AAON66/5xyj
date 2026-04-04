# Retrospective

## Milestone: v1.0 — 社保公积金管理系统

**Shipped:** 2026-04-04
**Phases:** 12 | **Plans:** 31 | **Tasks:** 56

### What Was Built

- 多地区社保/公积金 Excel 导入融合平台（广州、杭州、厦门、深圳、武汉、长沙）
- 三角色权限系统（管理员/HR/员工）+ PII 保护 + 审计日志
- 员工主数据管理 + 自助查询门户
- HR 数据管理界面（级联筛选、质量仪表盘）
- Ant Design 5 飞书风格 UI 重建（23 个页面）
- REST API + API Key 双重认证
- 飞书多维表格双向同步 + OAuth 登录
- 跨期对比 + 异常检测 + 字段映射管理 UI

### What Worked

- **波次并行执行**: Wave 1/2 并行大幅减少执行时间
- **Gap closure 模式**: 验证器发现问题 → 自动创建修复计划 → 重新验证，闭环高效
- **里程碑审计**: 集成检查器发现了 3 个运行时 404（手动测试可能需要更长时间才能发现）
- **规则优先解析策略**: 多地区表头差异通过同义映射规则处理，LLM 只做兜底

### What Was Inefficient

- **Progress 表状态不同步**: ROADMAP.md 的进度表经常与实际完成状态不同步（部分阶段显示 "In Progress" 但实际已完成）
- **Worktree 竞态**: 并行代理 worktree 创建偶尔失败（git config 锁），需要回退到顺序执行
- **REQUIREMENTS.md 复选框滞后**: 多个阶段完成后复选框未及时更新，在里程碑审计时才发现

### Patterns Established

- 每个阶段：discuss → plan → review → execute → verify 完整链路
- 跨 AI 审查 (cross-AI review) 在规划后执行，捕获实现前的设计问题
- 异常检测使用 delete-before-insert 模式确保幂等性
- 所有 API 端点使用中文 summary/description 便于 Swagger 阅读

### Key Lessons

1. **集成检查是必要的**: 12 个阶段独立验证都通过，但跨阶段路径不匹配直到集成检查才暴露
2. **小修复应内联**: Phase 12 只有 3 行代码改动，单独建阶段是过度流程化
3. **并行代理需要隔离**: Worktree 隔离对并行执行至关重要，但 git config 锁仍是瓶颈

### Cost Observations

- Sessions: ~10 (discuss/plan/execute per phase batch)
- Notable: 10 天完成 12 阶段 31 计划，平均每个计划含执行+验证约 15 分钟

## Cross-Milestone Trends

| Metric | v1.0 |
|--------|------|
| Phases | 12 |
| Plans | 31 |
| Tasks | 56 |
| Duration | 10 days |
| Files changed | 378 |
| Lines added | 53,276 |
| Gap closure phases | 2 (Phase 11.05 + Phase 12) |
