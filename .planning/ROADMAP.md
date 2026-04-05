# Roadmap: 社保公积金管理系统

## Milestones

- ✅ **v1.0 社保公积金管理系统** — Phases 1-12 (shipped 2026-04-04)
- 🚧 **v1.1 体验优化与功能完善** — Phases 13-20 (in progress)

## Phases

<details>
<summary>✅ v1.0 社保公积金管理系统 (Phases 1-12) — SHIPPED 2026-04-04</summary>

- [x] Phase 1: Export Stabilization (2/2 plans)
- [x] Phase 2: Authentication & RBAC (3/3 plans)
- [x] Phase 3: Security Hardening (2/2 plans)
- [x] Phase 4: Employee Master Data (2/2 plans) — completed 2026-03-29
- [x] Phase 5: Employee Portal (2/2 plans) — completed 2026-03-30
- [x] Phase 6: Data Management (2/2 plans)
- [x] Phase 7: Design System & UI Foundation (4/4 plans)
- [x] Phase 8: Page Rebuild & UX Flow (2/2 plans)
- [x] Phase 9: API System (2/2 plans)
- [x] Phase 10: Feishu Integration (4/4 plans) — completed 2026-04-02
- [x] Phase 11: Intelligence & Polish (5/5 plans) — completed 2026-04-04
- [x] Phase 12: Integration Wiring Fix (1/1 plan) — completed 2026-04-04

**Total:** 12 phases, 31 plans, 56 tasks

See: `.planning/milestones/v1.0-ROADMAP.md` for full details

</details>

### 🚧 v1.1 体验优化与功能完善 (In Progress)

**Milestone Goal:** 清理技术债、全面提升前端体验（响应式+暗黑模式+菜单重组）、补齐账号管理和融合能力短板、适配云服务器部署环境。

- [x] **Phase 13: 基础准备与部署适配** - Python 3.9 适配 + 技术债清理 + 审计日志增强 + 快速见效修复 (completed 2026-04-05)
- [ ] **Phase 14: 样式 Token 化与暗黑模式** - 内联样式迁移到 AntD token + 暗黑模式切换
- [ ] **Phase 15: 菜单重组与设置导航** - 左侧菜单多级折叠 + 设置页搜索导航
- [ ] **Phase 16: 账号管理** - 管理员用户 CRUD + 用户自改密码
- [ ] **Phase 17: 数据管理增强** - 筛选多选 + 匹配状态过滤 + 批次联动删除 + 缴费基数修复
- [ ] **Phase 18: 全页面响应式适配** - 手机端/平板/多窗口尺寸全页面适配
- [ ] **Phase 19: 融合能力增强** - 个人承担额 + 特殊规则配置
- [ ] **Phase 20: 对比重做与飞书完善** - diff 风格月度对比 + 飞书前端配置页

## Phase Details

### Phase 13: 基础准备与部署适配
**Goal**: 系统可在 Python 3.9 云服务器上稳定运行，技术债清零，审计日志可信
**Depends on**: Phase 12 (v1.0 complete)
**Requirements**: INFRA-01, INFRA-02, INFRA-03, INFRA-04, FUSE-02, FUSE-04
**Success Criteria** (what must be TRUE):
  1. 后端在 Python 3.9 环境下启动正常且全部测试通过
  2. v1.0 遗留的 5 个废弃组件文件已删除，武汉公积金测试补充完成
  3. 审计日志记录显示真实客户端 IP 地址（经过反向代理时正确解析 X-Forwarded-For）
  4. 快速融合页面显示已上传文件数量计数
  5. 员工主档上传步骤默认选择"使用服务器已有主档"
**Plans:** 4/4 plans complete
Plans:
- [ ] 13-01-PLAN.md — Python 3.9 兼容性修复 + 依赖清理
- [ ] 13-02-PLAN.md — 前端废弃组件清理 + 快速融合页面小修复
- [ ] 13-03-PLAN.md — 技术债常量合并 + 自助查询端点认证修复
- [ ] 13-04-PLAN.md — 审计日志 IP 解析增强 + nginx 配置文档

### Phase 14: 样式 Token 化与暗黑模式
**Goal**: 用户可在亮色和暗黑模式之间自由切换，所有页面视觉一致无硬编码颜色残留
**Depends on**: Phase 13
**Requirements**: UX-01, UX-02
**Success Criteria** (what must be TRUE):
  1. 所有页面中的硬编码内联颜色已替换为 Ant Design 主题 token
  2. 用户点击切换按钮可在亮色/暗黑模式间切换，所有页面颜色正确响应
  3. 暗黑模式偏好持久化到 localStorage，刷新后保持用户选择
  4. 暗黑模式下无"半白半黑"的混合颜色问题
**Plans**: 4 plans
Plans:
- [ ] 14-01-PLAN.md — 主题基础设施（buildTheme + ThemeModeProvider + hooks + FOUC + 切换按钮 + MainLayout token 化）
- [ ] 14-02-PLAN.md — 核心业务页面 token 化（App/Login/Workspace/Portal/Dashboard/Employees/ImportBatchDetail/SimpleAggregate/Imports）
- [ ] 14-03-PLAN.md — 结果/对比/飞书页面 token 化（Results/Exports/Mappings/AnomalyDetection/Compare/PeriodCompare/FeishuFieldMapping/FeishuSync/ApiKeys）
- [ ] 14-04-PLAN.md — 死代码清理 + 硬编码色审计脚本 + 视觉验证 checkpoint
**UI hint**: yes

### Phase 15: 菜单重组与设置导航
**Goal**: 用户通过层级清晰的菜单快速定位功能，低频功能不再干扰日常操作
**Depends on**: Phase 14
**Requirements**: UX-04, UX-05
**Success Criteria** (what must be TRUE):
  1. 左侧菜单按功能分组为多级结构，低频功能（如高级设置）收入子菜单
  2. 菜单分组折叠/展开状态在页面导航间保持
  3. 设置页提供搜索框，输入关键词可快速定位并导航到对应设置项
**Plans**: TBD
**UI hint**: yes

### Phase 16: 账号管理
**Goal**: 管理员可完整管理系统用户，用户可自主维护密码
**Depends on**: Phase 13
**Requirements**: ACCT-01, ACCT-02, ACCT-03, ACCT-04
**Success Criteria** (what must be TRUE):
  1. 管理员可在账号管理页面创建新用户并分配角色
  2. 管理员可修改已有用户的角色权限
  3. 管理员可为用户重置密码
  4. 普通用户可在个人设置中修改自己的密码
**Plans**: TBD
**UI hint**: yes

### Phase 17: 数据管理增强
**Goal**: HR 可用更灵活的筛选和删除操作高效管理社保数据
**Depends on**: Phase 13
**Requirements**: DATA-01, DATA-02, DATA-03, DATA-04
**Success Criteria** (what must be TRUE):
  1. 数据管理页面的地区、公司等筛选条件支持多选
  2. 数据管理页面提供"已匹配/未匹配"过滤选项，默认显示已匹配数据
  3. 删除批次时自动清理关联的 NormalizedRecords、MatchResults、ValidationIssues
  4. 个人险种缴费基数显示真实基数值而非错误值
**Plans**: TBD
**UI hint**: yes

### Phase 18: 全页面响应式适配
**Goal**: 用户在手机、平板、不同窗口尺寸下都能正常使用系统所有功能
**Depends on**: Phase 14
**Requirements**: UX-03
**Success Criteria** (what must be TRUE):
  1. 所有数据表格页面在窄屏下提供横向滚动且左列固定
  2. 移动端侧边栏自动切换为 Drawer 模式，导航后自动关闭
  3. 员工自助查询页面在手机端布局优先适配（最高价值移动端场景）
  4. 上传、导出等操作流程在移动端可完整执行
**Plans**: TBD
**UI hint**: yes

### Phase 19: 融合能力增强
**Goal**: 融合流程支持个人承担额和特殊规则，覆盖复杂薪酬场景
**Depends on**: Phase 13
**Requirements**: FUSE-01, FUSE-03
**Success Criteria** (what must be TRUE):
  1. 融合结果包含个人社保承担额和个人公积金承担额字段（通过 Excel 上传或飞书同步输入）
  2. 用户可配置特殊规则：选择员工 + 选择字段 + 设置覆盖值
  3. 特殊规则可保存并在后续融合中复用
  4. 新字段仅影响 Tool 模板输出，Salary 模板保持不变
**Plans**: TBD
**UI hint**: yes

### Phase 20: 对比重做与飞书完善
**Goal**: 月度对比以直观的 diff 视图呈现差异，飞书集成可在前端完整配置
**Depends on**: Phase 14
**Requirements**: COMP-01, FEISHU-01
**Success Criteria** (what must be TRUE):
  1. 月度对比页面以左右 Excel 表格样式展示两期数据，差异单元格高亮显示
  2. 对比面板支持同步滚动，500+ 员工数据量下渲染流畅
  3. 飞书凭证、同步设置等配置可在前端页面直接查看和修改
**Plans**: TBD
**UI hint**: yes

## Progress

**Execution Order:**
Phases execute in numeric order. Phases 15-18 depend on 14 (token化); Phases 16, 17, 19 only depend on 13.

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 1. Export Stabilization | v1.0 | 2/2 | Complete | - |
| 2. Authentication & RBAC | v1.0 | 3/3 | Complete | - |
| 3. Security Hardening | v1.0 | 2/2 | Complete | - |
| 4. Employee Master Data | v1.0 | 2/2 | Complete | 2026-03-29 |
| 5. Employee Portal | v1.0 | 2/2 | Complete | 2026-03-30 |
| 6. Data Management | v1.0 | 2/2 | Complete | - |
| 7. Design System & UI Foundation | v1.0 | 4/4 | Complete | - |
| 8. Page Rebuild & UX Flow | v1.0 | 2/2 | Complete | - |
| 9. API System | v1.0 | 2/2 | Complete | - |
| 10. Feishu Integration | v1.0 | 4/4 | Complete | 2026-04-02 |
| 11. Intelligence & Polish | v1.0 | 5/5 | Complete | 2026-04-04 |
| 12. Integration Wiring Fix | v1.0 | 1/1 | Complete | 2026-04-04 |
| 13. 基础准备与部署适配 | v1.1 | 0/4 | Complete    | 2026-04-05 |
| 14. 样式 Token 化与暗黑模式 | v1.1 | 0/4 | Planned | - |
| 15. 菜单重组与设置导航 | v1.1 | 0/0 | Not started | - |
| 16. 账号管理 | v1.1 | 0/0 | Not started | - |
| 17. 数据管理增强 | v1.1 | 0/0 | Not started | - |
| 18. 全页面响应式适配 | v1.1 | 0/0 | Not started | - |
| 19. 融合能力增强 | v1.1 | 0/0 | Not started | - |
| 20. 对比重做与飞书完善 | v1.1 | 0/0 | Not started | - |
