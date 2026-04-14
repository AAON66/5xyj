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

## Milestone: v1.1 — 体验优化与功能完善

**Shipped:** 2026-04-14
**Phases:** 8 | **Plans:** 28 | **Tasks:** 57

### What Was Built

- Python 3.9 全面兼容 + v1.0 技术债清理 + 审计日��� IP 解析增强
- 暗黑模式基础设施 + 全部 18+ 页面颜色 token 化（FOUC 预防 + localStorage 持久化）
- 菜单三级分组重构 + 设置页搜索导航（高亮 + 自动滚动）
- 管理员用户 CRUD + 密码重置 + 强制改密拦截 + 自我保护
- 数据管理多选筛选 + 匹配状态过滤 + 批次级联删除 + 缴费基数映射修复
- 全页面响应式（手机/平板），员工自助移动卡片流，Drawer 筛选模式
- 融合个人承担额（Excel/飞书输入）+ 特殊规则（选人+选字段+覆盖值，可保存复用）
- 月度对比 diff 重做（左右 workbook + 同步滚动）+ 飞书前端配置闭环

### What Worked

- **零新依赖策略**: AntD 5 内置暗黑模式/响应式/多级菜单，不引入额外包，减少维护负担
- **Token 化先行**: 先迁移硬编码颜色再做暗黑模式，避免了反复修改
- **并行阶段依赖设计**: Phases 16/17/19 仅依赖 Phase 13，与 14-15 链可并行
- **UAT 人工验收闭环**: Phase 14 的 9 项暗黑模式测试全部人工通过

### What Was Inefficient

- **summary-extract 质量低**: CLI 自动提取的 one-liner 经常为空或不可读，里程碑 accomplishments 需手动重写
- **VALIDATION.md 模板未补齐**: Phase 13-17 的 Nyquist 验证占位文件一直是 draft，未在阶段内完成
- **VERIFICATION.md human_needed 堆积**: Phase 14/15 的浏览器级验证项在最后才统一处理

### Patterns Established

- `useSemanticColors` / `useCardStatusColors` / `getChartColors` 三层颜色消费接口
- FOUC 预防: index.html 同步脚本 + ThemeModeProvider ��取 data-theme 属性
- Drawer 筛选模式: 移动端用抽屉替代内联筛选器
- FusionRule 持久化模型: 特殊规则 CRUD + aggregate runtime overlay
- system_settings 表: 飞书运行时配置 DB 持久化 + effective settings 合并

### Key Lessons

1. **样式迁移应分批验证**: 18+ 页面颜色迁移分 4 个 plan 执行，每批验证 hex 残留，比一次性迁移安全
2. **响应式适配按价值排序**: 员工自助查询是最高价值移动场景，优先适配效果最好
3. **Salary 模板边界要明确**: 个人承担额只进 Tool 模板，Salary 逻辑不碰，避免回归风险

### Cost Observations

- Sessions: ~8 (discuss/plan/execute per phase)
- Notable: 25 天完成 8 阶段 28 计划，平均约 3 天/阶段

## Cross-Milestone Trends

| Metric | v1.0 | v1.1 |
|--------|------|------|
| Phases | 12 | 8 |
| Plans | 31 | 28 |
| Tasks | 56 | 57 |
| Duration | 10 days | 25 days |
| Files changed | 378 | 177 |
| Lines added | 53,276 | 20,069 |
| Lines removed | - | 5,653 |
| Gap closure phases | 2 | 0 |
| Requirements | 23 | 23 |
| UAT passed | - | 9/9 (Phase 14) |
